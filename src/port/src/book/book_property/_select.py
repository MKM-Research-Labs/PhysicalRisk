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

"""Property selection, tenor matching and metadata lookup helpers."""

import random
from typing import Dict, List


def _select_properties(phc_curves: Dict, num: int) -> List[Dict]:
    """Select properties across the flood-risk spectrum.

    Picks roughly equal numbers from high, medium, and low flood-count
    buckets to give a representative client portfolio.
    """
    items = []
    for prop_id, curve in phc_curves.items():
        fc = curve.get('flood_count', 0)
        ts = curve.get('term_structure', {}).get('severe', {})
        spreads = ts.get('prs_spread_bps', [])
        tenors = curve.get('term_structure', {}).get('tenors', [])
        if not spreads or not tenors or fc == 0:
            continue
        items.append({
            'property_id': prop_id,
            'flood_count': fc,
            'spreads': spreads,
            'tenors': tenors,
            'curve': curve,
        })

    if not items:
        return []

    # Sort by flood count and split into thirds
    items.sort(key=lambda x: x['flood_count'], reverse=True)
    n = len(items)
    third = max(1, n // 3)

    high = items[:third]
    medium = items[third:2 * third]
    low = items[2 * third:]

    # Sample from each bucket
    per_bucket = max(1, num // 3)
    selected = []
    for bucket in [high, medium, low]:
        k = min(per_bucket, len(bucket))
        selected.extend(random.sample(bucket, k))

    # Top up if needed
    remaining = num - len(selected)
    pool = [x for x in items if x not in selected]
    if remaining > 0 and pool:
        selected.extend(random.sample(pool, min(remaining, len(pool))))

    return selected[:num]


def _match_tenor_idx(tenors_available: List[int], tenor: int) -> int:
    """Return the index of the tenor in the curve closest to ``tenor``."""
    if tenor in tenors_available:
        return tenors_available.index(tenor)
    return min(range(len(tenors_available)),
               key=lambda i: abs(tenors_available[i] - tenor))


def _lookup_property_metadata(property_json: List[Dict],
                              property_id: str) -> Dict:
    """Extract PropertySet metadata from property.json for a given property."""
    for p in property_json:
        hdr = p.get('PropertyHeader', {}).get('Header', {})
        if hdr.get('PropertyID') == property_id:
            loc = p.get('PropertyHeader', {}).get('Location', {})
            val = p.get('PropertyHeader', {}).get('Valuation', {})
            risk = p.get('PropertyHeader', {}).get('RiskAssessment', {})
            address_parts = [
                loc.get('BuildingNumber', ''),
                loc.get('StreetName', ''),
            ]
            address = ' '.join(part for part in address_parts if part).strip()
            return {
                'PropertyID': property_id,
                'EAFloodZone': risk.get('EAFloodZone', ''),
                'PropertyAddress': address,
                'Postcode': loc.get('Postcode', ''),
                'LocalAuthority': loc.get('LocalAuthority', ''),
                'PropertyValue': val.get('PropertyValue', 0),
                'Latitude': loc.get('LatitudeDegrees', 0),
                'Longitude': loc.get('LongitudeDegrees', 0),
            }
    return {'PropertyID': property_id}
