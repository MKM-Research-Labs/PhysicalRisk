# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""PropertyHazardCurveGenerator — hazard curves, PRS pricing and basis."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

from config import config
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

        pts_dir = cfg.ts_dir(self.output_dir, self.mode)
        if not pts_dir.exists():
            raise FileNotFoundError(
                f"{cfg.label} timeseries directory not found: {pts_dir}\n"
                f"Run: python app.py port --{cfg.ts_dirs[self.mode]} first"
            )

        property_files = sorted(pts_dir.glob(cfg.id_glob))
        self.log(f"Found {len(property_files)} property timeseries files")

        gauge_hazard, num_storms = self._load_gauge_hazard_curves()
        self.log(f"Loaded hazard curves for {len(gauge_hazard)} gauges ({num_storms} storms)")

        price_prs_func = self._get_prs_pricer()

        results = {}
        stats = {
            'total_properties': len(property_files),
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

        for i, pf in enumerate(property_files):
            result = self._process_property(pf, gauge_hazard, price_prs_func, num_storms)
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
                self.log(f"  Processed {i + 1}/{len(property_files)} properties")

        stats['avg_basis_bps'] = round(np.mean(basis_values), 2) if basis_values else 0.0
        stats['avg_transmission_rate'] = round(np.mean(transmission_rates), 4) if transmission_rates else 0.0
        stats['avg_spread_bps'] = round(np.mean(spread_values), 2) if spread_values else 0.0

        output_path = cfg.hc_file(self.output_dir, self.mode)
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

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=json_default)

        self.log(f"Output: {output_path.name}")
        avg_spread = stats['avg_spread_bps']
        n_flooded = len([s for s in spread_values if s > 0])
        self.log(f"  {stats['properties_processed']} properties  |  "
                 f"{n_flooded} with floods  |  {stats['properties_processed'] - n_flooded} zero")
        self.log(f"  Avg basis: {stats['avg_basis_bps']:.1f} bps")
        self.log(f"  Avg transmission rate: {stats['avg_transmission_rate']:.1%}")

        return stats
