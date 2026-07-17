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
Aggregate View tab for the Trading Desk panel.

Embedded Leaflet map showing:
- Gauge circles: sized by absolute net FS01, colored by direction
- Permanent gauge area labels for quick identification
- Popups with aggregate trade summaries
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript fragment for the aggregate view tab."""
    from config.visual import get_map_center
    _lat, _lon = get_map_center()
    return (
        js_static('trading/aggregate/map_view.js')
        .replace('__MAP_LAT__', f"{_lat:.5f}")
        .replace('__MAP_LON__', f"{_lon:.5f}")
    )
