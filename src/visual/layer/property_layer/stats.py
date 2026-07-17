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

"""Property layer statistics computation."""

from typing import Any, Dict, List

from ...utils import DataExtractor


def get_property_statistics(properties: List[Dict[str, Any]], loaded_data) -> Dict[str, Any]:
    """
    Calculate statistics for the properties.

    Args:
        properties: List of property data
        loaded_data: Full loaded data

    Returns:
        Dictionary with property statistics
    """
    if not properties:
        return {}

    risk_counts = {}
    mortgage_count = 0

    for prop in properties:
        try:
            property_info = DataExtractor.extract_property_info(prop)
            if property_info:
                property_id = property_info['property_id']

                flood_info = loaded_data.property_flood_info.get(property_id, {}) if loaded_data.property_flood_info else {}
                risk_level = flood_info.get('risk_level', property_info.get('flood_risk', 'Unknown'))
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

                if property_id in (loaded_data.rloan_lookup or {}):
                    mortgage_count += 1
        except Exception:
            continue

    return {
        'total_properties': len(properties),
        'mortgaged_properties': mortgage_count,
        'mortgage_percentage': (mortgage_count / len(properties)) * 100,
        'risk_distribution': risk_counts
    }
