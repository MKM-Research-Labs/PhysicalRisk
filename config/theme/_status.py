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

"""Which colour a business value is drawn in — the ramps, in one place.

:mod:`config.theme._palette` and :mod:`config.theme._domain` name the hues. This says
what they *mean*: that a "Very High" flood band is drawn in ``red-deep``, that a
decommissioned gauge is ``marker-grey``, that an LTV above 95% crosses into
``marker-purple``.

Every ramp maps a value to a **token name**, never to a colour. That is the point: the
"High" flood band and a red RAG badge then move together when the palette moves, and a
rebrand cannot leave one of them behind. Resolution to a hex value happens at the edge
— ``src/visual/utils/color_schemes`` for Python, ``window.Theme`` for the browser.

Before this module the flood ramp existed four times (``ColorSchemes``,
``visual.utils.risk_assessors``, ``visual.popups.popup_builder``, and
``ColorSchemes.get_folium_color_name``) and the gauge ramp twice
(``ColorSchemes``, ``visual.popups.gauge_popup``). They agreed, by maintenance rather
than by construction, except where noted below. The JS copies are step 3 of
docs/refactor/theme_centralisation_plan.md and will read this same table.

**Folium is why some ramps are listed twice.** A Leaflet marker takes a colour *name*
from a fixed vocabulary (``green``, ``lightgreen``, ``darkred``…), not a hex value, so
the marker ramps cannot be expressed as tokens at all. They are the one place a colour
is named outside the palette, and they are kept beside the token ramp they shadow so
the two cannot drift apart unnoticed.
"""

# --- Flood risk band → token. The platform's primary ramp. ------------------------
# Both casings of "Very Low"/"Very High" are live in the data and both are kept; the
# data is not being normalised as part of a styling change.
FLOOD_RISK_TOKENS = {
    "Very Low": "green",
    "Very low": "green",
    "Low": "green-soft",
    "Medium": "amber-bright",
    "High": "red-bright",
    "Very High": "red-deep",
    "Very high": "red-deep",
    "Unknown": "accent-bright",
}

# The same ramp in Folium's marker vocabulary. ``N/A`` exists here and not above: the
# marker ramp in ``visual.utils.risk_assessors`` carried it and the hex ramp never
# did, so a property with no assessment drew a grey marker and a blue popup swatch.
# Preserved rather than fixed — this step moves no pixels — but now visible in one
# place instead of implied by the gap between two files.
FLOOD_RISK_MARKERS = {
    "Very Low": "green",
    "Very low": "green",
    "Low": "lightgreen",
    "Medium": "orange",
    "High": "red",
    "Very High": "darkred",
    "Very high": "darkred",
    "Unknown": "blue",
    "N/A": "gray",
}

# --- Gauge operational status → token. -------------------------------------------
OPERATIONAL_STATUS_TOKENS = {
    "Fully operational": "marker-green",
    "Maintenance required": "marker-amber",
    "Temporarily offline": "marker-red",
    "Decommissioned": "marker-grey",
    "Unknown": "marker-blue",
}

# --- Loan risk grade → token. -----------------------------------------------------
LOAN_RISK_TOKENS = {
    "Low": "marker-green",
    "Moderate": "marker-amber",
    "High": "marker-red-alt",
    "Critical": "marker-purple",
    "Unknown": "marker-slate",
}

# --- Property type → token. Categorical, so the hues carry no severity. -----------
PROPERTY_TYPE_TOKENS = {
    "Residential": "marker-blue",
    "Commercial": "marker-violet",
    "Industrial": "marker-orange",
    "Mixed": "marker-teal",
    "Unknown": "marker-silver",
}

# --- Storm intensity band → token. ------------------------------------------------
STORM_INTENSITY_TOKENS = {
    "low": "green-bright",
    "moderate": "amber-bright",
    "high": "red-bright",
    "extreme": "purple-bright",
}

# --- Flood depth band → token. ----------------------------------------------------
DEPTH_BAND_TOKENS = {
    "none": "flood-none",
    "minor": "yellow",
    "moderate": "amber-bright",
    "significant": "red-bright",
    "severe": "purple-bright",
}

# --- LTV band → token. Shares the loan-risk hues, deliberately: the two are the ----
# same judgement expressed two ways, and a reader comparing a grade against a ratio
# should see the same colour for the same level of concern.
LTV_BAND_TOKENS = {
    "low": "marker-green",
    "moderate": "marker-amber",
    "high": "marker-red-alt",
    "critical": "marker-purple",
}

# --- The thresholds those last three ramps are cut at. ----------------------------
# Upper bound of each band, ascending; a value above the last one falls in the final
# band. They live here rather than in the display code because they are parameters
# (coding rule R1) and because a band edge and the colour it selects are one decision.

#: Wind speed in m/s. Below 30 is "low", 30–50 "moderate", 50–70 "high", above
#: "extreme". These are display bands for the storm layer, not the classifier's own
#: thresholds — MKM-ST-001 is not driven from here.
#:
#: Banded on a strict ``<``, unlike the two ramps below: exactly 30 m/s is "moderate",
#: where exactly 0.5 m of depth is "minor". The inconsistency predates this package and
#: is preserved, because correcting it would recolour markers at the boundaries.
STORM_INTENSITY_BOUNDS_MS = ((30.0, "low"), (50.0, "moderate"), (70.0, "high"))

#: Flood depth in metres. At or below zero is "none".
DEPTH_BAND_BOUNDS_M = (
    (0.0, "none"), (0.5, "minor"), (1.0, "moderate"), (2.0, "significant"),
)

#: Loan-to-value as a ratio in 0–1.
LTV_BAND_BOUNDS = ((0.6, "low"), (0.8, "moderate"), (0.95, "high"))

#: Fallback band for the ramps above, used when a value exceeds every bound.
STORM_INTENSITY_TOP = "extreme"
DEPTH_BAND_TOP = "severe"
LTV_BAND_TOP = "critical"

# Every value→token ramp, for the emitters and the audit. The Folium marker ramp is
# deliberately absent: its values are colour names, not tokens, and including it would
# make a token check pass on strings that are not tokens.
STATUS_TOKEN_RAMPS = {
    "flood_risk": FLOOD_RISK_TOKENS,
    "operational_status": OPERATIONAL_STATUS_TOKENS,
    "loan_risk": LOAN_RISK_TOKENS,
    "property_type": PROPERTY_TYPE_TOKENS,
    "storm_intensity": STORM_INTENSITY_TOKENS,
    "depth_band": DEPTH_BAND_TOKENS,
    "ltv_band": LTV_BAND_TOKENS,
}

__all__ = [
    "FLOOD_RISK_TOKENS", "FLOOD_RISK_MARKERS", "OPERATIONAL_STATUS_TOKENS",
    "LOAN_RISK_TOKENS", "PROPERTY_TYPE_TOKENS", "STORM_INTENSITY_TOKENS",
    "DEPTH_BAND_TOKENS", "LTV_BAND_TOKENS", "STATUS_TOKEN_RAMPS",
    "STORM_INTENSITY_BOUNDS_MS", "DEPTH_BAND_BOUNDS_M", "LTV_BAND_BOUNDS",
    "STORM_INTENSITY_TOP", "DEPTH_BAND_TOP", "LTV_BAND_TOP",
]
