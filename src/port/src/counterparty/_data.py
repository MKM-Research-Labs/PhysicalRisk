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

"""Static reference data for counterparty generation."""

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

