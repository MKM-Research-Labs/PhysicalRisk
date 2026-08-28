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

"""Domain hues: the colours that carry a meaning this platform alone has.

:mod:`config.theme._palette` holds the chrome — the accent, the paper, the ink, the
RAG ramp. This holds the vocabulary that is specific to physical risk: which colour a
peril is drawn in, the flood-depth ramp, the map's choropleth families, the sign of a
P&L. They are separated because they change for different reasons. An adopter
rebrands the chrome; the domain hues change when the science does.

Only the *tokens* live here. The ramps that map a business value to one of them — the
flood-risk bands, the gauge operational states, the loan risk grades — are step 2 of
docs/refactor/theme_centralisation_plan.md, when ``src/visual/utils/color_schemes``
moves into this package. Until then those maps are still in ``src/``, which is the R1
violation step 2 exists to fix.
"""

# --- One colour per peril, so a legend, a tab and a map layer agree. --------------
# The four perils the platform prices. Flood takes the accent blue because it is the
# platform's original and default peril; the other three take hues from the palette's
# HUE group rather than from RAG, because a peril is not a severity.
PERIL = {
    "peril-flood": "#1976d2",
    "peril-wind": "#00838f",
    "peril-fire": "#bf360c",
    "peril-seismic": "#6a1b9a",
}

# --- Water depth, shallow to deep. The map's flood layers and the depth legends. --
# A single-hue sequential ramp: depth is a magnitude, so it reads as one colour
# getting darker rather than as a set of categories.
DEPTH = {
    "depth-1": "#ebf5fb",
    "depth-2": "#aed6f1",
    "depth-3": "#5dade2",
    "depth-4": "#2874a6",
    "depth-5": "#1a5276",
}

# --- The map's other choropleth families, from src/visual/layer. ------------------
# Kept as families rather than folded into HUE because a layer legend needs a light
# fill and a dark stroke that belong together, and separating them across groups is
# how a legend ends up with a fill from one ramp and an outline from another.
MAP = {
    "layer-violet": "#6c3483",
    "layer-violet-soft": "#8e44ad",
    "layer-violet-bg": "#e8daef",
    "layer-violet-wash": "#f5eef8",
    "layer-olive": "#7d6608",
    "layer-olive-wash": "#fef9e7",
    "layer-teal": "#148f77",
    "layer-teal-wash": "#e8f8f5",
    "layer-clay": "#943126",
    "layer-clay-wash": "#fadbd8",
    "layer-earth": "#6e2c00",
    "layer-earth-wash": "#fdebd0",
    "layer-neutral": "#566573",
}

# --- The map's markers and popups draw from a different palette than the console. --
# These are the flat-UI family (Nephritis, Pomegranate, Peter River, Amethyst…) that
# the gauge markers, the property markers and their popups have always used, where the
# console chrome is Material. Two palettes in one product is drift, but it is drift
# along a real seam — the map is a different surface with a different job — so they
# are recorded distinctly rather than collapsed. Collapsing them would move pixels on
# every marker, which is a decision for a design pass, not for this migration.
MARKER = {
    "marker-green": "#27ae60",
    "marker-amber": "#f39c12",
    "marker-red": "#c0392b",
    "marker-red-alt": "#e74c3c",
    "marker-purple": "#8e44ad",
    "marker-violet": "#9b59b6",
    "marker-orange": "#e67e22",
    "marker-teal": "#1abc9c",
    "marker-blue": "#3498db",
    "marker-slate": "#34495e",
    "marker-grey": "#7f8c8d",
    "marker-silver": "#95a5a6",
}

# The "no flood" fill on the depth ramp. One digit away from the palette's ``ok-bg``
# (#e8f5e9) and not the same colour — a near-duplicate that predates this package.
# Recorded exactly as it is drawn today; whether the difference is intentional is a
# question for the design pass, not something to silently resolve here.
FLOOD = {
    "flood-none": "#e8f5e8",
}

# --- The sign of a number. --------------------------------------------------------
# The trading surfaces draw a gain green and a loss red, which are the RAG hues doing
# a second job. Named separately because they are not a rating: a loss is not "Red"
# in the governance sense, and an adopter who recolours the risk ratings should not
# silently recolour the blotter. ``-fill`` is the translucent bar form the P&L charts
# use, which cannot be a token reference because Chart.js resolves no ``var()``.
SIGN = {
    "gain": "#2e7d32",
    "loss": "#c62828",
    "gain-fill": "rgba(46, 125, 50, 0.8)",
    "loss-fill": "rgba(198, 40, 40, 0.8)",
    "flat": "#90a4ae",
}

# --- Series colours for a chart with no meaning to carry. -------------------------
# A categorical ramp: eight hues chosen to stay distinguishable in order, for the
# charts that plot "gauge 1, gauge 2, gauge 3" and need them merely to differ. The
# console currently spells four separate arrays of these; they collapse onto this one
# in step 6, and Chart.js reads it through ``Theme.value()`` rather than ``var()``.
SERIES = {
    "series-1": "#1565c0",
    "series-2": "#0277bd",
    "series-3": "#00838f",
    "series-4": "#00695c",
    "series-5": "#2e7d32",
    "series-6": "#558b2f",
    "series-7": "#9e9d24",
    "series-8": "#f57f17",
}

__all__ = ["PERIL", "DEPTH", "MAP", "MARKER", "FLOOD", "SIGN", "SERIES"]
