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
Market-making book generator.

Generates a balanced PRS trading book with equal payer and receiver
positions across multiple gauges, tenors, and trigger levels.
Trades are priced near fair value with small MTM (0.05-0.15% of notional).

Sub-modules:
- book_common: Constants, leg PV computation, CDM record builder, counterparty loader
- book_thames: Thames Central 50-trade portfolio specs and generator
"""

import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import database

# Re-export shared constants and helpers for backward compatibility
from .book_common import (  # noqa: F401
    _REIT_PARTY_ID,
    DEFAULT_YIELD_CURVE,
    NOTIONALS,
    RECOVERY,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
    TENORS,
    TRIGGER_RATE_KEY,
    TRIGGERS,
    _build_cdm_record,
    _compute_leg_pvs,
    _load_counterparties,
    _price_and_save_trade,
)

# Re-export Thames Central book
from .book_thames import (  # noqa: F401
    _AREA_TO_GAUGE_NAME,
    _THAMES_TRADE_SPECS,
    THAMES_CENTRAL_AREAS,
    generate_thames_central_book,
)

logger = logging.getLogger(__name__)


def generate_market_making_book(
    output_dir: Path,
    num_gauges: int = 12,
    catchment_id: str = 'thames',
    seed: Optional[int] = 42,
) -> List[Dict]:
    """
    Generate a balanced market-making book of PRS trades.

    Creates paired payer/receiver trades across selected gauges
    with small MTM near fair value.

    Args:
        output_dir: Directory to write trade JSON files
        num_gauges: Number of gauges to include (trades = num_gauges * 2)
        catchment_id: Catchment identifier (gauge hazard curves and
            counterparties are loaded for it through the ``database`` seam)
        seed: Random seed for reproducibility (None for random)

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

    # Synthetic gauges (SYNTH-*) are interpolation anchors, not real
    # market-quoted instruments — never trade against them.
    curves = {gid: c for gid, c in curves.items() if not gid.startswith('SYNTH-')}
    if not curves:
        raise ValueError('No real (non-SYNTH) hazard curves found for catchment')

    # Load counterparties — the shared helper excludes the REIT (reserved
    # for property PRS) and falls back to a synthetic pool when none exist.
    counterparties = _load_counterparties(catchment_id)

    # Select gauges: spread across risk spectrum
    gauge_list = sorted(
        curves.items(),
        key=lambda x: x[1].get('annual_hazard_rate_warning', 0)
    )

    # Pick evenly spaced gauges
    step = max(1, len(gauge_list) // num_gauges)
    selected = gauge_list[::step][:num_gauges]

    output_dir.mkdir(parents=True, exist_ok=True)
    trades = []
    ctpy_idx = 0
    trade_date = datetime.now() - timedelta(days=random.randint(5, 30))

    for i, (gauge_id, gauge_data) in enumerate(selected):
        gauge_name = gauge_data.get('gauge_name', gauge_id)

        # Alternate tenor and trigger for variety
        tenor = TENORS[i % len(TENORS)]
        trigger = TRIGGERS[i % len(TRIGGERS)]
        notional = NOTIONALS[i % len(NOTIONALS)]

        rate_key = TRIGGER_RATE_KEY[trigger]
        hazard_rate = gauge_data.get(rate_key, 0.025)

        # Create paired trades: payer + receiver
        for is_payer in [True, False]:
            record, ctpy_idx = _price_and_save_trade(
                gauge_id=gauge_id,
                gauge_name=gauge_name,
                catchment_id=catchment_id,
                is_payer=is_payer,
                tenor=tenor,
                notional=notional,
                trigger=trigger,
                hazard_rate=hazard_rate,
                counterparties=counterparties,
                ctpy_idx=ctpy_idx,
                base_date=trade_date,
                output_dir=output_dir,
            )
            trades.append(record)

    return trades


def generate_trade_pdfs(trades: List[Dict], output_dir: Path) -> List[Path]:
    """Generate PDF confirmations for all trades."""
    from routes.prs import _generate_trade_pdf

    pdfs = []
    for record in trades:
        try:
            pdf_path = _generate_trade_pdf(record, [], output_dir)
            pdfs.append(pdf_path)
        except Exception as e:
            swap_id = record.get('PhysicalSwap', {}).get(
                'Header', {}).get('SwapID', '?')
            logger.warning('PDF generation failed for %s: %s', swap_id, e)

    return pdfs


def print_book_summary(trades: List[Dict], currency: Optional[str] = None) -> None:
    """Print a summary of the generated book.

    ``currency`` defaults to the active catchment's ``CURRENCY`` if not
    passed, so summary labels reflect the right ISO code (e.g. USD) without
    callers needing to know.
    """
    if currency is None:
        try:
            from config import config as _cfg
            currency = _cfg.CURRENCY
        except Exception:
            currency = "GBP"

    payer_count = 0
    receiver_count = 0
    payer_notional = 0.0
    receiver_notional = 0.0
    total_npv = 0.0

    for t in trades:
        ps = t['PhysicalSwap']
        is_payer = ps['LegData']['Payer']
        notional = ps['LegData']['Notional']
        npv = ps['Pricing']['NPV']

        if is_payer:
            payer_count += 1
            payer_notional += notional
        else:
            receiver_count += 1
            receiver_notional += notional

        total_npv += npv

    print(f'\n{"=" * 60}')
    print(f'  Market-Making Book Summary')
    print(f'{"=" * 60}')
    print(f'  Total trades:     {len(trades)}')
    print(f'  Payer (short):    {payer_count} trades, '
          f'{currency} {payer_notional:,.0f} notional')
    print(f'  Receiver (long):  {receiver_count} trades, '
          f'{currency} {receiver_notional:,.0f} notional')
    print(f'  Net notional:     {currency} {payer_notional - receiver_notional:,.0f}')
    print(f'  Total NPV:        {currency} {total_npv:,.0f}')
    print(f'{"=" * 60}\n')
