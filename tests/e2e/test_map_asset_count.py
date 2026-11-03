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
Landing-map asset count — every property and commercial asset loaded must
be countable on the map at the view that frames the whole portfolio.

Regression: on the thames demo book the landing view drew 40 assets as
about 25 distinguishable pins, because assets a few hundred metres apart
stacked their pins. Pins are now clustered and each bubble shows how many
assets it holds, so bubble numbers plus single pins must equal the book.
Properties and commercial share one cluster, so no bubble hides another.
"""

import json

import pytest

from tests.e2e._helpers import SHOWN_ASSET_COUNTS_JS
from tests.e2e.conftest import INPUT_DIR

FIT_PORTFOLIO_JS = """() => new Promise((resolve) => {
    const k = Object.keys(window).find(k => k.startsWith('map_'));
    const map = window[k];
    const pts = [];
    map.eachLayer(l => {
        if (window.L.MarkerClusterGroup && l instanceof L.MarkerClusterGroup) {
            // Fold back any bubble an earlier test fanned out.
            l.unspiderfy();
            l.getLayers().forEach(m => pts.push(m.getLatLng()));
        }
    });
    map.once('moveend', () => setTimeout(resolve, 500));
    // Same framing as the folium fit_bounds the landing view is built with.
    map.fitBounds(L.latLngBounds(pts), {padding: [30, 30], animate: false});
})"""


@pytest.fixture(scope="module")
def commercial_data():
    path = INPUT_DIR / "commercial.json"
    if not path.exists():
        pytest.skip("commercial.json not found — run `python phys.py port` first")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def shown(map_page):
    map_page.evaluate(FIT_PORTFOLIO_JS)
    return map_page.evaluate(SHOWN_ASSET_COUNTS_JS)


class TestLandingAssetCount:

    def test_every_property_is_on_the_map(self, shown, property_data):
        n = len(property_data.get("properties", []))
        assert n > 0
        assert shown["property"]["held"] == n, shown

    def test_every_commercial_asset_is_on_the_map(self, shown, commercial_data):
        n = len(commercial_data.get("commercial_assets", []))
        assert n > 0
        assert shown["commercial"]["held"] == n, shown

    def test_every_property_is_in_a_bubble_or_drawn(self, shown, property_data):
        assert shown["property"]["shown"] == len(property_data["properties"]), shown

    def test_every_commercial_asset_is_in_a_bubble_or_drawn(self, shown, commercial_data):
        assert shown["commercial"]["shown"] == len(commercial_data["commercial_assets"]), shown

    def test_on_screen_property_count_matches_book(self, shown, property_data):
        """What a viewer counts — bubble numbers plus drawn pins — is the book."""
        s = shown["property"]
        assert s["bubbleTotal"] + s["pins"] == len(property_data["properties"]), shown

    def test_on_screen_commercial_count_matches_book(self, shown, commercial_data):
        s = shown["commercial"]
        assert s["bubbleTotal"] + s["pins"] == len(commercial_data["commercial_assets"]), shown

    def test_bubble_labels_are_property_plus_commercial(self, shown):
        assert shown["bubbleLabelsMatch"], shown
