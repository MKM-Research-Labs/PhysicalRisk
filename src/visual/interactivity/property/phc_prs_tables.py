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
Property hazard PRS-pricing — HTML-building helper functions.

Two pure JS helpers concatenated into the parent IIFE:

  - ``_buildPRSComponentTableHTML(result, gauges, propElev)`` returns the
    component summary table (gauge row per nearest gauge, property row,
    avg-basis row).
  - ``_buildPRSWaterfallTableHTML(sd, terrainDelta, selectedZone,
    actualZone, adjustedPropSpread)`` returns the spread-decomposition
    waterfall (Path 1 distance-first / Path 2 elevation-first, with an
    optional Terrain Effect row).

Pulled out of ``phc_prs_render.py`` so the main render function stays
focused on layout assembly + chart rendering.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment with the two HTML-builder helpers."""
    return js_static('property/phc_prs_tables.js')
