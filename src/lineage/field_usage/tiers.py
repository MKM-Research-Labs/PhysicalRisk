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

from config.theme import colour
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

"""Usage tiers for CDM field downstream lineage.

A field is classified by how far downstream its value travels:

    RED    — feeds the PRS pricing (directly, or via a peril damage function
             whose loss drives the PRS spread). Highest scrutiny.
    AMBER  — contract / operational detail: used by the platform (loan terms,
             transaction history, counterparty accounts) but not in the PRS.
    GREEN  — descriptive: only appears in the property/asset report.

GREEN is the default for any field not explicitly classified.
"""

RED = "RED"
AMBER = "AMBER"
GREEN = "GREEN"

DEFAULT_TIER = GREEN

# Display metadata for the legend and the lineage popup. Colours match the
# CDM Asset Review palette (RED #d32f2f, AMBER #f57c00, GREEN #388e3c).
TIER_META = {
    RED: {
        "label": "Feeds PRS pricing",
        "colour": colour('red'),
        "description": "Feeds the PRS spread — directly or via a peril damage function.",
    },
    AMBER: {
        "label": "Contract / operational",
        "colour": colour('amber'),
        "description": "Used operationally (contract, loan, transaction, counterparty) — not in the PRS.",
    },
    GREEN: {
        "label": "Report only",
        "colour": colour('green'),
        "description": "Descriptive field — used only in the property/asset report.",
    },
}
