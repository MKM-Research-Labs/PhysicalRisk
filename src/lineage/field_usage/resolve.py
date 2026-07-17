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

"""Field-usage resolution — the public API of the field_usage package.

Given a CDM dotted path (from the record root, e.g.
``ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIWindScore``) return
its downstream-usage tier and lineage:

    classify(path) -> "RED" | "AMBER" | "GREEN"
    lineage(path)  -> {tier, summary, consumers, chain}
    tier_meta()    -> the RED/AMBER/GREEN legend metadata

Resolution order: exact RED entry, then AMBER prefix rule, else GREEN default.
"""

from .registry import AMBER_PREFIXES, EXACT_FIELDS
from .tiers import DEFAULT_TIER, GREEN, TIER_META


def _green_entry(path):
    return {
        "tier": GREEN,
        "summary": "Descriptive field — surfaced in the property/asset report only; "
                   "not used by a model or the PRS.",
        "consumers": ["Asset report"],
        "chain": [
            {"node": (path.rsplit(".", 1)[-1] or path) + " (CDM)", "kind": "field"},
            {"node": "Asset report", "kind": "output"},
        ],
    }


def _amber_match(path):
    for prefix, entry in AMBER_PREFIXES:
        if path == prefix or path.startswith(prefix + "."):
            return entry
    return None


def lineage(path):
    """Full usage entry for a CDM dotted path (never None — GREEN by default)."""
    if path in EXACT_FIELDS:
        return EXACT_FIELDS[path]
    amber = _amber_match(path)
    if amber is not None:
        return amber
    return _green_entry(path)


def classify(path):
    """The usage tier for a CDM dotted path: RED, AMBER or GREEN."""
    if path in EXACT_FIELDS:
        return EXACT_FIELDS[path]["tier"]
    amber = _amber_match(path)
    if amber is not None:
        return amber["tier"]
    return DEFAULT_TIER


def tier_meta():
    """The RED/AMBER/GREEN legend metadata (label, colour, description)."""
    return TIER_META
