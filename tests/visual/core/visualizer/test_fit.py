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

"""Tests for visual.core.visualizer.fit — the landing-map portfolio fit.

Regression: a page laid out before it had a size fitted the portfolio to
a 0x0 map and opened at maximum zoom on one street, showing none of the
properties or commercial assets.
"""

import shutil
import subprocess

import folium
import pytest

from visual.core.visualizer.fit import FitPortfolioBounds, fit_portfolio_bounds


def _render(m):
    return m.get_root().render()


class TestFitPortfolioBounds:

    def test_fits_the_extremes(self):
        m = folium.Map()
        fit_portfolio_bounds(m, [(51.5, -0.2), (51.9, -0.5), (51.2, -0.05)])
        html = _render(m)
        assert "[[51.2, -0.5], [51.9, -0.05]]" in html
        assert '{"padding": [30, 30]}' in html

    def test_single_point_adds_nothing(self):
        m = folium.Map()
        fit_portfolio_bounds(m, [(51.5, -0.2)])
        assert not any(isinstance(c, FitPortfolioBounds) for c in m._children.values())

    def test_refits_on_resize_when_first_fit_saw_no_size(self):
        m = folium.Map()
        fit_portfolio_bounds(m, [(51.4, -0.3), (51.6, -0.1)])
        html = _render(m)
        assert "map.on('resize'" in html
        assert f"}})({m.get_name()});" in html


NODE_HARNESS = r"""
// Minimal Leaflet map double: records fits, lets the test set its size
// and fire resize.
const fits = [];
const handlers = {};
const map = {
    size: {x: 0, y: 0},
    getSize() { return this.size; },
    fitBounds(b, o) { fits.push(this.size.x + 'x' + this.size.y); },
    on(ev, fn) { (handlers[ev] = handlers[ev] || []).push(fn); },
    off(ev, fn) { handlers[ev] = (handlers[ev] || []).filter(f => f !== fn); },
    fire(ev) { (handlers[ev] || []).slice().forEach(f => f()); },
};
const startSize = %s;
map.size = startSize;
const run = new Function('MAP', %s);
run(map);
map.size = {x: 0, y: 0}; map.fire('resize');       // still hidden: no refit
map.size = {x: 1024, y: 768}; map.fire('resize');  // laid out: refit once
map.fire('resize');                                 // later resizes: left alone
console.log(JSON.stringify(fits));
"""


def _script_body():
    import json
    m = folium.Map()
    fit_portfolio_bounds(m, [(51.4, -0.3), (51.6, -0.1)])
    fit = next(c for c in m._children.values() if isinstance(c, FitPortfolioBounds))
    js = fit._template.module.script(fit).replace(m.get_name(), "MAP")
    return json.dumps(js)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
class TestFitBehaviour:

    def _fits(self, start):
        out = subprocess.run(
            ["node", "-e", NODE_HARNESS % (start, _script_body())],
            capture_output=True, text=True, check=True)
        import json
        return json.loads(out.stdout)

    def test_hidden_page_refits_once_it_has_a_size(self):
        assert self._fits("{x: 0, y: 0}") == ["0x0", "1024x768"]

    def test_laid_out_page_fits_once(self):
        assert self._fits("{x: 800, y: 600}") == ["800x600"]
