# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Data loading mixin for PropertyHazardCurveGenerator."""

import json


class LoaderMixin:
    """Mixin providing data-loading helpers."""

    def _load_gauge_hazard_curves(self) -> tuple:
        """Load gauge hazard curves and metadata from gaugehc.json."""
        hc_path = self.output_dir / 'gaugehc.json'
        if not hc_path.exists():
            self.log("  Warning: gaugehc.json not found, basis will be empty")
            return {}, 1000

        with open(hc_path, 'r') as f:
            data = json.load(f)

        num_storms = data.get('metadata', {}).get('num_storms', 1000)
        return data.get('hazard_curves', {}), num_storms

    def _get_prs_pricer(self):
        """Try to import QuantLib PRS pricer. Returns None if unavailable."""
        try:
            from models.prs.prshc import price_prs
            return price_prs
        except ImportError:
            self.log("  Warning: QuantLib not available, PRS pricing will use analytical model")
            return None
