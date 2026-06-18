# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
