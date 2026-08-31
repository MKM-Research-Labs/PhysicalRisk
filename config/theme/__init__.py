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

"""Design tokens — every visual parameter the platform draws with (coding rule R7).

Colours, type sizes, spacing steps, corner radii and shadows are named here and
nowhere else. ``src/visual/theme_css.py`` serialises them into the ``:root`` block
and the ``window.__THEME`` object injected at the top of every console page; the
stylesheets and the panel scripts then refer to tokens rather than to values. An
adopting institution rebrands by changing this package, not by editing the front end.

Layout::

    _palette.py   BRAND, SURFACE, TEXT, RAG, STATE, HUE   — the chrome
    _scale.py     TYPE, SPACE, RADIUS, SHADOW             — the non-colour parameters
    _domain.py    PERIL, DEPTH, MAP, MARKER, FLOOD, …     — physical-risk vocabulary
    _status.py    the value→token ramps and their bounds   — what a colour *means*
    _badges.py    this platform's own workflow-state ramps — triggers, lineage
    _governance.py the ramps shared with MKM-ModelRisk    — RAG, MRC, lifecycle
    registry.py   THEME, THEME_GROUPS                     — the flat view emitters use

See docs/refactor/theme_centralisation_plan.md for the migration this package is
step 1 of, and docs/rules/coding_rules.md R7 for the rule it exists to satisfy.
"""

from ._badges import (
    BADGE_COLOUR_DEFAULTS, BADGE_TOKEN_RAMPS, DATASET_TOKENS,
    LINEAGE_FRESHNESS_BG_TOKENS, LINEAGE_FRESHNESS_TOKENS,
    LINEAGE_HEALTH_TOKENS, LINEAGE_ROLE_TOKENS,
    PRIORITY_TOKENS, REPORT_FORMAT_TOKENS, REVIEW_STATUS_TOKENS, RISK_RATING_TOKENS,
    SEQUENCE_BG_TOKENS, SEQUENCE_INK_TOKENS, SEQUENCE_TOKENS, TASK_STATUS_TOKENS,
    TRIGGER_LEVEL_BG_TOKENS, TRIGGER_LEVEL_CHART_FILL_TOKENS,
    TRIGGER_LEVEL_CHART_TOKENS, TRIGGER_LEVEL_CHART_WASH_TOKENS,
    TRIGGER_LEVEL_DARK_TOKENS,
    TRIGGER_LEVEL_TOKENS,
)
from ._governance import (
    ATTENTION_TOKENS, GOVERNANCE_COLOUR_DEFAULTS, GOVERNANCE_TOKEN_RAMPS,
    LIFECYCLE_TOKENS, MEETING_STATUS_TOKENS, MISSION_CRITICALITY_TOKENS,
    MRC_STATE_TOKENS, PRODUCT_STATUS_TOKENS, RAG_TOKENS, REVIEW_THREAD_TOKENS,
    VALIDATION_QUESTION_TOKENS,
)
from ._domain import (
    CHART, DATASET, DEPTH, FLOOD, GROUND, LOG, MAP, MARKER, PERIL, SEQUENCE,
    SERIES, SIGN,
)
from ._palette import BRAND, DARK, HUE, RAG, STATE, SURFACE, TEXT
from ._review import REVIEW
from ._scale import GRAPH, RADIUS, SHADOW, SPACE, TYPE
from ._status import (
    DEPTH_BAND_BOUNDS_M, DEPTH_BAND_TOKENS, DEPTH_BAND_TOP, FLOOD_RISK_MARKERS,
    FLOOD_RISK_TOKENS, LOAN_RISK_TOKENS, LTV_BAND_BOUNDS, LTV_BAND_TOKENS,
    LTV_BAND_TOP, OPERATIONAL_STATUS_TOKENS, PROPERTY_TYPE_TOKENS,
    STATUS_TOKEN_RAMPS, STORM_INTENSITY_BOUNDS_MS, STORM_INTENSITY_TOKENS,
    STORM_INTENSITY_TOP,
)
from .registry import (
    SANCTIONED_PACKAGE, STATUS_COLOUR_DEFAULTS, STATUS_COLOUR_TOKENS, THEME,
    THEME_GROUPS,
)

__all__ = [
    "BRAND", "SURFACE", "TEXT", "RAG", "STATE", "HUE", "DARK",
    "TYPE", "SPACE", "RADIUS", "SHADOW", "GRAPH", "REVIEW",
    "PERIL", "DEPTH", "MAP", "MARKER", "FLOOD", "SIGN", "SERIES", "DATASET",
    "SEQUENCE", "CHART", "LOG", "GROUND",
    "TRIGGER_LEVEL_TOKENS", "TRIGGER_LEVEL_DARK_TOKENS", "TRIGGER_LEVEL_BG_TOKENS",
    "TRIGGER_LEVEL_CHART_TOKENS", "TRIGGER_LEVEL_CHART_WASH_TOKENS",
    "TRIGGER_LEVEL_CHART_FILL_TOKENS",
    "MODEL_TIER_TOKENS", "REVIEW_STATUS_TOKENS", "LIFECYCLE_TOKENS",
    "RAG_TOKENS", "PRIORITY_TOKENS", "TASK_STATUS_TOKENS",
    "RISK_RATING_TOKENS", "VALIDATION_QUESTION_TOKENS", "LINEAGE_FRESHNESS_TOKENS", "LINEAGE_FRESHNESS_BG_TOKENS",
    "LINEAGE_HEALTH_TOKENS", "LINEAGE_ROLE_TOKENS", "DATASET_TOKENS",
    "SEQUENCE_TOKENS", "BADGE_TOKEN_RAMPS",
    "BADGE_FALLBACK_TOKEN",
    "FLOOD_RISK_TOKENS", "FLOOD_RISK_MARKERS", "OPERATIONAL_STATUS_TOKENS",
    "LOAN_RISK_TOKENS", "PROPERTY_TYPE_TOKENS", "STORM_INTENSITY_TOKENS",
    "DEPTH_BAND_TOKENS", "LTV_BAND_TOKENS", "STATUS_TOKEN_RAMPS",
    "STORM_INTENSITY_BOUNDS_MS", "DEPTH_BAND_BOUNDS_M", "LTV_BAND_BOUNDS",
    "STORM_INTENSITY_TOP", "DEPTH_BAND_TOP", "LTV_BAND_TOP",
    "THEME", "THEME_GROUPS", "SANCTIONED_PACKAGE",
]
