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

"""Fit the landing map to the whole portfolio, even when the page has no
size yet.

folium's ``fit_bounds`` runs once, as the page script executes. A page
loaded before it is laid out (a background tab, a hidden pane) has a 0x0
map at that moment, Leaflet fits the bounds to an empty box and lands at
maximum zoom: the landing view shows one street and none of the assets.
This fits as folium would, then fits again on the map's first resize if
the first fit saw no size.
"""

import json

from branca.element import MacroElement
from jinja2 import Template

FIT_PADDING_PX = 30


class FitPortfolioBounds(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        (function (map) {
            var bounds = {{ this.bounds }};
            var opts = {{ this.options }};
            var sized = function () { var s = map.getSize(); return s.x > 0 && s.y > 0; };
            var wasEmpty = !sized();
            map.fitBounds(bounds, opts);
            if (wasEmpty) {
                map.on('resize', function refit() {
                    if (!sized()) return;
                    map.off('resize', refit);
                    map.fitBounds(bounds, opts);
                });
            }
        })({{ this._parent.get_name() }});
        {% endmacro %}
    """)

    def __init__(self, bounds, padding=FIT_PADDING_PX):
        super().__init__()
        self._name = "FitPortfolioBounds"
        self.bounds = json.dumps(bounds)
        self.options = json.dumps({"padding": [padding, padding]})


def fit_portfolio_bounds(base_map, coords) -> None:
    """Fit ``base_map`` to every (lat, lon) in ``coords`` (needs two or more)."""
    if len(coords) < 2:
        return
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    base_map.add_child(FitPortfolioBounds(
        [[min(lats), min(lons)], [max(lats), max(lons)]]))
