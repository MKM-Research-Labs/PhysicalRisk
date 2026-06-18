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

"""Wind-coupled hazard-curve stages: win/faw/fow/bow/baw for property + commercial.

These scenarios sit alongside the flood spine (propertyhc) and the shd/she/bri
basis steps, following the IDENTICAL scenario protocol:

    flag  →  per-mode ts input dir  →  hc generator(mode)  →  hc output json

    win   wind-only         propertytsw    →  propertywin.json
    faw   flood AND wind     propertytsfaw  →  propertyfaw.json
    fow   flood OR wind      propertytsfow  →  propertyfow.json   (+ commercial*)
    bow   BRI OR wind        propertytsbow  →  propertybow.json
    baw   BRI AND wind       propertytsbaw  →  propertybaw.json

bow/baw mirror fow/faw but anchor the flood leg on the BRI-resilient flood
(derived from the bri ts rather than the raw flood spine) — the level the book
actually trades at. They are skipped when the bri ts is absent.

The wind leg has no gauge intermediary, so instead of a flood-propagation
timeseries we DERIVE the three ts dirs from the flood spine: the peril
timeseries generator re-stamps each event's flooded/exceeded_severe flags so
the existing hazard-curve pricer counts the peril of interest unchanged
(``count / num_storms × 10 000`` bps).

This stage runs AFTER the typhoon stage (which writes ``typhoon/damage/``).
It is skipped silently for catchments with no typhoon damage — the join input
the wind perils require.

Split into cohesive submodules; the public surface (``run_all`` plus the
individual ``run_*`` entry points) is unchanged.
"""

from ._helpers import (
    _damage_available, _peril_requested, _commercial_peril_requested,
)
from .property import (
    run_property_peril_ts, _run_property_peril_hc,
    run_propertywin, run_propertyfaw, run_propertyfow,
    run_propertybow, run_propertybaw, run_property_peril_decomposition,
)
from .commercial import (
    run_commercial_peril_ts, _run_commercial_peril_hc,
    run_commercialwin, run_commercialfaw, run_commercialfow,
    run_commercialbow, run_commercialbaw, run_commercial_peril_decomposition,
)
from ._run_all import run_all

__all__ = [
    'run_all',
    '_damage_available', '_peril_requested', '_commercial_peril_requested',
    'run_property_peril_ts', '_run_property_peril_hc',
    'run_propertywin', 'run_propertyfaw', 'run_propertyfow',
    'run_propertybow', 'run_propertybaw', 'run_property_peril_decomposition',
    'run_commercial_peril_ts', '_run_commercial_peril_hc',
    'run_commercialwin', 'run_commercialfaw', 'run_commercialfow',
    'run_commercialbow', 'run_commercialbaw', 'run_commercial_peril_decomposition',
]
