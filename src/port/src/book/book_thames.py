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

"""
Book generator — Thames Central trading book.

50-trade portfolio across 10 inner London gauges with:
- Core short position on Westminster hedged by longs on neighbours
- Calendar spreads (long 5Y / short 1-2Y on same gauge)
- Gauge spreads (long one gauge / short adjacent)
- Heavy sub-3Y tenor weighting (1Y, 2Y, 3Y, 5Y)
"""

import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import database

from .book_common import (
    DEFAULT_YIELD_CURVE,
    RECOVERY,
    _load_counterparties,
    _price_and_save_trade,
)

logger = logging.getLogger(__name__)


# 10 Thames Central gauges used by the trade specs.
# Each entry maps the trade-spec label → gauge name substring for matching.
# These correspond to gauge points 10, 11, 13, 14, 15, 16, 20, 7, 12, 8
# i.e. the inner London reach from Chelsea Bridge to London Bridge.
THAMES_CENTRAL_AREAS = [
    'Chelsea', 'Kensington', 'Westminster', 'Camden', 'Islington',
    'Hackney', 'Tower Hamlets', 'Southwark', 'Lambeth', 'Wandsworth',
]

# Map trade-spec area labels to gauge name substrings for matching in gaugehc.json
_AREA_TO_GAUGE_NAME = {
    'Chelsea': 'Chelsea Bridge',
    'Kensington': 'Vauxhall Bridge',
    'Westminster': 'Westminster Bridge',
    'Camden': 'Hungerford Bridge',
    'Islington': 'Waterloo Bridge',
    'Hackney': 'Blackfriars Bridge',
    'Tower Hamlets': 'London Bridge',
    'Southwark': 'Putney Bridge',
    'Lambeth': 'Lambeth Bridge',
    'Wandsworth': 'Wandsworth Bridge',
}

# Trade specs: gauge area name, tenor, notional, is_payer
# 50 trades across 10 gauges with tenors 1-5Y (heavier sub-3Y weighting)
_THAMES_TRADE_SPECS = [
    # ── Westminster Core Short: large net receiver book ──────────
    {'gauge': 'Westminster', 'tenor': 5, 'notional': 15_000_000, 'is_payer': False},
    {'gauge': 'Westminster', 'tenor': 5, 'notional': 12_000_000, 'is_payer': False},
    {'gauge': 'Westminster', 'tenor': 3, 'notional': 10_000_000, 'is_payer': False},
    {'gauge': 'Westminster', 'tenor': 3, 'notional': 12_000_000, 'is_payer': False},
    {'gauge': 'Westminster', 'tenor': 2, 'notional': 8_000_000, 'is_payer': False},
    {'gauge': 'Westminster', 'tenor': 1, 'notional': 5_000_000, 'is_payer': False},
    {'gauge': 'Westminster', 'tenor': 1, 'notional': 5_000_000, 'is_payer': True},
    # ── Calendar spreads: Pay long tenor / Rcv short tenor ──────
    # Lambeth 5Y/2Y
    {'gauge': 'Lambeth', 'tenor': 5, 'notional': 10_000_000, 'is_payer': True},
    {'gauge': 'Lambeth', 'tenor': 2, 'notional': 10_000_000, 'is_payer': False},
    # Lambeth 3Y/1Y
    {'gauge': 'Lambeth', 'tenor': 3, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Lambeth', 'tenor': 1, 'notional': 5_000_000, 'is_payer': False},
    # Southwark 5Y/2Y
    {'gauge': 'Southwark', 'tenor': 5, 'notional': 10_000_000, 'is_payer': True},
    {'gauge': 'Southwark', 'tenor': 2, 'notional': 8_000_000, 'is_payer': False},
    # Southwark 3Y/1Y
    {'gauge': 'Southwark', 'tenor': 3, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Southwark', 'tenor': 1, 'notional': 5_000_000, 'is_payer': False},
    # Kensington 5Y/2Y
    {'gauge': 'Kensington', 'tenor': 5, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Kensington', 'tenor': 2, 'notional': 8_000_000, 'is_payer': False},
    # Camden 3Y/1Y
    {'gauge': 'Camden', 'tenor': 3, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Camden', 'tenor': 1, 'notional': 8_000_000, 'is_payer': False},
    # Hackney 5Y/3Y
    {'gauge': 'Hackney', 'tenor': 5, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Hackney', 'tenor': 3, 'notional': 8_000_000, 'is_payer': False},
    # Tower Hamlets 5Y/2Y
    {'gauge': 'Tower Hamlets', 'tenor': 5, 'notional': 10_000_000, 'is_payer': True},
    {'gauge': 'Tower Hamlets', 'tenor': 2, 'notional': 10_000_000, 'is_payer': False},
    # ── Gauge spreads: long one gauge / short adjacent ──────────
    # Chelsea vs Wandsworth 5Y
    {'gauge': 'Chelsea', 'tenor': 5, 'notional': 10_000_000, 'is_payer': True},
    {'gauge': 'Wandsworth', 'tenor': 5, 'notional': 10_000_000, 'is_payer': False},
    # Tower Hamlets vs Southwark 3Y
    {'gauge': 'Tower Hamlets', 'tenor': 3, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Southwark', 'tenor': 3, 'notional': 8_000_000, 'is_payer': False},
    # Kensington vs Islington 2Y
    {'gauge': 'Kensington', 'tenor': 2, 'notional': 5_000_000, 'is_payer': True},
    {'gauge': 'Islington', 'tenor': 2, 'notional': 5_000_000, 'is_payer': False},
    # Camden vs Hackney 1Y
    {'gauge': 'Camden', 'tenor': 1, 'notional': 5_000_000, 'is_payer': True},
    {'gauge': 'Hackney', 'tenor': 1, 'notional': 5_000_000, 'is_payer': False},
    # Chelsea vs Westminster 3Y (adds to core short)
    {'gauge': 'Chelsea', 'tenor': 3, 'notional': 10_000_000, 'is_payer': True},
    {'gauge': 'Westminster', 'tenor': 3, 'notional': 10_000_000, 'is_payer': False},
    # Lambeth vs Wandsworth 2Y
    {'gauge': 'Lambeth', 'tenor': 2, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Wandsworth', 'tenor': 2, 'notional': 8_000_000, 'is_payer': False},
    # ── Hedges: long protection near core short ─────────────────
    {'gauge': 'Chelsea', 'tenor': 2, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Tower Hamlets', 'tenor': 5, 'notional': 12_000_000, 'is_payer': True},
    {'gauge': 'Lambeth', 'tenor': 5, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Islington', 'tenor': 2, 'notional': 5_000_000, 'is_payer': True},
    {'gauge': 'Hackney', 'tenor': 1, 'notional': 5_000_000, 'is_payer': True},
    {'gauge': 'Camden', 'tenor': 3, 'notional': 8_000_000, 'is_payer': True},
    # ── Outright positions ──────────────────────────────────────
    {'gauge': 'Wandsworth', 'tenor': 2, 'notional': 10_000_000, 'is_payer': True},
    {'gauge': 'Kensington', 'tenor': 1, 'notional': 5_000_000, 'is_payer': True},
    {'gauge': 'Southwark', 'tenor': 2, 'notional': 8_000_000, 'is_payer': True},
    {'gauge': 'Islington', 'tenor': 3, 'notional': 8_000_000, 'is_payer': False},
    {'gauge': 'Tower Hamlets', 'tenor': 1, 'notional': 5_000_000, 'is_payer': False},
    {'gauge': 'Camden', 'tenor': 2, 'notional': 5_000_000, 'is_payer': False},
    {'gauge': 'Wandsworth', 'tenor': 1, 'notional': 8_000_000, 'is_payer': False},
    {'gauge': 'Hackney', 'tenor': 2, 'notional': 5_000_000, 'is_payer': False},
    {'gauge': 'Chelsea', 'tenor': 1, 'notional': 5_000_000, 'is_payer': False},
]


def generate_thames_central_book(
    output_dir: Path,
    catchment_id: str = 'thames',
    seed: Optional[int] = 42,
) -> List[Dict]:
    """
    Generate a Thames Central trading book across inner London gauges.

    Creates a realistic 50-trade portfolio with:
    - Core short position on Westminster hedged by longs on neighbours
    - Calendar spreads (long 5Y / short 1-2Y on same gauge)
    - Gauge spreads (long one gauge / short adjacent)
    - Heavy sub-3Y tenor weighting (1Y, 2Y, 3Y, 5Y)

    Args:
        output_dir: Directory to write trade JSON files
        catchment_id: Catchment identifier (gauge hazard curves and
            counterparties are loaded for it through the ``database`` seam)
        seed: Random seed for reproducibility

    Returns:
        List of generated CDM records
    """
    if seed is not None:
        random.seed(seed)

    # Load gauge hazard curves through the database seam.
    gaugehc_data = database.get_gauge_hazard_curves(catchment_id)
    curves = (gaugehc_data or {}).get('hazard_curves', {})
    if not curves:
        raise ValueError('No hazard curves found for catchment')

    # Build area name → (gauge_id, curve_data) lookup by matching gauge names
    gauge_lookup = {}
    for gauge_id, curve_data in curves.items():
        gname = curve_data.get('gauge_name', '')
        for area in THAMES_CENTRAL_AREAS:
            target = _AREA_TO_GAUGE_NAME.get(area, area)
            if area not in gauge_lookup and target.lower() in gname.lower():
                gauge_lookup[area] = (gauge_id, curve_data)
                break

    for area in THAMES_CENTRAL_AREAS:
        if area not in gauge_lookup:
            logger.warning('Area %s not matched to any gauge in hazard curves', area)

    # Load counterparties
    counterparties = _load_counterparties(catchment_id)

    output_dir.mkdir(parents=True, exist_ok=True)
    trades = []
    ctpy_idx = 0
    base_date = datetime.now() - timedelta(days=random.randint(5, 30))

    for spec in _THAMES_TRADE_SPECS:
        area = spec['gauge']
        if area not in gauge_lookup:
            logger.warning('Skipping trade spec for %s — gauge not found', area)
            continue

        gauge_id, gauge_data = gauge_lookup[area]
        gauge_name = gauge_data.get('gauge_name', gauge_id)
        tenor = spec['tenor']
        notional = spec['notional']
        is_payer = spec['is_payer']

        hazard_rate = gauge_data.get('annual_hazard_rate_severe', 0.025)

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
        )
        trades.append(record)

    return trades
