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

"""Field-usage downstream lineage for CDM fields.

Classifies each CDM field by how far downstream its value travels — RED (feeds
PRS pricing), AMBER (contract / operational) or GREEN (report only) — and
returns the lineage chain to the consuming model / output. See resolve.py for
the public functions.
"""

from .registry import AMBER_PREFIXES, EXACT_FIELDS
from .resolve import classify, lineage, tier_meta
from .tiers import AMBER, DEFAULT_TIER, GREEN, RED, TIER_META

__all__ = [
    "classify",
    "lineage",
    "tier_meta",
    "RED",
    "AMBER",
    "GREEN",
    "DEFAULT_TIER",
    "TIER_META",
    "EXACT_FIELDS",
    "AMBER_PREFIXES",
]
