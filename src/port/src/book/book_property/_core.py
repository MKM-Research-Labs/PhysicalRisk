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

from config.port import (
    PROPERTY_BOOK_NOTIONAL_MAX,
    PROPERTY_BOOK_NOTIONAL_MIN,
    PROPERTY_BOOK_NOTIONAL_STEP,
    PROPERTY_BOOK_NUM_TRADES,
    PROPERTY_BOOK_TENOR_WEIGHTS,
    PROPERTY_BOOK_TENORS,
)

from ..book_common import _price_and_save_trade, _load_counterparties  # noqa: F401
from ._select import (
    _select_properties,
    _match_tenor_idx,
    _lookup_property_metadata,
)

logger = logging.getLogger(__name__)


def generate_property_book(
    propertyhc_path: Path,
    property_path: Path,
    counterparty_path: Path,
    output_dir: Path,
    catchment_id: str = 'thames',
    seed: Optional[int] = 43,
    propertybri_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Generate a property PRS client book for the Trading Desk Client tab.

    Creates ~15 property-level trades across the flood-risk spectrum using
    fair spreads from propertyhc.json and property metadata from property.json.

    Two PRS flavours are booked per eligible property when a BRI-adjusted
    curve is available:

    * ``pure`` — priced on the surveyed-floor spread (propertyhc.json); the
      instrument ignores building resilience.
    * ``resilient`` — priced on the BRI-adjusted floor spread
      (propertybri.json); raising the effective flood floor removes some
      severe floods, so the resilient spread is tighter. Each trade is tagged
      with ``PropertySet.PRSVariant`` so the blotter can separate the lines.

    Args:
        propertyhc_path: Path to propertyhc.json (pure / surveyed-floor curve).
        property_path:   Path to property.json.
        counterparty_path: Path to counterparty.json.
        output_dir:      Directory to write PRS-P*.json trade files.
        catchment_id:    Catchment identifier.
        seed:            Random seed (default 43, distinct from gauge book's 42).
        propertybri_path: Optional path to propertybri.json (BRI-adjusted
            curve). When present and a property has a BRI curve, a second
            ``resilient`` trade is booked alongside the ``pure`` one.

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

    # Load BRI-adjusted curves (optional). Absent until the propertybri stage
    # has run — the book then simply omits the resilient leg.
    bri_curves = {}
    if propertybri_path is not None and Path(propertybri_path).exists():
        with open(propertybri_path) as f:
            bri_curves = json.load(f).get('property_hazard_curves', {})

    # Load property metadata
    with open(property_path) as f:
        prop_data = json.load(f)
    properties = prop_data.get('properties', [])

    # Property PRS: all trades are between the REIT (buyer) and the desk
    # (seller).  Use a fixed REIT counterparty rather than cycling dealers.
    counterparties = [{'id': 'CTPY-REIT-001', 'name': 'Thames Property REIT'}]

    # Select properties across risk spectrum
    selected = _select_properties(phc_curves, PROPERTY_BOOK_NUM_TRADES)
    if not selected:
        logger.warning('No eligible properties for book — skipping')
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    trades = []
    ctpy_idx = 0
    base_date = datetime.now() - timedelta(days=random.randint(5, 30))

    num_storms = phc_data.get('metadata', {}).get('num_storms', 20000)

    for item in selected:
        prop_id = item['property_id']
        curve = item['curve']

        # Pick tenor and find matching spread
        tenor = random.choices(
            PROPERTY_BOOK_TENORS, weights=PROPERTY_BOOK_TENOR_WEIGHTS, k=1)[0]
        tenors_available = item['tenors']
        spreads_available = item['spreads']

        # Match tenor to available tenors (find closest)
        idx = _match_tenor_idx(tenors_available, tenor)
        fair_spread = spreads_available[idx]

        if fair_spread <= 0:
            continue

        # Reference gauge from nearest_gauges — skip synthetic (SYNTH-*)
        # interpolation anchors; we only trade against real gauges.
        nearest = curve.get('nearest_gauges', [])
        ref_gauge = next(
            (g for g in nearest if not str(g.get('gauge_id', '')).startswith('SYNTH-')),
            None,
        )
        if ref_gauge is None:
            continue
        gauge_id = ref_gauge.get('gauge_id', '')
        gauge_name = ref_gauge.get('gauge_name', gauge_id)

        # Notional — fixed per property so the pure and resilient lines are
        # directly comparable (the spread difference is the resilience credit).
        notional = random.randrange(
            PROPERTY_BOOK_NOTIONAL_MIN, PROPERTY_BOOK_NOTIONAL_MAX + 1,
            PROPERTY_BOOK_NOTIONAL_STEP)

        # PropertyPRS: REIT client is always the payer (buying protection),
        # Trader (desk) is always the receiver (selling protection).
        is_payer = True

        # Use flood_count to derive a hazard rate for leg PV computation
        flood_count = item['flood_count']
        hazard_rate = flood_count / num_storms if num_storms > 0 else 0.02

        # Build base PropertySet (shared by both flavours)
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

        # ---- Pure flavour: surveyed-floor spread (ignores BRI) ----
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
            property_set={**prop_meta, 'PRSVariant': 'pure'},
            fair_spread_override=fair_spread,
        )
        trades.append(record)

        # ---- Resilient flavour: BRI-adjusted floor spread ----
        # Only when a BRI-adjusted curve exists for this property. Raising the
        # effective floor can only remove severe floods, so the resilient
        # spread is <= the pure spread.
        bri_curve = bri_curves.get(prop_id)
        if bri_curve:
            bri_ts = bri_curve.get('term_structure', {}).get('severe', {})
            bri_spreads = bri_ts.get('prs_spread_bps', [])
            bri_tenors = bri_curve.get('term_structure', {}).get('tenors', [])
            if bri_spreads and bri_tenors:
                bri_idx = _match_tenor_idx(bri_tenors, tenor)
                bri_fair_spread = bri_spreads[bri_idx]
                bri_flood_count = bri_curve.get('flood_count', 0)
                bri_hazard_rate = (bri_flood_count / num_storms
                                   if num_storms > 0 else 0.02)
                record, ctpy_idx = _price_and_save_trade(
                    gauge_id=gauge_id,
                    gauge_name=gauge_name,
                    catchment_id=catchment_id,
                    is_payer=is_payer,
                    tenor=tenor,
                    notional=notional,
                    trigger='severe',
                    hazard_rate=bri_hazard_rate,
                    counterparties=counterparties,
                    ctpy_idx=ctpy_idx,
                    base_date=base_date,
                    output_dir=output_dir,
                    property_set={**prop_meta, 'PRSVariant': 'resilient'},
                    fair_spread_override=bri_fair_spread,
                )
                trades.append(record)

    logger.info('Generated %d property PRS trades', len(trades))
    return trades
