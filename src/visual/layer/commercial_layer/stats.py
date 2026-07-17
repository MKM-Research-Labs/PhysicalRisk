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
