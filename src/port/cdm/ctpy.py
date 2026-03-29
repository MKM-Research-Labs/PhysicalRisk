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
Counterparty / Party Common Data Model (CDM) implementation.

Based on FINOS Common Domain Model Party / Counterparty concepts.

This module provides a standardized data model for legal entities and
their roles as counterparties on trades, aligned with CDM usage of
Party, Counterparty and CounterpartyRoleEnum (Party1 / Party2).

Intended for:
- Reusable party master data (LEI, name, contact, accounts)
- Trade-time counterparty role assignment (Party1 / Party2)
- Mapping into PRS trades (Physical Risk Swaps) following CDM guidelines
"""

from typing import Dict, List

from .base import BaseCDM


class CounterpartyCDM(BaseCDM):
    """
    Counterparty / Party Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for counterparties on trades, following FINOS CDM patterns for
    Party and Counterparty.
    """

    def __init__(self):
        """Initialize the Counterparty CDM with schema definition."""
        self._schema = {
            "CounterpartySet": {
                # Party master data (reusable, CDM Party analogue)
                "Party": {
                    "PartyID": {
                        "type": "text",
                        "description": "Primary identifier for the legal entity (e.g., LEI or internal ID)",
                    },
                    "PartyIdScheme": {
                        "type": "text",
                        "description": "Identifier scheme (e.g., 'LEI', 'Internal', 'BIC')",
                    },
                    "PartyName": {
                        "type": "text",
                        "description": "Registered name of the legal entity",
                    },
                    "BusinessUnits": {
                        "type": "array",
                        "items": {
                            "BusinessUnitName": {"type": "text"},
                            "BusinessUnitId": {"type": "text"},
                        },
                        "description": "List of business units within the party",
                    },
                    "Accounts": {
                        "type": "array",
                        "items": {
                            "AccountID": {"type": "text"},
                            "AccountDescription": {"type": "text"},
                            "AccountCurrency": {"type": "text"},
                        },
                        "description": "List of trading/settlement accounts",
                    },
                    "ContactInformation": {
                        "PrimaryEmail": {
                            "type": "text",
                            "description": "Primary contact email address",
                        },
                        "PrimaryPhone": {
                            "type": "text",
                            "description": "Primary contact phone number",
                        },
                        "AddressLine1": {
                            "type": "text",
                            "description": "Address line 1",
                        },
                        "AddressLine2": {
                            "type": "text",
                            "description": "Address line 2 (optional)",
                        },
                        "City": {
                            "type": "text",
                            "description": "City / locality",
                        },
                        "PostCode": {
                            "type": "text",
                            "description": "Postal / ZIP code",
                        },
                        "Country": {
                            "type": "text",
                            "description": "Country (ISO 3166-1 alpha-2 preferred)",
                        },
                    },
                    "NaturalPersons": {
                        "type": "array",
                        "items": {
                            "PersonID": {"type": "text"},
                            "FirstName": {"type": "text"},
                            "LastName": {"type": "text"},
                            "Role": {"type": "text"},
                        },
                        "description": "Named individuals associated with this party (e.g., trader, sales)",
                    },
                },

                # Counterparty role assignment (CDM Counterparty analogue)
                "Counterparties": {
                    "type": "array",
                    "items": {
                        "CounterpartyRole": {
                            "type": "menu",
                            "options": ["Party1", "Party2"],
                            "description": "Role of the party on the trade (CDM CounterpartyRoleEnum)",
                        },
                        "PartyRef": {
                            "type": "text",
                            "description": "Reference to Party.PartyID for this counterparty",
                        },
                        "ExternalPartyId": {
                            "type": "text",
                            "description": "Optional external system ID for the party in this role",
                        },
                        "BookingAccountRef": {
                            "type": "text",
                            "description": "Reference to the account used for booking (if applicable)",
                        },
                    },
                    "description": "Set of counterparties for the trade, typically exactly two entries",
                },

                # Optional ancillary parties for fees, agents, etc.
                "AncillaryParties": {
                    "type": "array",
                    "items": {
                        "PartyRole": {
                            "type": "text",
                            "description": "Role of the ancillary party (e.g., 'CalculationAgent', 'Broker')",
                        },
                        "PartyRef": {
                            "type": "text",
                            "description": "Reference to Party.PartyID",
                        },
                    },
                    "description": "Non-principal parties associated with the trade",
                },
            }
        }

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, ctpy_data: dict) -> Dict[str, List[str]]:
        """
        Validate counterparty / party data against the CDM schema.

        Args:
            ctpy_data: Counterparty data to validate

        Returns:
            Dictionary of validation errors by section
        """
        errors: Dict[str, List[str]] = {}

        try:
            root = ctpy_data.get("CounterpartySet", {})

            # Validate Party section (basic requirements)
            party = root.get("Party", {})
            party_errors: List[str] = []

            if not party.get("PartyID"):
                party_errors.append("Missing required field: Party.PartyID")

            if not party.get("PartyName"):
                party_errors.append("Missing required field: Party.PartyName")

            if party_errors:
                errors["Party"] = party_errors

            # Validate Counterparties (must be 2, both Party1 and Party2 present)
            cp_errors: List[str] = []
            cps = root.get("Counterparties", []) or []

            if len(cps) == 0:
                cp_errors.append("Counterparties array must contain at least one entry")
            else:
                roles = set()
                for idx, cp in enumerate(cps):
                    role = cp.get("CounterpartyRole")
                    party_ref = cp.get("PartyRef")

                    if not role:
                        cp_errors.append(f"Counterparties[{idx}]: Missing CounterpartyRole")
                    elif role not in ["Party1", "Party2"]:
                        cp_errors.append(
                            f"Counterparties[{idx}]: Invalid CounterpartyRole '{role}'"
                        )
                    else:
                        roles.add(role)

                    if not party_ref:
                        cp_errors.append(f"Counterparties[{idx}]: Missing PartyRef")

                # Enforce typical CDM pattern: exactly Party1 and Party2
                if len(cps) == 2 and roles != {"Party1", "Party2"}:
                    cp_errors.append(
                        "When exactly two counterparties are supplied, roles must be Party1 and Party2"
                    )

            if cp_errors:
                errors["Counterparties"] = cp_errors

            return errors

        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_mapping(self, ctpy: dict) -> dict:
        """
        Create a flat dictionary from nested CDM counterparty structure.

        Args:
            ctpy: Nested counterparty data in CDM format

        Returns:
            Flat dictionary with snake_case keys
        """
        try:
            root = ctpy.get("CounterpartySet", {})

            party = root.get("Party", {})
            cps = root.get("Counterparties", []) or []
            ancillary = root.get("AncillaryParties", []) or []

            # Build role-specific view (Party1 / Party2) if present
            party1 = next((c for c in cps if c.get("CounterpartyRole") == "Party1"), {})
            party2 = next((c for c in cps if c.get("CounterpartyRole") == "Party2"), {})

            ctpy_data = {
                # Party (master) fields
                "party_id": party.get("PartyID"),
                "party_id_scheme": party.get("PartyIdScheme"),
                "party_name": party.get("PartyName"),

                # ContactInformation
                "primary_email": party.get("ContactInformation", {}).get("PrimaryEmail"),
                "primary_phone": party.get("ContactInformation", {}).get("PrimaryPhone"),
                "address_line1": party.get("ContactInformation", {}).get("AddressLine1"),
                "address_line2": party.get("ContactInformation", {}).get("AddressLine2"),
                "city": party.get("ContactInformation", {}).get("City"),
                "post_code": party.get("ContactInformation", {}).get("PostCode"),
                "country": party.get("ContactInformation", {}).get("Country"),

                # Role-specific fields
                "party1_ref": party1.get("PartyRef"),
                "party1_external_id": party1.get("ExternalPartyId"),
                "party1_booking_account_ref": party1.get("BookingAccountRef"),

                "party2_ref": party2.get("PartyRef"),
                "party2_external_id": party2.get("ExternalPartyId"),
                "party2_booking_account_ref": party2.get("BookingAccountRef"),

                # Aggregated counts
                "business_unit_count": len(party.get("BusinessUnits", []) or []),
                "account_count": len(party.get("Accounts", []) or []),
                "natural_person_count": len(party.get("NaturalPersons", []) or []),
                "counterparty_count": len(cps),
                "ancillary_party_count": len(ancillary),
            }

            # Remove None values
            return {k: v for k, v in ctpy_data.items() if v is not None}

        except Exception as e:
            raise ValueError(f"Error creating counterparty mapping: {str(e)}")

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return [
            "CounterpartySet.Party.PartyID",
            "CounterpartySet.Party.PartyName",
            "CounterpartySet.Counterparties[0].CounterpartyRole",
            "CounterpartySet.Counterparties[0].PartyRef",
        ]
