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
