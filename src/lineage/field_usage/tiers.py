# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

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
        "colour": "#d32f2f",
        "description": "Feeds the PRS spread — directly or via a peril damage function.",
    },
    AMBER: {
        "label": "Contract / operational",
        "colour": "#f57c00",
        "description": "Used operationally (contract, loan, transaction, counterparty) — not in the PRS.",
    },
    GREEN: {
        "label": "Report only",
        "colour": "#388e3c",
        "description": "Descriptive field — used only in the property/asset report.",
    },
}
