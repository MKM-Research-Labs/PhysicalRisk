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
Storm portfolio — Sim (map animation) tab sub-module.

Embedded Leaflet map showing frame-by-frame flood propagation from
gauges to properties with play/pause, speed control, and scrubber.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for sim/map tab (injected into parent IIFE)."""
    from config.models import STORM_SIMULATION_HOURS
    from . import catchment_map_center
    _max = STORM_SIMULATION_HOURS - 1
    _lat, _lon = catchment_map_center()
    js = _get_js_template()
    return (
        js.replace("'__SCRUBBER_MAX__'", f"'{_max}'")
        .replace('__ANIM_MAX__', str(_max))
        .replace('__MAP_LAT__', f"{_lat:.5f}")
        .replace('__MAP_LON__', f"{_lon:.5f}")
    )


def _get_js_template() -> str:
    return js_static('storm/sp_sim.js')
