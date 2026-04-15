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

"""
Book generator — property PRS client book.

Generates ~15-20 property-level PRS trades from propertyhc.json so the
Client tab in the Trading Desk is populated on a fresh ``port --blotter`` run.

Properties are selected across the flood-risk spectrum (high / medium / low
flood_count) to give a representative client portfolio.  Pricing uses the
event-count fair spread from propertyhc.json term_structure rather than the
gauge-level analytical pricer.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .book_common import (
    DEFAULT_YIELD_CURVE,
    RECOVERY,
    _compute_leg_pvs,
    _load_counterparties,
    _price_and_save_trade,
)

logger = logging.getLogger(__name__)

# Tenor weights: heavier on 3Y and 5Y for client trades (longer-dated
# protection mirrors real mortgage-linked hedging demand).
_TENORS = [1, 2, 3, 5]
_TENOR_WEIGHTS = [0.10, 0.20, 0.35, 0.35]

# Notional range for property trades (smaller than gauge-level book)
_NOTIONAL_MIN = 2_000_000
_NOTIONAL_MAX = 8_000_000
_NOTIONAL_STEP = 1_000_000

# Target number of property trades
_NUM_TRADES = 15


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


def generate_property_book(
    propertyhc_path: Path,
    property_path: Path,
    counterparty_path: Path,
    output_dir: Path,
    catchment_id: str = 'thames',
    seed: Optional[int] = 43,
) -> List[Dict]:
    """
    Generate a property PRS client book for the Trading Desk Client tab.

    Creates ~15 property-level trades across the flood-risk spectrum using
    fair spreads from propertyhc.json and property metadata from property.json.

    Args:
        propertyhc_path: Path to propertyhc.json.
        property_path:   Path to property.json.
        counterparty_path: Path to counterparty.json.
        output_dir:      Directory to write PRS-P*.json trade files.
        catchment_id:    Catchment identifier.
        seed:            Random seed (default 43, distinct from gauge book's 42).

    Returns:
        List of generated CDM records.
    """
    if seed is not None:
        random.seed(seed)

    # Load propertyhc curves
    with open(propertyhc_path) as f:
        phc_data = json.load(f)
    phc_curves = phc_data.get('property_hazard_curves', {})
    if not phc_curves:
        logger.warning('No property hazard curves found — skipping property book')
        return []

    # Load property metadata
    with open(property_path) as f:
        prop_data = json.load(f)
    properties = prop_data.get('properties', [])

    # Property PRS: all trades are between the REIT (buyer) and the desk
    # (seller).  Use a fixed REIT counterparty rather than cycling dealers.
    counterparties = [{'id': 'CTPY-REIT-001', 'name': 'Thames Property REIT'}]

    # Select properties across risk spectrum
    selected = _select_properties(phc_curves, _NUM_TRADES)
    if not selected:
        logger.warning('No eligible properties for book — skipping')
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    trades = []
    ctpy_idx = 0
    base_date = datetime.now() - timedelta(days=random.randint(5, 30))

    for item in selected:
        prop_id = item['property_id']
        curve = item['curve']

        # Pick tenor and find matching spread
        tenor = random.choices(_TENORS, weights=_TENOR_WEIGHTS, k=1)[0]
        tenors_available = item['tenors']
        spreads_available = item['spreads']

        # Match tenor to available tenors (find closest)
        if tenor in tenors_available:
            idx = tenors_available.index(tenor)
        else:
            idx = min(range(len(tenors_available)),
                      key=lambda i: abs(tenors_available[i] - tenor))
        fair_spread = spreads_available[idx]

        if fair_spread <= 0:
            continue

        # Reference gauge from nearest_gauges
        nearest = curve.get('nearest_gauges', [])
        if nearest:
            ref_gauge = nearest[0]
            gauge_id = ref_gauge.get('gauge_id', '')
            gauge_name = ref_gauge.get('gauge_name', gauge_id)
        else:
            continue

        # Notional
        notional = random.randrange(_NOTIONAL_MIN, _NOTIONAL_MAX + 1,
                                    _NOTIONAL_STEP)

        # PropertyPRS: REIT client is always the payer (buying protection),
        # Trader (desk) is always the receiver (selling protection).
        is_payer = True

        # Use flood_count to derive a hazard rate for leg PV computation
        num_storms = phc_data.get('metadata', {}).get('num_storms', 20000)
        flood_count = item['flood_count']
        hazard_rate = flood_count / num_storms if num_storms > 0 else 0.02

        # Build PropertySet
        prop_meta = _lookup_property_metadata(properties, prop_id)
        # Use flood zone from propertyhc (more reliable than property.json)
        prop_meta['EAFloodZone'] = curve.get('flood_zone', prop_meta.get(
            'EAFloodZone', ''))
        # Add reference gauge info
        if nearest:
            prop_meta['ReferenceGauge'] = {
                'GaugeID': gauge_id,
                'Distance': round(ref_gauge.get('distance_km', 0), 3),
            }

        record, ctpy_idx = _price_and_save_trade(
            gauge_id=gauge_id,
            gauge_name=gauge_name,
            catchment_id=catchment_id,
            is_payer=is_payer,
            tenor=tenor,
            notional=notional,
            trigger='severe',
            hazard_rate=hazard_rate,
            counterparties=counterparties,
            ctpy_idx=ctpy_idx,
            base_date=base_date,
            output_dir=output_dir,
            property_set=prop_meta,
            fair_spread_override=fair_spread,
        )
        trades.append(record)

    logger.info('Generated %d property PRS trades', len(trades))
    return trades
