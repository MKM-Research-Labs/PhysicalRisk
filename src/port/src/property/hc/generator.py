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

from .constants import DEPTH_THRESHOLDS, MIN_PRS_SPREAD_BPS, TENORS
from .encoder import json_default
from .loader import LoaderMixin
from .pricing import PricingMixin

logger = logging.getLogger(__name__)


class PropertyHazardCurveGenerator(LoaderMixin, PricingMixin):
    """
    Property-level hazard curve, PRS pricing, and basis calculator.

    Reads propertyts output, fits GEV per property, prices PRS,
    and computes basis against nearest gauge PRS prices.
    """

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True
    ):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.gev_fitter = GEVFitter()
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

    # Keep as static method on class for backward compatibility with tests
    _json_default = staticmethod(json_default)

    def log(self, message: str):
        logger.info(message)

    def generate(self) -> Dict:
        """
        Generate property-level hazard curves, PRS pricing, and basis.

        Returns:
            Dictionary with generation metadata and summary statistics.
        """
        self.log("Property Hazard Curve Generator")
        self.log(f"Catchment: {config.CATCHMENT}")

        pts_dir = self.output_dir / 'propertyts'
        if not pts_dir.exists():
            raise FileNotFoundError(
                f"Property timeseries directory not found: {pts_dir}\n"
                "Run: python app.py port --propertyts first"
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

        output_path = self.output_dir / 'propertyhc.json'
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
