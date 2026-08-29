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

"""Model-governance ramps — the table PhysicalRisk and MKM-ModelRisk both draw from.

ModelRisk's ``STATUS_COLOUR_TOKENS`` lives here, name for name and value for value. The
two products were one codebase and are meant to sit in one suite, so a governance badge
should mean the same thing and look the same in both: an "Amber" RAG rating, a rejected
MRC submission, a partially-addressed validation question.

Several of these ramps have no consumer in PhysicalRisk today. They are carried anyway,
so that a governance surface added later reaches for the shared table instead of
inventing a parallel one, and so that an adopter's theme file written against either
product covers both.

The ramps specific to this platform — trigger levels, lineage freshness, storm sequence
types — are in :mod:`config.theme._badges`.
"""

# --- Model governance. --------------------------------------------------------------
# ModelRisk's name for this ramp, and its five levels. Materiality descends red → amber
# → blue → green → grey: level 1 is the most material model, not the best one. The
# PhysicalRisk inventory only uses 1–4 and its UI labels them "Tier 1 — Maximum"…
# "Tier 4 — Minimal"; level 5 is carried so one table serves both products.
MISSION_CRITICALITY_TOKENS = {
    "1": "red",
    "2": "amber",
    "3": "accent",
    "4": "green",
    "5": "grey",
}

# The union of both products' lifecycle vocabularies. PhysicalRisk's inventory says
# Production/Development/Validation/Retired; ModelRisk's says New/Being Enhanced/No New
# Development/Marked for Removal. They are the same concept enumerated differently, and
# a ramp is a lookup — carrying both key sets costs nothing and means neither product
# needs a table of its own.
LIFECYCLE_TOKENS = {
    "Production": "green",
    "Development": "accent",
    "Validation": "amber",
    "Retired": "grey",
    "New": "accent",
    "Being Enhanced": "amber",
    "No New Development": "grey",
    "Marked for Removal": "red",
}

RAG_TOKENS = {
    "Green": "green",
    "Amber": "amber",
    "Red": "red",
    "Not Rated": "grey",
}

VALIDATION_QUESTION_TOKENS = {
    "Addressed": "green",
    "Partially Addressed": "amber",
    "Not Addressed": "red",
    "Not Applicable": "grey",
}

# --- ModelRisk's remaining ramps, carried across so the two products share one table.
# Nothing in PhysicalRisk draws these yet; they are here so a governance surface added
# later reaches for them rather than inventing a parallel set, and so an adopter theme
# file written against either product covers both.
MEETING_STATUS_TOKENS = {
    "Scheduled": "accent",
    "In Progress": "amber",
    "Held": "green",
    "Cancelled": "grey",
}

MRC_STATE_TOKENS = {
    "Pending": "amber",
    "Rejected": "red",
    "Revoked": "red",
    "Re-classify": "amber",
    "Rating moved": "amber",
    "Not placed": "grey",
    "Approved": "green",
}

PRODUCT_STATUS_TOKENS = {
    "Active": "green",
    "Proposed": "info",
    "Suspended": "amber",
    "Retired": "grey",
}

REVIEW_THREAD_TOKENS = {
    "open": "violet",
    "answered": "blue-grey",
}

ATTENTION_TOKENS = {
    "escalate": "red",
    "act": "amber",
    "monitor": "accent",
    "clear": "green",
}

#: Per-ramp fallback, ModelRisk's shape: the token a badge takes when the value is not
#: in its ramp. A ramp absent from here has no default, and an unrecognised value on it
#: is a programming error rather than missing data.
GOVERNANCE_COLOUR_DEFAULTS = {
    "validation_question": "grey",
    "mrc_state": "grey",
    "lifecycle": "grey",
    "product_status": "grey",
    "mission_criticality": "grey",
    "rag": "grey",
}

GOVERNANCE_TOKEN_RAMPS = {
    "rag": RAG_TOKENS,
    "mission_criticality": MISSION_CRITICALITY_TOKENS,
    "meeting_status": MEETING_STATUS_TOKENS,
    "validation_question": VALIDATION_QUESTION_TOKENS,
    "mrc_state": MRC_STATE_TOKENS,
    "lifecycle": LIFECYCLE_TOKENS,
    "product_status": PRODUCT_STATUS_TOKENS,
    "review_thread": REVIEW_THREAD_TOKENS,
    "attention": ATTENTION_TOKENS,
}

__all__ = [
    "MISSION_CRITICALITY_TOKENS",
    "LIFECYCLE_TOKENS",
    "RAG_TOKENS",
    "VALIDATION_QUESTION_TOKENS",
    "MEETING_STATUS_TOKENS",
    "MRC_STATE_TOKENS",
    "PRODUCT_STATUS_TOKENS",
    "REVIEW_THREAD_TOKENS",
    "ATTENTION_TOKENS",
    "GOVERNANCE_TOKEN_RAMPS", "GOVERNANCE_COLOUR_DEFAULTS",
]
