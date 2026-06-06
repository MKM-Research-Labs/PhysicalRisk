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


"""Counterparty record builders (REIT + external) for the portfolio generator."""

import random
import uuid
from typing import Any, Dict

from config import config

from port.src.counterparty._data import (
    _ADDRESSES,
    _CONTACTS,
    _RATING_AGENCIES,
    _RATINGS,
    _SORT_CODES,
)


class _RecordBuilderMixin:
    """Record-building methods for CounterpartyPortfolioGenerator."""

    @staticmethod
    def _generate_reit() -> Dict[str, Any]:
        """Build the fixed CTPY-REIT-001 counterparty record.

        Trading rule: property PRS trades are *exclusively* between the
        trader and the REIT client.  The REIT is a fixed (non-random)
        counterparty that always appears in counterparty.json, even
        when ``--num-properties`` is small or zero.
        """
        party_id = "CTPY-REIT-001"
        full_name = "Thames Property REIT"
        short_name = "Thames REIT"
        ctpy_type = "REIT"
        # Deterministic banking details so re-runs don't churn the file
        sort_code = "20-00-00"
        account_number = "10000001"
        iban = "GB29MKMM20000010000001"
        swift_bic = "REITGB2L"
        lei = "REIT" + "0" * 16
        email = "treasury@thamespropertyreit.co.uk"

        return {
            "CounterpartySet": {
                "Party": {
                    "PartyID": party_id,
                    "PartyIdScheme": "Internal",
                    "PartyName": full_name,
                    "BusinessUnits": [
                        {
                            "BusinessUnitName": f"{ctpy_type} - {short_name}",
                            "BusinessUnitId": f"BU-{party_id}",
                        }
                    ],
                    "Accounts": [
                        {
                            "AccountID": f"ACC-{party_id}-GBP",
                            "AccountDescription": f"{config.CURRENCY} trading/settlement - {short_name}",
                            "AccountCurrency": config.CURRENCY,
                            "SortCode": sort_code,
                            "AccountNumber": account_number,
                            "IBAN": iban,
                            "BIC": swift_bic,
                        },
                        {
                            "AccountID": f"ACC-{party_id}-COLL",
                            "AccountDescription": f"Collateral account - {short_name}",
                            "AccountCurrency": config.CURRENCY,
                        },
                    ],
                    "ContactInformation": {
                        "PrimaryEmail": email,
                        "PrimaryPhone": "+44 20 7000 0001",
                        "AddressLine1": "1 Thames Embankment",
                        "AddressLine2": "Southwark",
                        "City": "London",
                        "PostCode": "SE1 9AA",
                        "Country": "GB",
                    },
                    "NaturalPersons": [
                        {
                            "PersonID": "NP-REIT01",
                            "FirstName": "Sarah",
                            "LastName": "Whitfield",
                            "Role": "Treasurer",
                            "Email": email,
                            "Phone": "+44 20 7000 0002",
                            "SymphonyID": "sarah.whitfield@thamespropertyreit.symphony.com",
                        }
                    ],
                },
                "Counterparties": [
                    {
                        "CounterpartyRole": "Party1",
                        "PartyRef": "MKM-RESEARCH-LABS",
                        "ExternalPartyId": "MKM-001",
                        "BookingAccountRef": "ACC-MKM-GBP",
                    },
                    {
                        "CounterpartyRole": "Party2",
                        "PartyRef": party_id,
                        "ExternalPartyId": lei,
                        "BookingAccountRef": f"ACC-{party_id}-GBP",
                    },
                ],
                "AncillaryParties": [],
                "_platform": {
                    "ShortName": short_name,
                    "PartyType": ctpy_type,
                    "LEI": lei,
                    "SWIFT_BIC": swift_bic,
                    "Jurisdiction": "UK",
                    "Status": "Active",
                    "CatchmentID": config.catchment_id,
                    # REITs aren't typically rated by the agencies; use a
                    # representative IG anchor so downstream pricers that
                    # expect a rating field have something sensible.
                    "CreditRating": "A",
                    "RatingAgency": "Internal",
                    "CreditLimit": 200_000_000,
                    "CurrentExposure": 0.0,
                    "CollateralPosted": 0.0,
                    "MaxTenor": 30,
                    "MaxNotional": 100_000_000,
                    "ISDAMasterAgreement": True,
                    "CSAAgreement": True,
                    "NettingAgreement": True,
                    "PreferredCurrency": config.CURRENCY,
                    # Marker so downstream consumers can filter
                    # (e.g., the property-PRS pricer / blotter REIT view).
                    "IsREIT": True,
                },
            }
        }

    def _generate_one(self, index: int, full_name: str, short_name: str,
                       ctpy_type: str) -> Dict[str, Any]:
        """Generate a single counterparty record in FINOS CDM format."""
        party_id = f"CTPY-{uuid.uuid4().hex[:8]}"
        first_name, last_name, role = _CONTACTS[index % len(_CONTACTS)]
        addr_street, addr_area, addr_postcode = _ADDRESSES[index % len(_ADDRESSES)]
        lei = f"{random.randint(1000, 9999)}00{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=14))}"

        # Rating quality correlates with institution type
        if ctpy_type in ("Bank", "Government Agency"):
            rating_pool = _RATINGS[:6]  # up to A-
        elif ctpy_type in ("Insurer", "Reinsurer"):
            rating_pool = _RATINGS[:7]
        else:
            rating_pool = _RATINGS[3:]  # AA- down to BBB-

        # CSA: banks/insurers/reinsurers always have one; others sometimes
        if ctpy_type in ("Bank", "Insurer", "Reinsurer"):
            has_csa = True
        else:
            has_csa = random.choice([True, True, False])

        email_domain = short_name.replace(' ', '').replace('&', '').lower()
        email = f"{first_name.lower()}.{last_name.lower()}@{email_domain}.co.uk"
        sort_code = _SORT_CODES[index % len(_SORT_CODES)]
        account_number = f"{random.randint(10000000, 99999999)}"
        iban = f"GB{random.randint(10, 99)}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))}{sort_code.replace('-', '')}{account_number}"
        swift_bic = f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))}GB2L"
        symphony_id = f"{first_name.lower()}.{last_name.lower()}@{email_domain}.symphony.com"

        credit_limit = random.choice([25, 50, 100, 150, 200, 500]) * 1_000_000
        current_exposure = round(random.uniform(0, credit_limit * 0.3), 2)

        return {
            "CounterpartySet": {
                "Party": {
                    "PartyID": party_id,
                    "PartyIdScheme": "Internal",
                    "PartyName": full_name,
                    "BusinessUnits": [
                        {
                            "BusinessUnitName": f"{ctpy_type} - {short_name}",
                            "BusinessUnitId": f"BU-{party_id}",
                        }
                    ],
                    "Accounts": [
                        {
                            "AccountID": f"ACC-{party_id}-GBP",
                            "AccountDescription": f"{config.CURRENCY} trading/settlement - {short_name}",
                            "AccountCurrency": config.CURRENCY,
                            "SortCode": sort_code,
                            "AccountNumber": account_number,
                            "IBAN": iban,
                            "BIC": swift_bic,
                        },
                        {
                            "AccountID": f"ACC-{party_id}-COLL",
                            "AccountDescription": f"Collateral account - {short_name}",
                            "AccountCurrency": config.CURRENCY,
                        },
                    ],
                    "ContactInformation": {
                        "PrimaryEmail": email,
                        "PrimaryPhone": f"+44 20 {random.randint(7000, 7999)} {random.randint(1000, 9999)}",
                        "AddressLine1": addr_street,
                        "AddressLine2": addr_area,
                        "City": "London",
                        "PostCode": addr_postcode,
                        "Country": "GB",
                    },
                    "NaturalPersons": [
                        {
                            "PersonID": f"NP-{uuid.uuid4().hex[:6]}",
                            "FirstName": first_name,
                            "LastName": last_name,
                            "Role": role,
                            "Email": email,
                            "Phone": f"+44 20 {random.randint(7000, 7999)} {random.randint(1000, 9999)}",
                            "SymphonyID": symphony_id,
                        }
                    ],
                },
                "Counterparties": [
                    {
                        "CounterpartyRole": "Party1",
                        "PartyRef": "MKM-RESEARCH-LABS",
                        "ExternalPartyId": "MKM-001",
                        "BookingAccountRef": "ACC-MKM-GBP",
                    },
                    {
                        "CounterpartyRole": "Party2",
                        "PartyRef": party_id,
                        "ExternalPartyId": lei,
                        "BookingAccountRef": f"ACC-{party_id}-GBP",
                    },
                ],
                "AncillaryParties": [],
                "_platform": {
                    "ShortName": short_name,
                    "PartyType": ctpy_type,
                    "LEI": lei,
                    "SWIFT_BIC": swift_bic,
                    "Jurisdiction": "UK",
                    "Status": "Active",
                    "CatchmentID": config.catchment_id,
                    "CreditRating": random.choice(rating_pool),
                    "RatingAgency": random.choice(_RATING_AGENCIES),
                    "CreditLimit": credit_limit,
                    "CurrentExposure": current_exposure,
                    "CollateralPosted": round(random.uniform(0, credit_limit * 0.1), 2),
                    "MaxTenor": random.choice([5, 10, 15, 20, 30]),
                    "MaxNotional": random.choice([10, 25, 50, 100]) * 1_000_000,
                    "ISDAMasterAgreement": True,
                    "CSAAgreement": has_csa,
                    "NettingAgreement": True if ctpy_type in ("Bank", "Insurer", "Reinsurer") else random.choice([True, False]),
                    "PreferredCurrency": config.CURRENCY,
                },
            }
        }
