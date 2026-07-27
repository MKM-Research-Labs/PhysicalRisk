# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""PropertyHazardCurveGenerator — hazard curves, PRS pricing and basis."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

import database
from config import config
from config.frequency import load_frequency_config
from models.frequency import shared_draws
from models.hazard.terrain_grid import compute_terrain_grid
from port.utils.asset_config import RESIDENTIAL_CONFIG, AssetTypeConfig
from port.utils.generator_base import GeneratorInitMixin

from ..constants import MIN_PRS_SPREAD_BPS, TENORS
from ..encoder import json_default
from ..loader import LoaderMixin
from ..pricing import PricingMixin

logger = logging.getLogger(__name__)

from ._decomposition import _DecompositionMixin


class PropertyHazardCurveGenerator(
    LoaderMixin, PricingMixin, GeneratorInitMixin, _DecompositionMixin
):
    """
    Property-level hazard curve, PRS pricing, and basis calculator.

    Reads the asset ts output, counts severe flood events, computes
    spread as event_count / num_scenarios, and calculates basis
    against the synthetic gauge.

    Asset-type-specific knobs (input ts dir, output JSON filename, id
    prefix) come from ``ASSET_CONFIG``. Subclass and override that single
    attribute for other asset classes (e.g. commercial).
    """

    ASSET_CONFIG: AssetTypeConfig = RESIDENTIAL_CONFIG

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
        mode: str = "normal",
    ):
        self._init_generator(output_dir, mode, verbose)

    # Keep as static method on class for backward compatibility with tests
    _json_default = staticmethod(json_default)

    def generate(self) -> Dict:
        """
        Generate property-level hazard curves, PRS pricing, and basis.

        Returns:
            Dictionary with generation metadata and summary statistics.
        """
        cfg = self.ASSET_CONFIG
        mode_label = f" [{self.mode}]" if self.mode != "normal" else ""
        self.log(f"{cfg.label} Hazard Curve Generator{mode_label}")
        self.log(f"Catchment: {config.CATCHMENT}")

        catchment = database.active_catchment()
        if not cfg.timeseries_exists(catchment, self.mode):
            raise FileNotFoundError(
                f"{cfg.label} timeseries collection not generated "
                f"(mode '{self.mode}')\n"
                f"Run: python app.py port --{cfg.ts_dirs[self.mode]} first"
            )

        asset_ids = sorted(cfg.iter_timeseries_ids(catchment, self.mode))
        self.log(f"Found {len(asset_ids)} {cfg.label.lower()} timeseries records")

        gauge_hazard, num_storms = self._load_gauge_hazard_curves()
        self.log(f"Loaded hazard curves for {len(gauge_hazard)} gauges ({num_storms} storms)")

        # Event frame for the frequency layer (MKM-EF-001). Derived from the
        # storm sequences alone, so the property leg can regroup its own
        # per-asset flood records onto hours-clause events without needing
        # anyone's gauge levels. A catchment with no sequences on disk prices
        # on the pre-frequency metric rather than failing.
        frame, lambda_per_year = self._load_event_frame(catchment)
        # Loss-weighted view (MKM-EF-001 Stage 6c, additive). Config loaded and
        # draws taken once for the whole book, so every asset's loss run is
        # scored against the same simulated storms.
        freq_config = None
        loss_draws = None
        value_lookup = None
        if frame is not None:
            self.log(
                f"Event frame: {frame.n_storms} storms -> {frame.n_events} events, "
                f"coverage {frame.coverage:.3f}, lambda {lambda_per_year}/yr"
            )
            freq_config = load_frequency_config(catchment or None)
            loss_draws = shared_draws(frame, lambda_per_year, freq_config.simulation)
            value_lookup = self._load_asset_values(catchment)

        price_prs_func = self._get_prs_pricer()

        results = {}
        stats = {
            'total_properties': len(asset_ids),
            'properties_processed': 0,
            'properties_skipped': 0,
            'total_flood_events': 0,
            'avg_basis_bps': 0.0,
            'avg_transmission_rate': 0.0,
            'num_storms': num_storms,
        }

        basis_values = []
        transmission_rates = []
        spread_values = []

        for i, asset_id in enumerate(asset_ids):
            try:
                pdata = cfg.get_timeseries(catchment, asset_id, self.mode)
            except (OSError, ValueError) as exc:
                # A per-asset record vanished or is unreadable mid-build — skip it
                # rather than aborting the whole hazard-curve generation.
                self.log(f"Skipping {asset_id}: {exc}")
                pdata = None
            result = self._process_property(
                pdata, gauge_hazard, price_prs_func, num_storms,
                frame=frame, lambda_per_year=lambda_per_year,
                freq_config=freq_config, catchment=catchment,
                loss_draws=loss_draws, value_lookup=value_lookup)
            if result:
                results[result['property_id']] = result
                stats['properties_processed'] += 1
                stats['total_flood_events'] += result['flood_count']

                spread = result.get('term_structure', {}).get(
                    'severe', {}).get('prs_spread_bps', [0])[0]
                spread_values.append(spread)

                if result.get('summary', {}).get('avg_basis_bps') is not None:
                    basis_values.append(result['summary']['avg_basis_bps'])
                if result.get('summary', {}).get('flood_transmission_rate') is not None:
                    transmission_rates.append(result['summary']['flood_transmission_rate'])
            else:
                stats['properties_skipped'] += 1

            if (i + 1) % 50 == 0:
                self.log(f"  Processed {i + 1}/{len(asset_ids)} properties")

        stats['avg_basis_bps'] = round(np.mean(basis_values), 2) if basis_values else 0.0
        stats['avg_transmission_rate'] = round(np.mean(transmission_rates), 4) if transmission_rates else 0.0
        stats['avg_spread_bps'] = round(np.mean(spread_values), 2) if spread_values else 0.0

        output_data = {
            'metadata': {
                'catchment_id': config.CATCHMENT,
                'generated_at': datetime.now().isoformat(),
                'num_properties': len(results),
                'num_storms': num_storms,
                'tenors': TENORS,
                'terrain_grid': compute_terrain_grid(),
            },
            'summary': stats,
            'property_hazard_curves': results,
        }

        cfg.save_hazard_curves(database.active_catchment(), output_data, self.mode)

        self.log(f"Output: {cfg.hc_files[self.mode]}")
        avg_spread = stats['avg_spread_bps']
        n_flooded = len([s for s in spread_values if s > 0])
        self.log(f"  {stats['properties_processed']} properties  |  "
                 f"{n_flooded} with floods  |  {stats['properties_processed'] - n_flooded} zero")
        self.log(f"  Avg basis: {stats['avg_basis_bps']:.1f} bps")
        self.log(f"  Avg transmission rate: {stats['avg_transmission_rate']:.1%}")

        return stats
