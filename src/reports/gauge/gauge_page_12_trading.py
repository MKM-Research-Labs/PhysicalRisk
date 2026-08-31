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
Page 12: Trading Activity
Gauge blotter table (open PRS trades) and market hazard curve comparison.
"""

import json
import logging
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from .gauge_page_00_base import GaugeBasePage
from config.theme import colour

logger = logging.getLogger(__name__)


class GaugeTradingPage(GaugeBasePage):
    """Generates trading activity page for a gauge report."""

    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        elements = []
        elements.append(Paragraph("Trading Activity", self.styles['SectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        try:
            gauge_id = gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            elements.append(Paragraph(
                "No gauge ID available for trading lookup.",
                self.styles['Normal']
            ))
            return elements

        # Load trades and market state
        trades = self._load_gauge_trades(gauge_id)
        market_state = self._load_market_state()

        # Section 1: Gauge Blotter
        elements.extend(self._build_blotter_section(gauge_id, trades))
        elements.append(Spacer(1, self.spacing['major_section']))

        # Section 2: Market Hazard Curves
        elements.extend(self._build_market_curves_section(gauge_id, market_state))

        return elements

    def _load_gauge_trades(self, gauge_id: str) -> List[Dict]:
        """Load open PRS trades for this gauge via the prs_trade seam."""
        import database
        trades = []
        catchment = database.active_catchment()
        for swap_id in database.iter_prs_trade_ids(catchment):
            try:
                data = database.get_prs_trade(catchment, swap_id) or {}
                ps = data.get('PhysicalSwap', {})
                gauge_basket = ps.get('GaugeSet', {}).get('GaugeBasket', [])
                gauge_ids = [g.get('GaugeID') for g in gauge_basket]
                if gauge_id in gauge_ids:
                    trades.append(ps)
            except Exception as e:
                logger.debug(f"Skipping trade {swap_id}: {e}")

        return trades

    def _load_market_state(self) -> Dict:
        """Load market state from trading directory."""
        try:
            from config import config
            ms_path = config.get_trading_dir() / 'market_state.json'
            if ms_path.exists():
                return json.loads(ms_path.read_text())
        except Exception as e:
            logger.debug(f"Could not load market state: {e}")
        return {}

    def _build_blotter_section(self, gauge_id: str,
                               trades: List[Dict]) -> List:
        """Build the gauge blotter table."""
        elements = []
        elements.append(Paragraph("Open Trades", self.styles['SubSectionHeader']))

        if not trades:
            elements.append(Paragraph(
                f"No open PRS trades for gauge {gauge_id}.",
                self.styles['Normal']
            ))
            return elements

        header = ['Swap ID', 'Dir', 'Trigger', 'Tenor', 'Notional',
                  'Spread', 'Fair Spd', 'NPV']
        rows = [header]

        for ps in trades:
            hdr = ps.get('Header', {})
            leg = ps.get('LegData', {})
            sched = ps.get('ScheduleData', {})
            pricing = ps.get('Pricing', {})
            basket = ps.get('GaugeSet', {}).get('GaugeBasket', [])

            swap_id = hdr.get('SwapID', 'N/A')
            is_payer = leg.get('Payer', False)
            direction = 'Pay' if is_payer else 'Rcv'
            trigger = pricing.get('TriggerLevel', 'N/A')
            notional = leg.get('Notional', 0)
            spread = pricing.get('SpreadBps', 0)
            fair_spread = pricing.get('FairSpreadBps', 0)
            npv = pricing.get('NPV', 0)

            # Derive tenor from schedule
            tenor_str = sched.get('Tenor', '')
            start = sched.get('StartDate', '')
            end = sched.get('EndDate', '')
            tenor_label = self._derive_tenor(start, end)

            rows.append([
                swap_id,
                direction,
                trigger.capitalize() if trigger != 'N/A' else 'N/A',
                tenor_label,
                f"{notional:,.0f}",
                f"{spread:.1f}",
                f"{fair_spread:.1f}",
                f"{npv:,.0f}"
            ])

        col_widths = [1.3*inch, 0.5*inch, 0.7*inch, 0.6*inch,
                      1.1*inch, 0.7*inch, 0.7*inch, 0.9*inch]
        table = Table(rows, colWidths=col_widths)
        table.setStyle(self.table_styles['standard'])
        elements.append(table)

        elements.append(Spacer(1, self.spacing['minor_section']))
        elements.append(Paragraph(
            f"Total trades: {len(trades)}",
            self.styles['Normal']
        ))

        return elements

    def _build_market_curves_section(self, gauge_id: str,
                                     market_state: Dict) -> List:
        """Build market hazard curve comparison table."""
        elements = []
        elements.append(Paragraph("Market Hazard Term Structure",
                                  self.styles['SubSectionHeader']))

        hts = market_state.get('hazard_term_structure', {})
        gauge_hts = hts.get(gauge_id, {})

        if not gauge_hts:
            elements.append(Paragraph(
                f"No market hazard term structure for gauge {gauge_id}.",
                self.styles['Normal']
            ))
            return elements

        # Build table: tenors across columns, triggers as rows
        tenors = ['1', '2', '3', '4', '5']
        header = ['Trigger'] + [f"{t}Y" for t in tenors]
        rows = [header]

        trigger_colors = {
            'alert': colour('amber-yellow'),
            'warning': colour('amber-bright'),
            'severe': colour('red-bright'),
        }

        for trigger in ['alert', 'warning', 'severe']:
            rates = gauge_hts.get(trigger, {})
            row = [trigger.capitalize()]
            for t in tenors:
                rate = rates.get(t)
                if rate is not None:
                    row.append(f"{rate * 10000:.1f} bps")
                else:
                    row.append('N/A')
            rows.append(row)

        col_widths = [1.2*inch] + [1.06*inch] * 5
        table = Table(rows, colWidths=col_widths)
        table.setStyle(self.table_styles['flood_risk'])
        elements.append(table)

        # Show adjustments if any
        adjustments = market_state.get('gauge_adjustments', {})
        gauge_adj = adjustments.get(gauge_id, {})
        if gauge_adj:
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Market Adjustments",
                                      self.styles['SubSectionHeader']))
            adj_rows = [['Parameter', 'Value']]
            for key, val in gauge_adj.items():
                if key == 'adjusted_at':
                    adj_rows.append(['Last Adjusted', str(val)[:19]])
                else:
                    label = key.replace('_', ' ').title()
                    if isinstance(val, float):
                        adj_rows.append([label, f"{val * 10000:.1f} bps"])
                    else:
                        adj_rows.append([label, str(val)])

            adj_table = Table(adj_rows, colWidths=self.table_widths['two_col'])
            adj_table.setStyle(self.table_styles['standard'])
            elements.append(adj_table)

        return elements

    def _derive_tenor(self, start_date: str, end_date: str) -> str:
        """Derive tenor label from start and end dates."""
        if not start_date or not end_date:
            return 'N/A'
        try:
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            years = round((end - start).days / 365.25)
            return f"{years}Y"
        except Exception:
            return 'N/A'
