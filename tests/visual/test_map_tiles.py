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

"""Every JavaScript-built Leaflet map takes its tiles from config.visual.

CARTO basemaps need an API key (and a paid plan above 1M commercial requests
a month), so no map may point at them; the OpenStreetMap attribution must
stay visible.
"""
import pytest

from config.visual import MAP_TILE_ATTRIBUTION, MAP_TILE_URL
from visual.interactivity._jsbundle import with_map_tiles
from visual.interactivity.storm import fa_render, sp_sim
from visual.interactivity.trading.aggregate import map_view


@pytest.mark.parametrize("module", [fa_render, sp_sim, map_view],
                         ids=["fa_render", "sp_sim", "map_view"])
def test_map_uses_configured_tiles_with_attribution(module):
    js = module.get_js()
    assert MAP_TILE_URL in js
    assert MAP_TILE_ATTRIBUTION in js
    assert "cartocdn" not in js
    assert "__MAP_TILE" not in js
    assert "attributionControl: false" not in js


def test_with_map_tiles_fills_every_placeholder():
    out = with_map_tiles("L.tileLayer('__MAP_TILE_URL__', "
                         "{attribution: '__MAP_TILE_ATTRIBUTION__', maxZoom: __MAP_TILE_MAX_ZOOM__})")
    assert "__" not in out
    assert "openstreetmap.org" in out
