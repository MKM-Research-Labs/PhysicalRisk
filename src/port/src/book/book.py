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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Re-export shared constants and helpers for backward compatibility
from .book_common import (  # noqa: F401
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
    THAMES_CENTRAL_AREAS,
    _AREA_TO_GAUGE_NAME,
    _THAMES_TRADE_SPECS,
    generate_thames_central_book,
)

logger = logging.getLogger(__name__)


def generate_market_making_book(
    gaugehc_path: Path,
    counterparty_path: Path,
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
        gaugehc_path: Path to gaugehc.json
        counterparty_path: Path to counterparty.json
        output_dir: Directory to write trade JSON files
        num_gauges: Number of gauges to include (trades = num_gauges * 2)
        catchment_id: Catchment identifier
        seed: Random seed for reproducibility (None for random)

    Returns:
        List of generated CDM records
    """
    if seed is not None:
        random.seed(seed)

    # Load gauge hazard curves
    with open(gaugehc_path) as f:
        gaugehc_data = json.load(f)

    curves = gaugehc_data.get('hazard_curves', {})
    if not curves:
        raise ValueError('No hazard curves found in gaugehc.json')

    # Load counterparties
    counterparties = []
    if counterparty_path.exists():
        with open(counterparty_path) as f:
            ctpy_data = json.load(f)
        for c in ctpy_data.get('counterparties', []):
            cs = c.get('CounterpartySet', {})
            party = cs.get('Party', {})
            platform = cs.get('_platform', {})
            counterparties.append({
                'id': party.get('PartyID', ''),
                'name': f"{platform.get('ShortName', party.get('PartyName', ''))} ({platform.get('CreditRating', 'NR')})",
            })

    if not counterparties:
        counterparties = [{'id': f'CTPY-{i:03d}', 'name': f'Counterparty {i}'}
                          for i in range(1, 22)]

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
    passed, so summary labels reflect the right ISO code (GBP for
    thames, USD for halong, etc.) without callers needing to know.
    """
    if currency is None:
        try:
            from config import config as _cfg
            import importlib
            currency = getattr(
                importlib.import_module(f"catch.{_cfg.catchment_id}"),
                "CURRENCY", "GBP",
            )
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
