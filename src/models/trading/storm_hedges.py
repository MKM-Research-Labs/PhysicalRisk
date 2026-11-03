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
Storm payouts on the PRS book: the REIT's hedges and the desk's position.

A PRS pays its notional when its gauge reaches the trigger level (severe) in
the storm. Per storm this works out:

* REIT hedges (``PropertyPRS``, REIT = protection buyer): the REIT receives
  the notional and the desk pays it.
* Desk gauge trades (``PRS``): ``LegData.Payer`` is the desk's side. A payer
  bought protection and receives the notional; a receiver sold it and pays.
  Trades with ``Header.TradePurpose == 'REITLayoff'`` are the desk's lay-off
  of the REIT hedges; the rest are its gauge book.

Whether a gauge reached severe comes from its per-storm responses
(``gaugets/<gauge>.json`` → ``storm_responses``), so the payout follows the
contract trigger rather than whether the asset itself flooded.
"""

import logging
from typing import Dict, Iterable, List, Optional

import database
from database.backend import active_backend

logger = logging.getLogger(__name__)

_REIT_TRADE_TYPE = 'PropertyPRS'
_LAYOFF_PURPOSE = 'REITLayoff'  # port.src.book.book_property LAYOFF_PURPOSE

# (backend id, catchment, gauge_id) -> {storm_id: (peak_level_m, exceeded_severe)}.
# Gauge timeseries files are several MB each, so they are read once per gauge.
_response_cache: Dict[tuple, Dict[str, tuple]] = {}
# (backend id, catchment) -> {sequence_id: [storm_id, ...]}
_sequence_cache: Dict[tuple, Dict[str, List[str]]] = {}


def clear_cache() -> None:
    """Forget cached gauge responses and sequences (after regenerating them)."""
    _response_cache.clear()
    _sequence_cache.clear()


def storms_in(catchment: str, storm_or_sequence_id: str) -> List[str]:
    """The individual storm IDs behind an ID from the storm list.

    The storm list (and property flood events) use sequence IDs, while gauge
    responses are recorded per storm within a sequence. An ID that is not a
    known sequence is taken to be a single storm.
    """
    key = (id(active_backend()), catchment)
    if key not in _sequence_cache:
        data = database.get_storm_sequences(catchment) or {}
        _sequence_cache[key] = {
            s['sequence_id']: [st['storm_id'] for st in s.get('storms', []) if st.get('storm_id')]
            for s in data.get('sequences', []) if s.get('sequence_id')
        }
    return _sequence_cache[key].get(storm_or_sequence_id) or [storm_or_sequence_id]


def gauge_storm_responses(catchment: str, gauge_id: str) -> Dict[str, tuple]:
    """``{storm_id: (peak_level_m, exceeded_severe)}`` for one gauge."""
    key = (id(active_backend()), catchment, gauge_id)
    if key not in _response_cache:
        responses = {}
        data = database.get_gauge_timeseries(catchment, gauge_id) or {}
        for r in data.get('storm_responses', {}).get('responses', []):
            sid = r.get('storm_id')
            if sid:
                responses[sid] = (r.get('peak_level_m'), bool(r.get('exceeded_severe')))
        _response_cache[key] = responses
    return _response_cache[key]


def _trigger_state(catchment: str, gauge_id: str, storm_ids: List[str]) -> tuple:
    """(triggered, highest peak level) for a gauge across ``storm_ids``."""
    responses = gauge_storm_responses(catchment, gauge_id)
    triggered = False
    peak: Optional[float] = None
    for sid in storm_ids:
        level, exceeded = responses.get(sid, (None, False))
        triggered = triggered or exceeded
        if level is not None and (peak is None or level > peak):
            peak = level
    return triggered, peak


def load_trades(catchment: str) -> List[Dict]:
    """Every PRS trade in the book, flattened to what the payout needs."""
    trades = []
    for swap_id in database.iter_prs_trade_ids(catchment):
        try:
            raw = database.get_prs_trade(catchment, swap_id)
        except ValueError as exc:  # corrupt trade file: skip it, keep the rest
            logger.warning('Skipping unreadable PRS trade %s: %s', swap_id, exc)
            continue
        if not raw or 'PhysicalSwap' not in raw:
            continue
        ps = raw.get('PhysicalSwap', {})
        header = ps.get('Header', {})
        basket = ps.get('GaugeSet', {}).get('GaugeBasket') or [{}]
        prop = ps.get('PropertySet', {})
        trades.append({
            'swap_id': header.get('SwapID', swap_id),
            'trade_type': header.get('TradeType', 'PRS'),
            'purpose': header.get('TradePurpose', ''),
            'counterparty': header.get('CounterPartyName', ''),
            'payer': bool(ps.get('LegData', {}).get('Payer', False)),
            'notional': ps.get('LegData', {}).get('Notional', 0) or 0,
            'end_date': ps.get('ScheduleData', {}).get('EndDate', ''),
            'spread_bps': ps.get('Pricing', {}).get('SpreadBps', 0),
            'gauge_id': basket[0].get('GaugeID', ''),
            'gauge_name': basket[0].get('GaugeName', ''),
            'asset_id': prop.get('PropertyID', ''),
            'asset_class': prop.get('AssetClass') or (
                'commercial' if str(prop.get('PropertyID', '')).startswith('CPROP-')
                else 'residential'),
            'address': prop.get('PropertyAddress', ''),
            'asset_value': prop.get('PropertyValue', 0) or 0,
        })
    return trades


def storm_hedge_report(catchment: str, storm_ids: Iterable[str],
                       trades: Optional[List[Dict]] = None) -> Dict:
    """REIT hedge payouts and the desk's net position for storms from the
    storm list (sequence IDs are expanded to their storms; a trade pays at
    most once).

    Returns ``{'reit': {...}, 'desk': {...}}``:

    * ``reit.hedges`` — one row per REIT hedge with ``triggered`` and
      ``payout`` (cash to the REIT).
    * ``desk.trades`` — one row per desk gauge trade with ``role``
      (``layoff`` or ``book``), ``triggered`` and ``cash`` (to the desk).
    * ``desk.net`` — what the desk pays the REIT, plus what its gauge trades
      pay or cost it.
    """
    requested = list(storm_ids)
    storm_ids = [s for sid in requested for s in storms_in(catchment, sid)]
    if trades is None:
        trades = load_trades(catchment)

    hedges, desk_trades = [], []
    for t in trades:
        if not t['gauge_id']:
            continue
        triggered, peak = _trigger_state(catchment, t['gauge_id'], storm_ids)
        row = {**t, 'triggered': triggered, 'gauge_peak_m': peak}
        if t['trade_type'] == _REIT_TRADE_TYPE:
            row['payout'] = t['notional'] if triggered else 0
            hedges.append(row)
        else:
            sign = 1 if t['payer'] else -1
            row['role'] = 'layoff' if t['purpose'] == _LAYOFF_PURPOSE else 'book'
            row['cash'] = sign * t['notional'] if triggered else 0
            desk_trades.append(row)

    hedges.sort(key=lambda r: (-r['payout'], -r['notional']))
    desk_trades.sort(key=lambda r: (r['role'] != 'layoff', -abs(r['cash']), r['gauge_name']))

    reit_payout = sum(r['payout'] for r in hedges)
    layoff_cash = sum(r['cash'] for r in desk_trades if r['role'] == 'layoff')
    book_cash = sum(r['cash'] for r in desk_trades if r['role'] == 'book')
    return {
        'storm_ids': requested,
        'num_storms': len(storm_ids),
        'reit': {
            'hedges': hedges,
            'num_hedges': len(hedges),
            'num_triggered': sum(1 for r in hedges if r['triggered']),
            'total_notional': sum(r['notional'] for r in hedges),
            'total_payout': reit_payout,
        },
        'desk': {
            'trades': desk_trades,
            'paid_to_reit': -reit_payout,
            'layoff_cash': layoff_cash,
            'book_cash': book_cash,
            'num_triggered': sum(1 for r in desk_trades if r['triggered']),
            'net': -reit_payout + layoff_cash + book_cash,
        },
    }
