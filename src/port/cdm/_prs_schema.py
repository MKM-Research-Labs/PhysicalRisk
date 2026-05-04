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
Physical Risk Swap CDM schema definition.

The full PhysicalSwap field schema (Header, LegData, ScheduleData,
GaugeSet, Triggers, Payouts) lives here so ``prs.py`` can stay focused
on validation and mapping behaviour rather than carrying the ~150-line
schema dict inline.
"""

from typing import Dict


def build_schema() -> Dict:
    """Return the Physical Risk Swap CDM schema dictionary.

    Spec: Physical_Risk_Swap_CDM v2.1.
    """
    return {
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
