# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Property-Level Hazard Curve Generator with PRS Pricing and Basis Calculation.

For each property in the propertyts output:
1. Extracts flood depths from flood_events
2. Fits GEV distribution (requires >= 3 events)
3. Computes exceedance probabilities at depth thresholds (0m, 0.5m, 1.0m)
4. Computes term structure and PRS pricing via QuantLib CDS
5. Calculates basis vs nearest gauge PRS prices

Usage:
    from port.src.property.hc import PropertyHazardCurveGenerator
    generator = PropertyHazardCurveGenerator(output_dir)
    result = generator.generate()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

from config import config
from models.hazard.gev import GEVFitter
from port.utils.generator_base import GeneratorInitMixin

from .constants import DEPTH_THRESHOLDS, MIN_PRS_SPREAD_BPS, TENORS
from .encoder import json_default
from .loader import LoaderMixin
from .pricing import PricingMixin

logger = logging.getLogger(__name__)


class PropertyHazardCurveGenerator(LoaderMixin, PricingMixin, GeneratorInitMixin):
    """
    Property-level hazard curve, PRS pricing, and basis calculator.

    Reads propertyts output, fits GEV per property, prices PRS,
    and computes basis against nearest gauge PRS prices.
    """

    # Map mode -> (input dir, output filename)
    _MODE_IO = {
        "normal": ("propertyts", "propertyhc.json"),
        "shd": ("propertytsd", "propertyshd.json"),
        "she": ("propertytse", "propertyshe.json"),
    }

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
        mode: str = "normal",
    ):
        self._init_generator(output_dir, mode, verbose)
        self.gev_fitter = GEVFitter()

    # Keep as static method on class for backward compatibility with tests
    _json_default = staticmethod(json_default)

    def generate(self) -> Dict:
        """
        Generate property-level hazard curves, PRS pricing, and basis.

        Returns:
            Dictionary with generation metadata and summary statistics.
        """
        pts_subdir, output_filename = self._MODE_IO[self.mode]
        mode_label = f" [{self.mode}]" if self.mode != "normal" else ""
        self.log(f"Property Hazard Curve Generator{mode_label}")
        self.log(f"Catchment: {config.CATCHMENT}")

        pts_dir = self.output_dir / pts_subdir
        if not pts_dir.exists():
            raise FileNotFoundError(
                f"Property timeseries directory not found: {pts_dir}\n"
                f"Run: python app.py port --{pts_subdir} first"
            )

        property_files = sorted(pts_dir.glob('PROP-*.json'))
        self.log(f"Found {len(property_files)} property timeseries files")

        gauge_hazard, num_storms = self._load_gauge_hazard_curves()
        self.log(f"Loaded hazard curves for {len(gauge_hazard)} gauges ({num_storms} storms)")

        price_prs_func = self._get_prs_pricer()

        results = {}
        stats = {
            'total_properties': len(property_files),
            'properties_with_gev': 0,
            'properties_with_floor': 0,
            'properties_skipped': 0,
            'total_flood_events': 0,
            'avg_basis_bps': 0.0,
            'avg_transmission_rate': 0.0,
            'min_spread_bps': MIN_PRS_SPREAD_BPS,
        }

        basis_values = []
        transmission_rates = []

        for i, pf in enumerate(property_files):
            result = self._process_property(pf, gauge_hazard, price_prs_func, num_storms)
            if result:
                results[result['property_id']] = result
                if result.get('has_gev'):
                    stats['properties_with_gev'] += 1
                else:
                    stats['properties_with_floor'] += 1
                stats['total_flood_events'] += result['flood_count']

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

        output_path = self.output_dir / output_filename
        output_data = {
            'metadata': {
                'catchment_id': config.CATCHMENT,
                'generated_at': datetime.now().isoformat(),
                'num_properties': len(results),
                'depth_thresholds': DEPTH_THRESHOLDS,
                'tenors': TENORS,
            },
            'summary': stats,
            'property_hazard_curves': results,
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=json_default)

        self.log(f"Output: {output_path.name}")
        self.log(f"  Properties with GEV: {stats['properties_with_gev']}/{len(property_files)}")
        self.log(f"  Properties with floor ({MIN_PRS_SPREAD_BPS}bp): {stats['properties_with_floor']}/{len(property_files)}")
        self.log(f"  Avg basis: {stats['avg_basis_bps']:.1f} bps")
        self.log(f"  Avg transmission rate: {stats['avg_transmission_rate']:.1%}")

        return stats

    def attach_spread_decomposition(self) -> int:
        """
        Post-processing: attach spread decompositions to propertyhc.json.

        Loads propertyhc.json, propertyshd.json, and propertyshe.json,
        then computes the data-driven spread decomposition for each property.

        Returns:
            Number of properties with decomposition attached.
        """
        hc_path = self.output_dir / 'propertyhc.json'
        shd_path = self.output_dir / 'propertyshd.json'
        she_path = self.output_dir / 'propertyshe.json'

        if not hc_path.exists():
            self.log("propertyhc.json not found — skipping decomposition")
            return 0

        with open(hc_path, 'r') as f:
            hc_data = json.load(f)

        shd_curves = {}
        if shd_path.exists():
            with open(shd_path, 'r') as f:
                shd_curves = json.load(f).get('property_hazard_curves', {})

        she_curves = {}
        if she_path.exists():
            with open(she_path, 'r') as f:
                she_curves = json.load(f).get('property_hazard_curves', {})

        curves = hc_data.get('property_hazard_curves', {})
        count = 0

        for prop_id, pc in curves.items():
            nearest_gauges = pc.get('nearest_gauges', [])
            synth_gauge = next(
                (ng for ng in nearest_gauges
                 if ng.get('gauge_id', '').startswith('SYNTH-')),
                None
            )

            shd_pc = shd_curves.get(prop_id, {})
            she_pc = she_curves.get(prop_id, {})

            prop_spread = self._get_5yr_spread(pc, 'severe')
            shd_spread = self._get_5yr_spread(shd_pc, 'severe')
            she_spread = self._get_5yr_spread(she_pc, 'severe')

            # Gauge spread baseline: use the synthetic gauge's severe spread
            if synth_gauge:
                synth_basis = synth_gauge.get('basis_bps', {}).get(
                    'severe', {}).get('values', [])
                prop_5yr = pc.get('term_structure', {}).get(
                    'severe', {}).get('prs_spread_bps', [0] * 5)
                p5 = prop_5yr[4] if len(prop_5yr) > 4 else 0.0
                sb = synth_basis[4] if len(synth_basis) > 4 else 0.0
                gauge_spread = p5 + sb
            else:
                gauge_spreads = pc.get('idw_gauge_spreads', {}).get('severe', [])
                gauge_spread = gauge_spreads[4] if len(gauge_spreads) > 4 else 0.0

            pc['spread_decomposition'] = {
                'gauge_spread_bps': round(gauge_spread, 2),
                'property_spread_bps': round(prop_spread, 2),
                'shd_spread_bps': round(shd_spread, 2),
                'she_spread_bps': round(she_spread, 2),
                'distance_first': {
                    'distance_effect_bps': round(she_spread - gauge_spread, 2),
                    'elevation_effect_bps': round(prop_spread - she_spread, 2),
                },
                'elevation_first': {
                    'elevation_effect_bps': round(shd_spread - gauge_spread, 2),
                    'distance_effect_bps': round(prop_spread - shd_spread, 2),
                },
            }
            count += 1

        with open(hc_path, 'w') as f:
            json.dump(hc_data, f, indent=2, default=json_default)

        self.log(f"Spread decomposition attached to {count} properties")
        return count

    @staticmethod
    def _get_5yr_spread(pc: Dict, threshold: str = 'any_flood') -> float:
        """Extract 5yr PRS spread for a given threshold from a hazard curve dict."""
        ts = pc.get('term_structure', {})
        spreads = ts.get(threshold, {}).get('prs_spread_bps', [])
        return spreads[4] if len(spreads) > 4 else 0.0
