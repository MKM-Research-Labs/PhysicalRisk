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

"""Validation of the optional CounterpartySet.Credit block (MKM-XV-001).

Optional, so counterparty files written before it existed still validate.
When present, the spreads must be positive and in increasing tenor order
(the XVA model bootstraps a hazard curve from them), the recovery must be a
fraction, and the source must be one the schema lists.
"""

from typing import List

from ._schema import COUNTERPARTY_SCHEMA

_SOURCES = COUNTERPARTY_SCHEMA["CounterpartySet"]["Credit"]["Source"]["options"]


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def credit_errors(root: dict) -> List[str]:
    """Return validation errors for ``root['Credit']``; empty if absent."""
    credit = root.get("Credit")
    if credit is None:
        return []
    errors: List[str] = []
    points = credit.get("CdsSpreads") or []
    if not points:
        errors.append("CdsSpreads: at least one tenor is required")
    tenors = []
    for idx, point in enumerate(points):
        tenor, spread = point.get("TenorYears"), point.get("SpreadBps")
        if not _number(tenor) or tenor <= 0:
            errors.append(f"CdsSpreads[{idx}]: TenorYears must be a positive number")
        else:
            tenors.append(tenor)
        if not _number(spread) or spread <= 0:
            errors.append(f"CdsSpreads[{idx}]: SpreadBps must be a positive number")
    if tenors != sorted(set(tenors)):
        errors.append("CdsSpreads: tenors must be strictly increasing")
    recovery = credit.get("Recovery")
    if recovery is not None and (not _number(recovery) or not 0 <= recovery < 1):
        errors.append("Recovery must be a number in [0, 1)")
    if "Source" in credit and credit["Source"] not in _SOURCES:
        errors.append(f"Invalid Source '{credit['Source']}'")
    return errors
