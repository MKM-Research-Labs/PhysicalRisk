# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Per-type statistics for the commercial layer."""

from typing import Any, Dict, List


def get_commercial_statistics(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute counts and total valuation per CommercialType."""
    type_counts: Dict[str, int] = {}
    type_value: Dict[str, float] = {}
    for a in assets:
        ca = a.get("CommercialAsset", {})
        ctype = ca.get("CommercialAttributes", {}).get("CommercialType", "Other")
        val = ca.get("Valuation", {}).get("PropertyValue", 0) or 0
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
        type_value[ctype] = type_value.get(ctype, 0.0) + float(val)
    return {
        "total_assets": len(assets),
        "by_type_count": type_counts,
        "by_type_value_gbp": {k: round(v, 0) for k, v in type_value.items()},
        "total_value_gbp": round(sum(type_value.values()), 0),
    }
