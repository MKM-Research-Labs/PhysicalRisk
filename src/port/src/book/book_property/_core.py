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
Book generator — the REIT's hedge book.

The REIT (asset owner) buys gauge-triggered PRS protection from the desk
(market-maker) on its residential properties and commercial assets, one hedge
per asset. Each hedge pays its notional when the asset's nearest real gauge
reaches its severe level, and is sized from the asset's value.

The desk then lays off part of that risk: for every gauge it has sold the REIT
protection on, it buys the same gauge protection from an external
counterparty (see ``generate_reit_layoff_book``).

Assets are selected across the flood-risk spectrum (high / medium / low
flood_count). Pricing uses the event-count fair spread from the asset hazard
curves rather than the gauge-level analytical pricer.
"""

import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import database
from config.port import (
    PROPERTY_BOOK_HEDGE_RATIO,
    PROPERTY_BOOK_LAYOFF_RATIO,
    PROPERTY_BOOK_NOTIONAL_STEP,
    PROPERTY_BOOK_NUM_COMMERCIAL,
    PROPERTY_BOOK_NUM_TRADES,
    PROPERTY_BOOK_TENOR_WEIGHTS,
    PROPERTY_BOOK_TENORS,
    TRIGGER_RATE_KEY,
)

from ..book_common import _load_counterparties, _price_and_save_trade  # noqa: F401
from ._select import (
    _lookup_commercial_metadata,
    _lookup_property_metadata,
    _match_tenor_idx,
    _select_properties,
)

logger = logging.getLogger(__name__)

# Header.TradePurpose on the desk's lay-off trades
LAYOFF_PURPOSE = 'REITLayoff'


def _hedge_notional(asset_value: float) -> int:
    """Hedge notional for an asset: PROPERTY_BOOK_HEDGE_RATIO of its value,
    rounded to PROPERTY_BOOK_NOTIONAL_STEP and never below one step."""
    step = PROPERTY_BOOK_NOTIONAL_STEP
    return max(step, int(round(asset_value * PROPERTY_BOOK_HEDGE_RATIO / step)) * step)


def _asset_pools(catchment_id: str, include_resilient: bool) -> List[Dict]:
    """Residential and commercial pools: hazard curves, BRI curves, metadata."""
    pools = []
    for asset_class, get_curves, get_portfolio, records_key, lookup, num in (
        ('residential', database.get_property_hazard_curves,
         database.get_property_portfolio, 'properties',
         _lookup_property_metadata, PROPERTY_BOOK_NUM_TRADES),
        ('commercial', database.get_commercial_hazard_curves,
         database.get_commercial_portfolio, 'commercial_assets',
         _lookup_commercial_metadata, PROPERTY_BOOK_NUM_COMMERCIAL),
    ):
        curves_data = get_curves(catchment_id) or {}
        curves = curves_data.get('property_hazard_curves', {})
        if not curves:
            continue
        bri = {}
        if include_resilient:
            bri = (get_curves(catchment_id, mode='bri') or {}).get(
                'property_hazard_curves', {})
        pools.append({
            'asset_class': asset_class,
            'curves': curves,
            'bri_curves': bri,
            'records': (get_portfolio(catchment_id) or {}).get(records_key, []),
            'lookup': lookup,
            'num': num,
            'num_storms': curves_data.get('metadata', {}).get('num_storms', 20000),
        })
    return pools


def generate_property_book(
    output_dir: Path,
    catchment_id: str = 'thames',
    seed: Optional[int] = 43,
    include_resilient: bool = False,
) -> List[Dict]:
    """
    Generate the REIT's hedge book for the Trading Desk Client tab.

    Books one gauge-triggered PRS per hedgeable asset — residential
    properties and commercial assets — with the REIT as payer (buying
    protection) and the desk as receiver. Hazard curves and asset metadata
    are read for *catchment_id* through the ``database`` seam.

    Each hedge's notional is ``PROPERTY_BOOK_HEDGE_RATIO`` of the asset's
    value. When ``include_resilient`` is set and the asset has a BRI-adjusted
    curve, the hedge is priced on the resilient (BRI-adjusted floor) spread
    and tagged ``PropertySet.PRSVariant = 'resilient'``; otherwise it is
    priced on the surveyed-floor spread and tagged ``'pure'``.

    Args:
        output_dir:      Directory to write PRS-P*.json trade files.
        catchment_id:    Catchment identifier.
        seed:            Random seed (default 43, distinct from gauge book's 42).
        include_resilient: Price on the BRI-adjusted curve where one exists.

    Returns:
        List of generated CDM records.
    """
    if seed is not None:
        random.seed(seed)

    pools = _asset_pools(catchment_id, include_resilient)
    if not pools:
        logger.warning('No property or commercial hazard curves — skipping REIT book')
        return []

    gauge_curves = (database.get_gauge_hazard_curves(catchment_id) or {}).get(
        'hazard_curves', {})

    # All REIT hedges are between the REIT (buyer) and the desk (seller).
    counterparties = [{'id': 'CTPY-REIT-001', 'name': 'Thames Property REIT'}]

    output_dir.mkdir(parents=True, exist_ok=True)
    trades = []
    ctpy_idx = 0
    base_date = datetime.now() - timedelta(days=random.randint(5, 30))

    for pool in pools:
        for item in _select_properties(pool['curves'], pool['num']):
            asset_id = item['property_id']
            curve = item['curve']

            tenor = random.choices(
                PROPERTY_BOOK_TENORS, weights=PROPERTY_BOOK_TENOR_WEIGHTS, k=1)[0]
            fair_spread = item['spreads'][_match_tenor_idx(item['tenors'], tenor)]
            if fair_spread <= 0:
                continue

            # Trigger gauge: the nearest real gauge. Synthetic (SYNTH-*)
            # interpolation anchors are never traded.
            ref_gauge = next(
                (g for g in curve.get('nearest_gauges', [])
                 if not str(g.get('gauge_id', '')).startswith('SYNTH-')),
                None,
            )
            if ref_gauge is None:
                continue
            gauge_id = ref_gauge['gauge_id']
            gauge_name = gauge_curves.get(gauge_id, {}).get('gauge_name', gauge_id)

            meta = pool['lookup'](pool['records'], asset_id)
            asset_value = meta.get('PropertyValue', 0) or 0
            if asset_value <= 0:
                continue  # nothing to size the hedge from
            # Flood zone from the hazard curve (more reliable than the record)
            meta['EAFloodZone'] = curve.get('flood_zone', meta.get('EAFloodZone', ''))
            meta['AssetClass'] = pool['asset_class']
            meta['ReferenceGauge'] = {
                'GaugeID': gauge_id,
                'Distance': round(ref_gauge.get('distance_km', 0), 3),
            }

            flood_count = item['flood_count']
            variant = 'pure'
            bri_curve = pool['bri_curves'].get(asset_id)
            if bri_curve:
                bri_spreads = bri_curve.get('term_structure', {}).get(
                    'severe', {}).get('prs_spread_bps', [])
                bri_tenors = bri_curve.get('term_structure', {}).get('tenors', [])
                if bri_spreads and bri_tenors:
                    bri_spread = bri_spreads[_match_tenor_idx(bri_tenors, tenor)]
                    if bri_spread > 0:
                        fair_spread = bri_spread
                        flood_count = bri_curve.get('flood_count', flood_count)
                        variant = 'resilient'
            num_storms = pool['num_storms']
            hazard_rate = flood_count / num_storms if num_storms > 0 else 0.02

            record, ctpy_idx = _price_and_save_trade(
                gauge_id=gauge_id,
                gauge_name=gauge_name,
                catchment_id=catchment_id,
                is_payer=True,  # the REIT buys protection; the desk sells it
                tenor=tenor,
                notional=_hedge_notional(asset_value),
                trigger='severe',
                hazard_rate=hazard_rate,
                counterparties=counterparties,
                ctpy_idx=ctpy_idx,
                base_date=base_date,
                output_dir=output_dir,
                property_set={**meta, 'PRSVariant': variant},
                fair_spread_override=fair_spread,
            )
            trades.append(record)

    logger.info('Generated %d REIT hedge trades', len(trades))
    return trades


def generate_reit_layoff_book(
    reit_trades: List[Dict],
    output_dir: Path,
    catchment_id: str = 'thames',
    seed: Optional[int] = 44,
) -> List[Dict]:
    """Book the desk's lay-off of the REIT hedges.

    For each gauge the desk has sold the REIT protection on, the desk buys
    ``PROPERTY_BOOK_LAYOFF_RATIO`` of that protection back from an external
    counterparty as a plain gauge PRS (desk = payer), for the longest tenor
    sold on that gauge. Priced on the gauge's analytical severe hazard rate.

    Returns:
        List of generated CDM records (empty when there are no REIT trades).
    """
    if seed is not None:
        random.seed(seed)

    by_gauge: Dict[str, Dict] = {}
    for t in reit_trades:
        ps = t['PhysicalSwap']
        g = ps['GaugeSet']['GaugeBasket'][0]
        tenor = _tenor_years(ps['ScheduleData'])
        slot = by_gauge.setdefault(g['GaugeID'], {
            'gauge_name': g.get('GaugeName', g['GaugeID']), 'notional': 0, 'tenor': 0})
        slot['notional'] += ps['LegData']['Notional']
        slot['tenor'] = max(slot['tenor'], tenor)
    if not by_gauge:
        return []

    gauge_curves = (database.get_gauge_hazard_curves(catchment_id) or {}).get(
        'hazard_curves', {})
    counterparties = _load_counterparties(catchment_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    trades = []
    ctpy_idx = random.randrange(len(counterparties))
    base_date = datetime.now() - timedelta(days=random.randint(5, 30))
    step = PROPERTY_BOOK_NOTIONAL_STEP

    for gauge_id in sorted(by_gauge):
        slot = by_gauge[gauge_id]
        notional = max(step, int(round(
            slot['notional'] * PROPERTY_BOOK_LAYOFF_RATIO / step)) * step)
        hazard_rate = gauge_curves.get(gauge_id, {}).get(
            TRIGGER_RATE_KEY['severe'], 0.0)
        record, ctpy_idx = _price_and_save_trade(
            gauge_id=gauge_id,
            gauge_name=slot['gauge_name'],
            catchment_id=catchment_id,
            is_payer=True,  # the desk buys protection back
            tenor=slot['tenor'],
            notional=notional,
            trigger='severe',
            hazard_rate=hazard_rate,
            counterparties=counterparties,
            ctpy_idx=ctpy_idx,
            base_date=base_date,
            output_dir=output_dir,
        )
        # Mark it so the storm view can tell a lay-off from the desk's other
        # gauge trades on the same gauge
        record['PhysicalSwap']['Header']['TradePurpose'] = LAYOFF_PURPOSE
        database.save_prs_trade(
            catchment_id, record['PhysicalSwap']['Header']['SwapID'], record)
        trades.append(record)

    logger.info('Generated %d desk lay-off trades', len(trades))
    return trades


def _tenor_years(schedule: Dict) -> int:
    """Whole years between a trade's start and end dates (at least 1)."""
    start = datetime.strptime(schedule['StartDate'], '%Y-%m-%d')
    end = datetime.strptime(schedule['EndDate'], '%Y-%m-%d')
    return max(1, round((end - start).days / 365.25))
