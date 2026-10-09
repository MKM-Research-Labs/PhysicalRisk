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

"""Validation of the optional CounterpartySet.CreditSupport block.

The block is optional so that counterparty files written before it existed
still validate. When present, every netting set must be identifiable, use the
menu values the schema lists, and carry non-negative amounts.
"""

from typing import List

from ._schema import COUNTERPARTY_SCHEMA

_ITEMS = COUNTERPARTY_SCHEMA["CounterpartySet"]["CreditSupport"]["NettingSets"]["items"]
_MENUS = {name: spec["options"] for name, spec in _ITEMS.items() if spec["type"] == "menu"}
_AMOUNTS = ("Threshold", "MinimumTransferAmount", "MarginPeriodOfRiskDays",
            "InitialMarginReceived", "InitialMarginPosted")


def credit_support_errors(root: dict) -> List[str]:
    """Return validation errors for ``root['CreditSupport']``; empty if absent."""
    support = root.get("CreditSupport")
    if support is None:
        return []
    errors: List[str] = []
    seen = set()
    for idx, ns in enumerate(support.get("NettingSets", []) or []):
        ns_id = ns.get("NettingSetID")
        if not ns_id:
            errors.append(f"NettingSets[{idx}]: Missing NettingSetID")
        elif ns_id in seen:
            errors.append(f"NettingSets[{idx}]: Duplicate NettingSetID '{ns_id}'")
        seen.add(ns_id)
        for field, options in _MENUS.items():
            if field in ns and ns[field] not in options:
                errors.append(f"NettingSets[{idx}]: Invalid {field} '{ns[field]}'")
        if "CloseOutNetting" in ns and not isinstance(ns["CloseOutNetting"], bool):
            errors.append(f"NettingSets[{idx}]: CloseOutNetting must be true or false")
        for field in _AMOUNTS:
            value = ns.get(field)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                errors.append(f"NettingSets[{idx}]: {field} must be a non-negative number")
    return errors
