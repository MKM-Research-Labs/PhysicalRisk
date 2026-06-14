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

"""Counterparty CDM schema definition (FINOS Party / Counterparty analogue)."""

COUNTERPARTY_SCHEMA = {
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
