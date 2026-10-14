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

        # Legal netting and collateral terms (ISDA Master + CSA). Read by
        # the XVA model: exposure is netted per netting set and reduced by
        # collateral under these terms.
        "CreditSupport": {
            "NettingSets": {
                "type": "array",
                "items": {
                    "NettingSetID": {
                        "type": "text",
                        "description": "Identifier referenced by PhysicalSwap.Header.NettingSetID",
                    },
                    "MasterAgreement": {
                        "type": "menu",
                        "options": ["ISDA2002", "ISDA1992", "None"],
                        "description": "Master agreement governing trades in the netting set",
                    },
                    "CloseOutNetting": {
                        "type": "boolean",
                        "description": "Close-out netting is legally enforceable; if false, each trade is closed out alone",
                    },
                    "CsaType": {
                        "type": "menu",
                        "options": ["None", "VM", "VM+IM"],
                        "description": "Collateral exchanged: none, variation margin only, or variation and initial margin",
                    },
                    "CollateralCurrency": {
                        "type": "text",
                        "description": "Currency of eligible cash collateral",
                    },
                    "Threshold": {
                        "type": "decimal",
                        "description": "Exposure below which no variation margin is called",
                    },
                    "MinimumTransferAmount": {
                        "type": "decimal",
                        "description": "Smallest margin transfer that will be called",
                    },
                    "MarginPeriodOfRiskDays": {
                        "type": "integer",
                        "description": "Business days from last good margin to close-out after a default",
                    },
                    "InitialMarginReceived": {
                        "type": "decimal",
                        "description": "Segregated initial margin (independent amount) held from the counterparty",
                    },
                    "InitialMarginPosted": {
                        "type": "decimal",
                        "description": "Segregated initial margin (independent amount) posted to the counterparty",
                    },
                },
                "description": "Netting sets under which trades with this party are closed out",
            },
        },

        # Credit curve of the party (MKM-XV-001): what its default risk costs.
        # The XVA model bootstraps a hazard curve from these spreads; with no
        # block it falls back to a rating proxy and says so.
        "Credit": {
            "CdsSpreads": {
                "type": "array",
                "items": {
                    "TenorYears": {"type": "decimal", "description": "CDS maturity in years"},
                    "SpreadBps": {"type": "decimal", "description": "Par CDS spread in basis points"},
                },
                "description": "Par CDS spreads by tenor, shortest first",
            },
            "Recovery": {
                "type": "decimal",
                "description": "Recovery rate the spreads are quoted at (0-1)",
            },
            "Source": {
                "type": "menu",
                "options": ["Market", "RatingProxy"],
                "description": "Market quotes, or a proxy derived from the credit rating",
            },
            "AsOf": {
                "type": "date",
                "description": "Date the spreads were observed",
            },
        },
    }
}
