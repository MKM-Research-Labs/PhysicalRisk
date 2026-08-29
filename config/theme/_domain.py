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
    # The combined-peril rows (flood AND wind, flood OR wind) on the hazard panel, each
    # an ink and a tint. They are their own colours rather than a blend of the two
    # perils they combine, which is a reasonable choice — a blend of blue and teal would
    # read as neither.
    "peril-flood-and-wind-bg": "#e0f7fa",
    "peril-flood-or-wind": "#5d4037",
    "peril-flood-or-wind-bg": "#efebe9",
    # The seismic row on the same panel draws #455a64, not peril-seismic's #6a1b9a. The
    # two disagree, and have since the seismic work landed: the independent-perils row
    # is slate where the peril's own colour is purple. Recorded rather than resolved,
    # because picking one recolours a row on a live panel and that is a design call.
    "peril-seismic-row": "#455a64",
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
    # Section header accents in the property detail panel, from the same flat-UI family
    # as the layer fills above.
    "layer-navy": "#154360",
    "layer-plum": "#4a235a",
    "layer-brick": "#922b21",
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

# --- The audit report viewer's terminal. ------------------------------------------
# ``mg-audit-reports.js`` renders build logs in a dark panel with macOS traffic-light
# chrome and log-level syntax colouring. It is a dark surface inside a light console —
# the only one besides the admin page — so it names its colours separately rather than
# borrowing tokens that mean "paper" and "ink" everywhere else.
LOG = {
    "log-bg": "#1e1e1e",
    "log-header": "#2d2d2d",
    "log-text": "#d4d4d4",
    "log-info": "#9cdcfe",
    "log-warn": "#e5a00d",
    "log-ok-bg": "#1a3a1a",
    # The three window buttons, in their conventional order and colours.
    "log-close": "#ff5f56",
    "log-minimise": "#ffbd2e",
    "log-expand": "#27c93f",
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
    "flat-fill": "rgba(144, 164, 174, 0.8)",
}

# --- Chart infrastructure: the marks a chart draws that carry no data. -------------
# Grid lines, axis rules and the translucent fills under a series. They are here rather
# than in SURFACE because a chart's furniture sits on a different background from a
# panel's and has to stay legible over both.
CHART = {
    "grid-line": "rgba(0, 0, 0, 0.06)",
    "chart-fill-accent": "rgba(21, 101, 192, 0.08)",
    "chart-fill-danger": "rgba(244, 67, 54, 0.25)",
    "chart-transparent": "rgba(0, 0, 0, 0)",
    # The trigger levels as chart fills, mirroring SIGN's gain-fill/loss-fill. The
    # storm panels drew these at six different opacities across two charts — 0.6, 0.7,
    # 0.8 and 0.9 for the same three levels — which is each chart having chosen for
    # itself rather than a scale. One fill per level, plus the faint wash the VaR chart
    # uses behind a distribution, which is a genuinely different job from a bar fill.
    "alert-fill": "rgba(251, 192, 45, 0.8)",
    "warning-fill": "rgba(245, 124, 0, 0.8)",
    "severe-fill": "rgba(211, 47, 47, 0.8)",
    "severe-wash": "rgba(211, 47, 47, 0.1)",
    # The VaR histogram's two distributions. They were built by concatenating a partial
    # rgba prefix with an alpha further down the file — 'rgba(25,118,210' + ',0.5)' —
    # which no scan can read as a colour and no adopter could ever have found.
    "chart-fill-accent-half": "rgba(25, 118, 210, 0.5)",
    "chart-fill-purple-half": "rgba(123, 31, 162, 0.5)",
    # The impact panel's series fills — accent bright, red bright and amber deep, each
    # translucent over the plot area.
    "chart-fill-bright": "rgba(33, 150, 243, 0.6)",
    "chart-wash-bright": "rgba(33, 150, 243, 0.1)",
    "chart-fill-red": "rgba(244, 67, 54, 0.7)",
    "chart-fill-amber": "rgba(230, 81, 0, 0.8)",
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

# --- Categorical palettes: hues that identify a thing, not rate it. ---------------
# A lineage step, a storm sequence type, a report format. The colour is a label, so the
# only requirement is that neighbours stay distinguishable. Kept apart from the RAG and
# badge ramps precisely because these carry no judgement — drawing a dataset red would
# read as a problem with it.

#: The pipeline steps the lineage panels colour-code. Ten steps, ten hues.
DATASET = {
    "dataset-gauges": "#4caf50",
    "dataset-properties": "#2196f3",
    "dataset-mortgages": "#ff9800",
    "dataset-gaugehd": "#009688",
    "dataset-stressm": "#e91e63",
    "dataset-hazard": "#f44336",
    "dataset-propertyts": "#795548",
    "dataset-propertyhc": "#607d8b",
    "dataset-counterparties": "#9c27b0",
    "dataset-blotter": "#ff5722",
}

#: Storm sequence types, in the two forms the impact panels draw them: a saturated hue
#: for chart bars and a tint/ink pair for the inline chips.
SEQUENCE = {
    "sequence-isolated": "#42a5f5",
    "sequence-doublet": "#ffa726",
    "sequence-cluster": "#ef5350",
    "sequence-persistent": "#ab47bc",
}

__all__ = [
    "PERIL", "DEPTH", "MAP", "MARKER", "FLOOD", "SIGN", "SERIES", "DATASET",
    "SEQUENCE", "CHART", "LOG",
]
