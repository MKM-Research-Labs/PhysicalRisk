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

"""
Counterparty portfolio generator.

Generates synthetic counterparty data following the CounterpartyCDM schema.
Counterparties represent trading partners for PRS instruments.

Trading rules
-------------
* **Gauge PRS** trades are between the trader (MKM Research Labs) and an
  *external* counterparty drawn from ``_ALL_COUNTERPARTIES`` (banks,
  insurers, reinsurers, etc.) with random ``CTPY-{8hex}`` IDs.
* **Property PRS** trades are between the trader and the **REIT client
  exclusively** — a fixed counterparty ``CTPY-REIT-001`` ("Thames
  Property REIT") that is *always* emitted by the generator regardless
  of the random external set.

This module therefore prepends a deterministic REIT entry before
generating the random external pool, so ``counterparty.json`` always
contains the counterpart that ``book_property.py`` references.
"""

import json
import logging
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config import config
from port.cdm.ctpy import CounterpartyCDM

logger = logging.getLogger(__name__)

# Realistic UK financial institution names for counterparties
_BANK_NAMES = [
    ("Barclays Flood Risk Trading", "Barclays FRT", "Bank"),
    ("HSBC Environmental Markets", "HSBC Enviro", "Bank"),
    ("Lloyds Climate Solutions", "Lloyds CS", "Bank"),
    ("NatWest Natural Capital", "NatWest NC", "Bank"),
    ("Standard Chartered Cat Risk", "StanChart CR", "Bank"),
]

_INSURER_NAMES = [
    ("Aviva Climate Risk", "Aviva CR", "Insurer"),
    ("Legal & General Flood Re", "L&G Flood", "Insurer"),
    ("Zurich Environmental Risk", "Zurich ER", "Insurer"),
    ("AXA Nat Cat Desk", "AXA NatCat", "Insurer"),
    ("Hiscox Flood Markets", "Hiscox FM", "Insurer"),
]

_REINSURER_NAMES = [
    ("Swiss Re Cat Bonds", "Swiss Re CB", "Reinsurer"),
    ("Munich Re Flood ILS", "Munich Re ILS", "Reinsurer"),
    ("Hannover Re Climate", "Hannover Clim", "Reinsurer"),
]

_OTHER_NAMES = [
    ("Thames Water Utilities", "Thames Water", "Utility"),
    ("Environment Agency Trading", "EA Trading", "Government Agency"),
    ("Flood Re Ltd", "Flood Re", "Insurer"),
    ("Citadel Climate Strategies", "Citadel CS", "Hedge Fund"),
    ("BlueCrest Nat Cat Fund", "BlueCrest NC", "Hedge Fund"),
    ("USS Pension Climate", "USS Climate", "Pension Fund"),
    ("Local Government Pension", "LGPS Climate", "Pension Fund"),
    ("Surrey County Council", "Surrey CC", "Local Authority"),
]

_ALL_COUNTERPARTIES = _BANK_NAMES + _INSURER_NAMES + _REINSURER_NAMES + _OTHER_NAMES

_RATINGS = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"]
_RATING_AGENCIES = ["S&P", "Moody's", "Fitch"]

# City of London and Canary Wharf addresses
_ADDRESSES = [
    ("1 Churchill Place", "Canary Wharf", "E14 5HP"),
    ("8 Canada Square", "Canary Wharf", "E14 5HQ"),
    ("25 Canada Square", "Canary Wharf", "E14 5LB"),
    ("10 Upper Bank Street", "Canary Wharf", "E14 5JJ"),
    ("40 Bank Street", "Canary Wharf", "E14 5NR"),
    ("25 Cabot Square", "Canary Wharf", "E14 4QA"),
    ("1 Poultry", "City of London", "EC2R 8EJ"),
    ("25 Ropemaker Street", "City of London", "EC2Y 9LY"),
    ("100 Bishopsgate", "City of London", "EC2N 4AG"),
    ("20 Moorgate", "City of London", "EC2R 6DA"),
    ("60 Threadneedle Street", "City of London", "EC2R 8HP"),
    ("1 Bartholomew Lane", "City of London", "EC2N 2AX"),
    ("51 Lime Street", "City of London", "EC3M 7DQ"),
    ("30 St Mary Axe", "City of London", "EC3A 8BF"),
    ("22 Bishopsgate", "City of London", "EC2N 4BQ"),
    ("1 Undershaft", "City of London", "EC3P 3DQ"),
    ("Willis Building, 51 Lime Street", "City of London", "EC3M 7DQ"),
    ("Leadenhall Building, 122 Leadenhall Street", "City of London", "EC3V 4AB"),
    ("One New Change", "City of London", "EC4M 9AF"),
    ("55 Gracechurch Street", "City of London", "EC3V 0EE"),
    ("71 Lombard Street", "City of London", "EC3P 3BS"),
]

_CONTACTS = [
    ("James", "Richardson", "Head of Trading"),
    ("Sarah", "Chen", "Senior Trader"),
    ("Michael", "Okonkwo", "Portfolio Manager"),
    ("Emma", "Thompson", "Director, Climate Risk"),
    ("David", "Patel", "VP Structured Products"),
    ("Rebecca", "Walsh", "Head of Cat Risk"),
    ("Andrew", "Kim", "Senior Analyst"),
    ("Laura", "Martinez", "Managing Director"),
    ("Thomas", "Wright", "Head of ILS"),
    ("Hannah", "Burke", "Director, Nat Cat"),
    ("Robert", "Singh", "VP Credit Trading"),
    ("Catherine", "Moore", "Head of Derivatives"),
    ("William", "Scott", "Senior Portfolio Manager"),
    ("Jennifer", "Blake", "Director, ESG Trading"),
    ("Christopher", "Adams", "Head of Risk Transfer"),
    ("Olivia", "Turner", "VP Environmental Markets"),
    ("Daniel", "Cooper", "Senior Structurer"),
    ("Sophie", "Evans", "Head of Pricing"),
    ("Matthew", "Lee", "Director, Flood Risk"),
    ("Emily", "Foster", "VP Cat Bonds"),
]

# Sort codes for major clearing banks
_SORT_CODES = [
    "20-00-00", "20-32-53", "30-94-28", "40-05-15", "60-01-73",
    "15-10-00", "23-05-80", "30-12-18", "40-47-34", "56-00-49",
]


class CounterpartyPortfolioGenerator:
    """Generates a portfolio of synthetic counterparties for PRS trading."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None, verbose: bool = True):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cdm = CounterpartyCDM()
        self.verbose = verbose

    def generate(self, count: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate counterparty portfolio.

        Args:
            count: Number of counterparties (defaults to all predefined names)

        Returns:
            Dict with 'data', 'file_path', and 'metadata'
        """
        if count is None:
            names = _ALL_COUNTERPARTIES
        else:
            names = _ALL_COUNTERPARTIES[:count]

        # Always emit the fixed REIT counterparty first.  Property PRS
        # trades are exclusively between the trader and CTPY-REIT-001
        # (see book_property.py); the lineage / blotter tests assert
        # that every PRS counterparty exists in counterparty.json, so
        # this entry must always be present.
        counterparties = [self._generate_reit()]
        if self.verbose:
            logger.info(
                "[REIT] Thames Property REIT (CTPY-REIT-001)"
            )

        for i, (full_name, short_name, ctpy_type) in enumerate(names):
            ctpy = self._generate_one(i, full_name, short_name, ctpy_type)
            counterparties.append(ctpy)
            if self.verbose:
                party_id = ctpy["CounterpartySet"]["Party"]["PartyID"]
                logger.info("[%d/%d] %s (%s)", i+1, len(names), short_name, party_id)

        output_path = self.output_dir / "counterparty.json"
        output_data = {
            "counterparties": counterparties,
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "v1.0",
                "catchment": config.catchment_id,
                "total_generated": len(counterparties),
            }
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        if self.verbose:
            logger.info("Wrote %d counterparties to %s", len(counterparties), output_path)

        return {
            "data": counterparties,
            "file_path": output_path,
            "metadata": output_data["generation_metadata"],
        }

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
                            "AccountDescription": f"GBP trading/settlement - {short_name}",
                            "AccountCurrency": "GBP",
                            "SortCode": sort_code,
                            "AccountNumber": account_number,
                            "IBAN": iban,
                            "BIC": swift_bic,
                        },
                        {
                            "AccountID": f"ACC-{party_id}-COLL",
                            "AccountDescription": f"Collateral account - {short_name}",
                            "AccountCurrency": "GBP",
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
                    "PreferredCurrency": "GBP",
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
                            "AccountDescription": f"GBP trading/settlement - {short_name}",
                            "AccountCurrency": "GBP",
                            "SortCode": sort_code,
                            "AccountNumber": account_number,
                            "IBAN": iban,
                            "BIC": swift_bic,
                        },
                        {
                            "AccountID": f"ACC-{party_id}-COLL",
                            "AccountDescription": f"Collateral account - {short_name}",
                            "AccountCurrency": "GBP",
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
                    "PreferredCurrency": "GBP",
                },
            }
        }


def generate_counterparties(output_dir=None, count=None, verbose=True):
    """Convenience function."""
    gen = CounterpartyPortfolioGenerator(output_dir=output_dir, verbose=verbose)
    return gen.generate(count)
