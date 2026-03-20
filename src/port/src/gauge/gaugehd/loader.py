# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Gauge portfolio loader."""

import json
from typing import Any, Dict, List

from config import config


def load_gauge_portfolio() -> List[Dict[str, Any]]:
    """Load the gauge portfolio from the catchment input directory."""
    portfolio_path = config.get_input_path("gauge.json")

    if not portfolio_path.exists():
        raise FileNotFoundError(f"Gauge portfolio not found: {portfolio_path}")

    with open(portfolio_path, 'r') as f:
        data = json.load(f)

    return data.get("flood_gauges", [])
