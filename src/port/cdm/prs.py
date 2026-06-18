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
Physical Risk Swap Common Data Model (CDM) implementation.
Based on Physical_Risk_Swap_CDM v2.1 specification.

Provides standardized data model for physical risk swap instruments
with multi-catchment support.  The schema dictionary lives in
``_prs_schema.py`` so this file can stay focused on the validation +
mapping behaviour.
"""

from typing import Dict, List

from ._prs_schema import build_schema
from .base import BaseCDM


class PhysicalRiskSwapCDM(BaseCDM):
    """
    Physical Risk Swap Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for physical risk swap instruments.
    """

    DEFAULT_GAUGE_BASKET_SIZE = 20

    def __init__(self, gauge_basket_size: int = None):
        """
        Initialize the Physical Risk Swap CDM.

        Args:
            gauge_basket_size: Number of gauges in the basket (default: 20)
        """
        self.gauge_basket_size = gauge_basket_size or self.DEFAULT_GAUGE_BASKET_SIZE
        self._schema = build_schema()

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, swap_data: dict) -> Dict[str, List[str]]:
        """
        Validate physical risk swap data against the CDM schema.

        Args:
            swap_data: Swap data to validate

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        try:
            header = swap_data.get("PhysicalSwap", {}).get("Header", {})
            header_errors = []

            if not header.get("SwapID"):
                header_errors.append("Missing required field: SwapID")

            if not header.get("CatchmentID"):
                header_errors.append("Missing recommended field: CatchmentID")

            if header_errors:
                errors["Header"] = header_errors

            # Validate gauge set
            gauge_set = swap_data.get("PhysicalSwap", {}).get("GaugeSet", {})
            gauge_errors = []

            if not gauge_set.get("GaugeSetID"):
                gauge_errors.append("Missing required field: GaugeSetID")

            basket = gauge_set.get("GaugeBasket", [])
            if len(basket) == 0:
                gauge_errors.append("GaugeBasket must contain at least one gauge")
            else:
                for i, gauge in enumerate(basket):
                    if not gauge.get("GaugeID", "").strip():
                        gauge_errors.append(f"GaugeBasket[{i}]: missing required GaugeID")

            if gauge_errors:
                errors["GaugeSet"] = gauge_errors

            return errors

        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_mapping(self, swap: dict) -> dict:
        """
        Create a flat dictionary from nested CDM structure.

        Args:
            swap: Nested swap data in CDM format

        Returns:
            Flat dictionary with snake_case keys
        """
        try:
            ps = swap.get('PhysicalSwap', {})
            header = ps.get('Header', {})
            leg = ps.get('LegData', {})
            schedule = ps.get('ScheduleData', {})
            gauge_set = ps.get('GaugeSet', {})
            triggers = ps.get('Triggers', {})
            payouts = ps.get('Payouts', {})

            swap_data = {
                # Header
                'swap_id': header.get('SwapID'),
                'catchment_id': header.get('CatchmentID'),
                'trade_type': header.get('TradeType'),
                'counter_party': header.get('CounterParty'),
                'party_id': header.get('PartyId'),
                'valuation_date': header.get('ValuationDate'),
                'gauge_set_id': header.get('GaugeSetID'),
                'protection_start': header.get('ProtectionStart'),

                # Leg Data
                'leg_type': leg.get('LegType'),
                'payer': leg.get('Payer'),
                'currency': leg.get('Currency'),
                'notional': leg.get('Notional'),
                'day_counter': leg.get('DayCounter'),
                'fixed_leg_rate': leg.get('FixedLegRate'),

                # Schedule
                'start_date': schedule.get('StartDate'),
                'end_date': schedule.get('EndDate'),
                'tenor': schedule.get('Tenor'),
                'calendar': schedule.get('Calendar'),

                # Gauge Set
                'gauge_set_catchment': gauge_set.get('CatchmentID'),
                'gauge_count': gauge_set.get('GaugeCount'),
                'gauge_basket': gauge_set.get('GaugeBasket', []),

                # Triggers
                'trigger_type': triggers.get('TriggerType'),
                'trigger_threshold': triggers.get('TriggerThreshold'),
                'flood_alert_trigger': triggers.get('FloodAlertTrigger'),
                'flood_warning_trigger': triggers.get('FloodWarningTrigger'),
                'severe_flood_trigger': triggers.get('SevereFloodTrigger'),

                # Payouts
                'payout_currency': payouts.get('Currency'),
                'flood_alert_payout': payouts.get('FloodAlertPayout'),
                'flood_warning_payout': payouts.get('FloodWarningPayout'),
                'severe_flood_payout': payouts.get('SevereFloodPayout'),
                'max_payout': payouts.get('MaxPayout')
            }

            # Remove None values (but keep empty lists)
            return {k: v for k, v in swap_data.items() if v is not None}

        except Exception as e:
            raise ValueError(f"Error creating PRS mapping: {str(e)}")

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return [
            'PhysicalSwap.Header.SwapID',
            'PhysicalSwap.Header.CatchmentID',
            'PhysicalSwap.GaugeSet.GaugeSetID'
        ]
