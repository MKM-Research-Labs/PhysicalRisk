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

"""Synthetic CreditSupport block for generated counterparties.

One netting set per counterparty, derived from the existing ``_platform``
flags so the generator's random draws are untouched: ``CSAAgreement`` decides
whether variation margin is exchanged and ``NettingAgreement`` whether
close-out netting is enforceable. The terms are placeholders that make the
schema populated; real terms come from the executed CSA.
"""

from typing import Any, Dict

from config.port import NETTING_SET_PREFIX, SYNTHETIC_CSA_TERMS
from config import config

_FINANCIAL_TYPES = ("Bank", "Insurer", "Reinsurer")


def netting_set_id(party_id: str) -> str:
    """Return the netting set identifier for a counterparty."""
    return f"{NETTING_SET_PREFIX}{party_id}"


def with_credit_support(record: Dict[str, Any]) -> Dict[str, Any]:
    """Attach ``CreditSupport`` to a generated counterparty record and return it."""
    root = record["CounterpartySet"]
    platform = root["_platform"]
    has_csa = bool(platform.get("CSAAgreement"))
    kind = "financial" if platform.get("PartyType") in _FINANCIAL_TYPES else "corporate"
    netting_set = {
        "NettingSetID": netting_set_id(root["Party"]["PartyID"]),
        "MasterAgreement": "ISDA2002" if platform.get("ISDAMasterAgreement") else "None",
        "CloseOutNetting": bool(platform.get("NettingAgreement")),
        "CsaType": "VM" if has_csa else "None",
        "CollateralCurrency": config.CURRENCY,
        "InitialMarginReceived": 0.0,
        "InitialMarginPosted": 0.0,
    }
    if has_csa:
        netting_set.update(SYNTHETIC_CSA_TERMS[kind])
    root["CreditSupport"] = {"NettingSets": [netting_set]}
    return record
