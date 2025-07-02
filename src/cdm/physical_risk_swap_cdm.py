# Copyright (c) 2025 MKM Research Labs. All rights reserved.
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
Based on Physical_Risk_Swap_CDM v2 specification.

This module provides a standardized data model for physical risk swap data,
enabling consistent processing across different data sources.
"""

import pandas as pd
from typing import Dict, List, Optional

class PhysicalRiskSwapCDM:
    """
    Physical Risk Swap Common Data Model (CDM) implementation.
    Provides a standardized schema and data transformation methods
    for physical risk swap data.
    """
    def __init__(self, gauge_basket_size: int = 20):
        """
        Initialize the Physical Risk Swap CDM with schema definition.
        
        Args:
            gauge_basket_size: Number of gauges in the basket (default: 20)
        """
        self.gauge_basket_size = gauge_basket_size
        self.schema = {
            "PhysicalSwap": {
                "Header": {
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
                        "description": "Identifier for netting set"
                    },
                    "ProtectionStart": {
                        "type": "date",
                        "description": "Start date of protection"
                    },
                    "SettlesAccrual": {
                        "type": "boolean",
                        "description": "Indicates if accrual is settled"
                    },
                    "PaysAtDefaultTime": {
                        "type": "boolean",
                        "description": "Indicates if payment occurs at default time"
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
                    "PaymentConvention": {
                        "type": "text",
                        "description": "Payment date convention"
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
                    },
                    "Convention": {
                        "type": "text",
                        "description": "Business day convention"
                    },
                    "TermConvention": {
                        "type": "text",
                        "description": "Terminal business day convention"
                    },
                    "Rule": {
                        "type": "text",
                        "description": "Schedule generation rule"
                    },
                    "EndOfMonth": {
                        "type": "boolean",
                        "description": "End of month adjustment flag"
                    },
                    "FirstDate": {
                        "type": "date",
                        "description": "First payment date"
                    },
                    "LastDate": {
                        "type": "date",
                        "description": "Last payment date"
                    }
                },
                "GaugeSet": {
                    "GaugeSet": {
                        "type": "text",
                        "description": "Identifier for netting set"
                    },
                    "GaugeBasketSize": {
                        "type": "integer",
                        "description": f"number of gauges so 1 < n < {self.gauge_basket_size + 1}"
                    },
                    **{f"Gauge{i}": {
                        "GaugeIndex": {
                            "type": "integer",
                            "description": f"Index position of gauge {i} in portfolio"
                        },
                        "GaugeID": {
                            "type": "text",
                            "description": f"Unique identifier for sensor {i}"
                        },
                        "PayoutSevereFlood": {
                            "type": "decimal",
                            "description": f"Payout for reaching Severe Flood Warning for gauge {i}"
                        }
                    } for i in range(1, self.gauge_basket_size + 1)}
                }
            }
        }

    def validate_swap(self, swap_data: dict) -> Dict[str, List[str]]:
        """
        Validates physical risk swap data against the CDM schema.
        Returns dictionary of validation errors by section.
        
        Args:
            swap_data: Physical risk swap data to validate
            
        Returns:
            Dictionary of validation errors by section
        """
        errors = {}
        
        try:
            # Validate Header section
            header_errors = []
            header = swap_data.get("PhysicalSwap", {}).get("Header", {})
            
            # Check required fields
            required_header_fields = ["TradeType", "CounterParty", "PartyId"]
            for field in required_header_fields:
                if not header.get(field):
                    header_errors.append(f"Missing required field: {field}")
            
            if header_errors:
                errors["Header"] = header_errors
                
            # Validate LegData section
            leg_errors = []
            leg_data = swap_data.get("PhysicalSwap", {}).get("LegData", {})
            
            # Validate menu fields
            leg_type = leg_data.get("LegType")
            if leg_type and leg_type not in ["Fixed", "Float"]:
                leg_errors.append("Invalid value for LegType")
                
            if leg_errors:
                errors["LegData"] = leg_errors
                
            # Validate ScheduleData section
            schedule_errors = []
            schedule_data = swap_data.get("PhysicalSwap", {}).get("ScheduleData", {})
            
            # Check date consistency
            start_date = schedule_data.get("StartDate")
            end_date = schedule_data.get("EndDate")
            if start_date and end_date:
                # Add date validation logic if needed
                pass
                
            if schedule_errors:
                errors["ScheduleData"] = schedule_errors
                
            # Validate GaugeSet section
            gauge_errors = []
            gauge_set = swap_data.get("PhysicalSwap", {}).get("GaugeSet", {})
            
            # Check that GaugeBasketSize is positive
            basket_size = gauge_set.get("GaugeBasketSize")
            if basket_size is not None and (not isinstance(basket_size, int) or basket_size <= 0):
                gauge_errors.append("GaugeBasketSize must be a positive integer")
            
            # Validate individual gauges (1 to gauge_basket_size)
            for i in range(1, self.gauge_basket_size + 1):
                gauge_key = f"Gauge{i}"
                if gauge_key in gauge_set:
                    gauge_data = gauge_set[gauge_key]
                    if not gauge_data.get("GaugeID"):
                        gauge_errors.append(f"Missing GaugeID for {gauge_key}")
                    
                    # Validate GaugeIndex
                    gauge_index = gauge_data.get("GaugeIndex")
                    if gauge_index is not None:
                        if not isinstance(gauge_index, int) or gauge_index < 1:
                            gauge_errors.append(f"Invalid GaugeIndex for {gauge_key} - must be positive integer")
                    else:
                        gauge_errors.append(f"Missing GaugeIndex for {gauge_key}")
                    
                    # Validate PayoutSevereFlood
                    if gauge_data.get("PayoutSevereFlood") is not None:
                        try:
                            float(gauge_data["PayoutSevereFlood"])
                        except (ValueError, TypeError):
                            gauge_errors.append(f"Invalid PayoutSevereFlood value for {gauge_key}")
                
            if gauge_errors:
                errors["GaugeSet"] = gauge_errors
                    
            return errors
            
        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_swap_mapping(self, swap: dict) -> dict:
        """
        Creates a standardized physical risk swap data dictionary based on the CDM schema.
        
        Args:
            swap: Raw physical risk swap data dictionary
            
        Returns:
            Structured physical risk swap data according to CDM schema
        """
        try:
            swap_data = {
                # Header section
                'trade_type': swap.get('PhysicalSwap', {}).get('Header', {}).get('TradeType'),
                'counter_party': swap.get('PhysicalSwap', {}).get('Header', {}).get('CounterParty'),
                'party_id': swap.get('PhysicalSwap', {}).get('Header', {}).get('PartyId'),
                'valuation_date': swap.get('PhysicalSwap', {}).get('Header', {}).get('ValuationDate'),
                'gauge_set_id': swap.get('PhysicalSwap', {}).get('Header', {}).get('GaugeSetID'),
                'protection_start': swap.get('PhysicalSwap', {}).get('Header', {}).get('ProtectionStart'),
                'settles_accrual': swap.get('PhysicalSwap', {}).get('Header', {}).get('SettlesAccrual'),
                'pays_at_default_time': swap.get('PhysicalSwap', {}).get('Header', {}).get('PaysAtDefaultTime'),
                
                # LegData section
                'leg_type': swap.get('PhysicalSwap', {}).get('LegData', {}).get('LegType'),
                'payer': swap.get('PhysicalSwap', {}).get('LegData', {}).get('Payer'),
                'currency': swap.get('PhysicalSwap', {}).get('LegData', {}).get('Currency'),
                'notional': swap.get('PhysicalSwap', {}).get('LegData', {}).get('Notional'),
                'day_counter': swap.get('PhysicalSwap', {}).get('LegData', {}).get('DayCounter'),
                'payment_convention': swap.get('PhysicalSwap', {}).get('LegData', {}).get('PaymentConvention'),
                'fixed_leg_rate': swap.get('PhysicalSwap', {}).get('LegData', {}).get('FixedLegRate'),
                
                # ScheduleData section
                'start_date': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('StartDate'),
                'end_date': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('EndDate'),
                'tenor': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('Tenor'),
                'calendar': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('Calendar'),
                'convention': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('Convention'),
                'term_convention': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('TermConvention'),
                'rule': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('Rule'),
                'end_of_month': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('EndOfMonth'),
                'first_date': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('FirstDate'),
                'last_date': swap.get('PhysicalSwap', {}).get('ScheduleData', {}).get('LastDate'),
                
                # GaugeSet section
                'gauge_set': swap.get('PhysicalSwap', {}).get('GaugeSet', {}).get('GaugeSet'),
                'gauge_basket_size': swap.get('PhysicalSwap', {}).get('GaugeSet', {}).get('GaugeBasketSize')
            }
            
            # Add individual gauges (1 to gauge_basket_size)
            gauge_set_data = swap.get('PhysicalSwap', {}).get('GaugeSet', {})
            for i in range(1, self.gauge_basket_size + 1):
                gauge_key = f"Gauge{i}"
                if gauge_key in gauge_set_data:
                    gauge_data = gauge_set_data[gauge_key]
                    swap_data[f'gauge_{i}_index'] = gauge_data.get('GaugeIndex')
                    swap_data[f'gauge_{i}_id'] = gauge_data.get('GaugeID')
                    swap_data[f'gauge_{i}_payout_severe_flood'] = gauge_data.get('PayoutSevereFlood')
            
            # Remove None values from the dictionary
            return {k: v for k, v in swap_data.items() if v is not None}
            
        except Exception as e:
            raise ValueError(f"Error creating swap mapping: {str(e)}")