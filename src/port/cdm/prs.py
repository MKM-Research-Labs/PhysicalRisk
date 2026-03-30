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
Physical Risk Swap Common Data Model (CDM) implementation.
Based on Physical_Risk_Swap_CDM v2.1 specification.

Provides standardized data model for physical risk swap instruments
with multi-catchment support.
"""

from typing import Dict, List

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
        self._schema = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": {
                        "type": "text",
                        "description": "Unique identifier for the swap"
                    },
                    "CatchmentID": {
                        "type": "text",
                        "description": "Identifier for the river catchment"
                    },
                    "TradeType": {
                        "type": "text",
                        "description": "Type of physical swap trade"
                    },
                    "CounterParty": {
                        "type": "text",
                        "description": "Unique identifier for the counterparty"
                    },
                    "PartyId": {
                        "type": "text",
                        "description": "Legal Entity Identifier for the party"
                    },
                    "ValuationDate": {
                        "type": "date",
                        "description": "Date of valuation"
                    },
                    "GaugeSetID": {
                        "type": "text",
                        "description": "Identifier for gauge basket"
                    },
                    "ProtectionStart": {
                        "type": "date",
                        "description": "Start date of protection"
                    }
                },
                "LegData": {
                    "LegType": {
                        "type": "menu",
                        "options": ["Fixed", "Float"],
                        "description": "Type of payment leg"
                    },
                    "Payer": {
                        "type": "boolean",
                        "description": "Indicates if party is the payer"
                    },
                    "Currency": {
                        "type": "text",
                        "description": "Currency of the trade"
                    },
                    "Notional": {
                        "type": "decimal",
                        "description": "Notional amount of the trade"
                    },
                    "DayCounter": {
                        "type": "text",
                        "description": "Day count convention"
                    },
                    "FixedLegRate": {
                        "type": "decimal",
                        "description": "Fixed rate for payments"
                    }
                },
                "ScheduleData": {
                    "StartDate": {
                        "type": "date",
                        "description": "Start date of payment schedule"
                    },
                    "EndDate": {
                        "type": "date",
                        "description": "End date of payment schedule"
                    },
                    "Tenor": {
                        "type": "text",
                        "description": "Payment frequency"
                    },
                    "Calendar": {
                        "type": "text",
                        "description": "Business day calendar"
                    }
                },
                "GaugeSet": {
                    "GaugeSetID": {
                        "type": "text",
                        "description": "Identifier for the gauge set"
                    },
                    "CatchmentID": {
                        "type": "text",
                        "description": "Catchment this gauge set belongs to"
                    },
                    "GaugeCount": {
                        "type": "integer",
                        "description": "Number of gauges in basket"
                    },
                    "GaugeBasket": {
                        "type": "array",
                        "items": {
                            "GaugeID": {"type": "text"},
                            "Weight": {"type": "decimal"},
                            "TriggerLevel": {"type": "decimal"}
                        },
                        "description": "Array of gauge references with weights"
                    }
                },
                "Triggers": {
                    "TriggerType": {
                        "type": "menu",
                        "options": ["Any", "All", "Weighted", "Majority"],
                        "description": "How triggers are evaluated"
                    },
                    "TriggerThreshold": {
                        "type": "integer",
                        "description": "Number of gauges required to trigger"
                    },
                    "FloodAlertTrigger": {
                        "type": "decimal",
                        "description": "Water level that triggers flood alert payout"
                    },
                    "FloodWarningTrigger": {
                        "type": "decimal",
                        "description": "Water level that triggers flood warning payout"
                    },
                    "SevereFloodTrigger": {
                        "type": "decimal",
                        "description": "Water level that triggers severe flood payout"
                    }
                },
                "Payouts": {
                    "Currency": {
                        "type": "text",
                        "description": "Currency for payouts"
                    },
                    "FloodAlertPayout": {
                        "type": "decimal",
                        "description": "Payout amount for flood alert trigger"
                    },
                    "FloodWarningPayout": {
                        "type": "decimal",
                        "description": "Payout amount for flood warning trigger"
                    },
                    "SevereFloodPayout": {
                        "type": "decimal",
                        "description": "Payout amount for severe flood trigger"
                    },
                    "MaxPayout": {
                        "type": "decimal",
                        "description": "Maximum total payout"
                    }
                }
            }
        }

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
