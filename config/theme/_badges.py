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

"""Console workflow states → tokens: the badges the front end draws.

The ramps shared with MKM-ModelRisk — RAG, lifecycle, mission criticality, the
MRC states — live in :mod:`config.theme._governance`. What is left here is what
this platform alone draws: trigger levels, lineage state, storm sequence types.

:mod:`config.theme._status` holds the ramps for the *modelled* world — a flood band, a
gauge's condition, an LTV bucket. This holds the ramps for the *application's* own
states: a model's governance tier, a review that is overdue, a validation question that
is only partially addressed, a lineage step that has gone stale. The two are separated
because they answer to different people. A hydrologist owns the first; the model risk
function owns the second.

These were 23 object literals scattered across ``src/static/js`` before this module,
and they did not agree. The trigger-level ramp alone existed five times in four
different spellings — see :data:`TRIGGER_LEVEL_TOKENS`. Collapsing them is the point of
step 3 of docs/refactor/theme_centralisation_plan.md and it is the one step in the
migration that deliberately changes what is on screen.

Every ramp maps a value to a token name, the same contract as ``_status.py``. The
browser reads them through ``window.__THEME_STATUS`` and ``Theme.status()``; Python
reads them directly.
"""

# --- Trigger levels. The ramp that existed five times in four spellings. ----------
#
#   ghc_historical.js      alert #ffc107  warning #ff9800  severe #f44336
#   curve_history.js       alert #f9a825  warning #e65100  severe #c62828
#   market/render.js  fg   alert #fbc02d  warning #f57c00  severe #d32f2f
#   market/render.js  dark alert #f9a825  warning #e65100  severe #b71c1c
#   sp_table_basis.js      alert #1976d2  warning #f57c00  severe #d32f2f
#
# The canon below is ``market/render.js``, which was the only site carrying both a
# foreground and an emphasis form, plus the background trio from ``curve_history.js``.
# Nothing is invented: all nine were already in the codebase, and all nine were already
# tokens. Two consequences are visible on screen and are intended —
# ``ghc_historical``'s trio deepens slightly, and ``sp_table_basis`` stops drawing
# "alert" in the accent blue, which made the same word mean caution on one screen and
# information on another.
TRIGGER_LEVEL_TOKENS = {
    "alert": "gold-bright",
    "warning": "amber",
    "severe": "red",
    # The storm basis table alone carries a fourth, milder level.
    "clean": "muted",
}

#: The emphasis form — a darker shade of the same level, for a border or a heading
#: sitting on the foreground colour.
TRIGGER_LEVEL_DARK_TOKENS = {
    "alert": "gold-deep",
    "warning": "amber-deep",
    "severe": "red-deep",
    "clean": "text-3",
}

#: The chart form — the brighter Material 500 tones the trigger lines and legends are
#: drawn in (``ghc_hazard``, ``ghc_return``, ``gsa_distribution``, ``phc_basis_gauge``,
#: ``psa_timeline``). Deliberately not the same as the badge form above: a 1px stroke
#: on a white chart needs more saturation to read, where the same colour behind 9px
#: bold text on a chip does not have the contrast for it. Those sites are single
#: literals rather than maps, so they convert in step 6 — this exists now so that step
#: has a target instead of inventing a fourth spelling of the ramp.
TRIGGER_LEVEL_CHART_TOKENS = {
    "alert": "amber-yellow",
    "warning": "amber-bright",
    "severe": "red-bright",
    "clean": "muted-2",
}

#: The tint form, for a chip or a banner background.
TRIGGER_LEVEL_BG_TOKENS = {
    "alert": "warn-bg",
    "warning": "warn-bg-warm",
    "severe": "danger-bg-soft",
    "clean": "sunken",
}


REVIEW_STATUS_TOKENS = {
    "Overdue": "red",
    "Due Soon": "amber",
    "Upcoming": "gold-bright",
    "On Track": "green",
    "Not Scheduled": "grey",
}


# --- Remediation and validation. ----------------------------------------------------
PRIORITY_TOKENS = {
    "High": "red",
    "Medium": "amber",
    "Low": "accent",
}

TASK_STATUS_TOKENS = {
    "Open": "amber-deep",
    "In Progress": "accent",
    "Closed": "green",
}

#: Was ``rrColors`` in mg_inventory.js and ``riskRatingColors`` in risk_rating.js —
#: two byte-identical copies, now one.
RISK_RATING_TOKENS = {
    "Acceptable": "green",
    "Conditional": "amber",
    "Unacceptable": "red",
    "Not Rated": "grey",
}


# --- Data lineage. ------------------------------------------------------------------
# These draw the *bright* green/amber/red rather than the governance mid tones. That is
# preserved: a lineage badge sits on a dark panel where the mid tones read as muddy,
# and unifying them is a design decision rather than a migration one.
LINEAGE_FRESHNESS_TOKENS = {
    "fresh": "green-bright",
    "stale": "amber-bright",
    "missing": "red-bright",
}

#: The tint form of the freshness ramp — a lineage step's row background sits behind
#: its badge. Was a second ternary alongside the first in ``mg_lineage.js``, spelling
#: the same three states in background tones.
LINEAGE_FRESHNESS_BG_TOKENS = {
    "fresh": "ok-bg",
    "stale": "warn-bg-warm",
    "missing": "danger-bg-soft",
}

LINEAGE_HEALTH_TOKENS = {
    "healthy": "green-bright",
    "degraded": "amber-bright",
    "unhealthy": "red-bright",
}

LINEAGE_ROLE_TOKENS = {
    "origin": "accent-mid",
    "derived": "green-dark",
    "consumed": "amber-deep",
    "found": "grey-dark",
}

# --- Categorical ramps. The key a caller uses is the bare name; the token carries a
# prefix so it cannot collide in the flat custom-property namespace.
DATASET_TOKENS = {
    "gauges": "dataset-gauges",
    "properties": "dataset-properties",
    "mortgages": "dataset-mortgages",
    "gaugehd": "dataset-gaugehd",
    "stressm": "dataset-stressm",
    "hazard": "dataset-hazard",
    "propertyts": "dataset-propertyts",
    "propertyhc": "dataset-propertyhc",
    "counterparties": "dataset-counterparties",
    "blotter": "dataset-blotter",
}

SEQUENCE_TOKENS = {
    "isolated": "sequence-isolated",
    "doublet": "sequence-doublet",
    "cluster": "sequence-cluster",
    "persistent": "sequence-persistent",
}

#: The chip form of a sequence type: a tint behind, an ink on top. Separate ramps
#: rather than one nested map, so every ramp in this package has the same flat shape
#: and the audit can check them all the same way.
SEQUENCE_BG_TOKENS = {
    "isolated": "accent-soft",
    "doublet": "warn-bg-warm",
    "cluster": "pink-bg",
    "persistent": "purple-bg",
}

SEQUENCE_INK_TOKENS = {
    "isolated": "accent-mid",
    "doublet": "amber-deep",
    "cluster": "red-dark",
    "persistent": "purple-deep",
}

#: Report formats in the audit browser. A format is an identity, not a rating.
REPORT_FORMAT_TOKENS = {
    "PDF": "red-dark",
    "XML": "purple-deep",
    "HTML": "info",
    "JSON": "amber-deep",
    "LaTeX": "green-dark",
    "Log": "text-2",
}


#: Per-ramp fallback token, the same shape ModelRisk uses. One shared answer per ramp,
#: so an unrecognised state looks the same everywhere instead of grey on one screen
#: and blue on the next.
BADGE_COLOUR_DEFAULTS = {
    "trigger_level": "muted",
    "trigger_level_dark": "text-3",
    "trigger_level_bg": "sunken",
    "trigger_level_chart": "muted-2",
    "review_status": "grey",
    "priority": "grey",
    "task_status": "grey",
    "risk_rating": "grey",
    "lineage_freshness": "muted-2",
    "lineage_freshness_bg": "sunken",
    "lineage_health": "muted-2",
    "lineage_role": "grey",
    "dataset": "muted-2",
    "sequence": "accent-light",
    "sequence_bg": "sunken",
    "sequence_ink": "text-2",
    "report_format": "text-2",
}

# Every console badge ramp, for the emitter and the audit.
BADGE_TOKEN_RAMPS = {
    "trigger_level": TRIGGER_LEVEL_TOKENS,
    "trigger_level_dark": TRIGGER_LEVEL_DARK_TOKENS,
    "trigger_level_bg": TRIGGER_LEVEL_BG_TOKENS,
    "trigger_level_chart": TRIGGER_LEVEL_CHART_TOKENS,
    "review_status": REVIEW_STATUS_TOKENS,
    "priority": PRIORITY_TOKENS,
    "task_status": TASK_STATUS_TOKENS,
    "risk_rating": RISK_RATING_TOKENS,
    "lineage_freshness": LINEAGE_FRESHNESS_TOKENS,
    "lineage_freshness_bg": LINEAGE_FRESHNESS_BG_TOKENS,
    "lineage_health": LINEAGE_HEALTH_TOKENS,
    "lineage_role": LINEAGE_ROLE_TOKENS,
    "dataset": DATASET_TOKENS,
    "sequence": SEQUENCE_TOKENS,
    "sequence_bg": SEQUENCE_BG_TOKENS,
    "sequence_ink": SEQUENCE_INK_TOKENS,
    "report_format": REPORT_FORMAT_TOKENS,
}

__all__ = [
    "TRIGGER_LEVEL_TOKENS", "TRIGGER_LEVEL_DARK_TOKENS", "TRIGGER_LEVEL_BG_TOKENS",
    "TRIGGER_LEVEL_CHART_TOKENS",
    "MISSION_CRITICALITY_TOKENS", "REVIEW_STATUS_TOKENS", "LIFECYCLE_TOKENS",
    "MEETING_STATUS_TOKENS", "MRC_STATE_TOKENS", "PRODUCT_STATUS_TOKENS",
    "REVIEW_THREAD_TOKENS", "ATTENTION_TOKENS",
    "RAG_TOKENS", "PRIORITY_TOKENS", "TASK_STATUS_TOKENS",
    "RISK_RATING_TOKENS", "VALIDATION_QUESTION_TOKENS", "LINEAGE_FRESHNESS_TOKENS", "LINEAGE_FRESHNESS_BG_TOKENS",
    "LINEAGE_HEALTH_TOKENS", "LINEAGE_ROLE_TOKENS", "DATASET_TOKENS",
    "SEQUENCE_TOKENS", "SEQUENCE_BG_TOKENS", "SEQUENCE_INK_TOKENS",
    "REPORT_FORMAT_TOKENS", "BADGE_TOKEN_RAMPS",
    "BADGE_COLOUR_DEFAULTS",
]
