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

"""
Basis Explorer — Peril Outcomes fan (Stage 7).

The basis waterfall (Gauge -> SHE -> SHD -> Property -> BRI) carries the
FLOOD spread to the property/BRI node. At that node the spread fans out into
the four PRS peril outcomes (coupling_spec.md Stage 6/7):

    Flood only       — severe flood triggers (the flood spine itself)
    Wind only        — binary is_prs_wind damage-onset triggers
    Flood OR Wind     — union over the 1:1-paired event set (the headline PRS)
    Flood AND Wind    — intersection (both perils on one event)

The four obey inclusion-exclusion: union = flood + wind - joint. Wind has no
gauge propagation — it is a pure intersect/union at the property node — so the
fan lives at the OUTPUT end of the waterfall, not along the geographic spine.

The peril data is ``spread_decomposition.peril_outcomes`` (preferred; the
BRI-adjusted node when present) with a fallback to the top-level ``prs_perils``.
Absent for flood-only catchments (no typhoon stage) — the renderer then draws
nothing and the caller keeps the flood-only layout (byte-identical).
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the peril-outcomes fan renderer."""
    return js_static('property/phc_peril_outcomes.js')
