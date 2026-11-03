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

"""Tests for property/commercial marker clustering (visual.layer.cluster).

Regression: the landing map fitted the whole portfolio, at which zoom
assets a few hundred metres apart stacked their pins, so the map showed
far fewer properties and commercial assets than were loaded. Every
property and commercial marker must now sit in one shared cluster whose
bubbles carry the child count; two separate clusters stacked their
bubbles and hid one type's count behind the other's.
"""

import json
import re
import shutil
import subprocess
from types import SimpleNamespace

import folium
import pytest
from folium.plugins import FeatureGroupSubGroup, MarkerCluster

from tests.visual.layer.commercial.test_commercial_layer import _asset
from tests.visual.layer.property.add_to_map import MockLoadedData, _make_property
from visual.layer import CommercialLayer, PropertyLayer
from visual.layer.cluster import (
    DISABLE_CLUSTERING_AT_ZOOM,
    MAX_CLUSTER_RADIUS_PX,
    make_asset_group,
)

# Twelve properties and twelve commercial assets packed within ~200 m,
# as along the Thames in the demo book.
N_EACH = 12


def _offset(i):
    return 51.5 + i * 0.0002, -0.1 + i * 0.0002


def _render(m: folium.Map) -> str:
    return m.get_root().render()


def _clusters(m):
    return [c for c in m._children.values() if isinstance(c, MarkerCluster)]


def _portfolio_map():
    m = folium.Map(location=[51.5, -0.1], zoom_start=10)
    props = [_make_property(f"PROP-{i:03x}", *_offset(i)) for i in range(N_EACH)]
    PropertyLayer().add_to_map(m, MockLoadedData(property_data={"items": props}))
    assets = [_asset(f"CPROP-{i:03x}", lat=_offset(i)[0], lon=_offset(i)[1])
              for i in range(N_EACH)]
    CommercialLayer().add_to_map(m, SimpleNamespace(
        commercial_data={"commercial_assets": assets}, commercial_loan_lookup={}))
    return m


class TestSharedCluster:

    def test_one_cluster_per_map(self):
        m = folium.Map()
        a = make_asset_group(m, "Properties")
        b = make_asset_group(m, "Commercial Assets")
        assert isinstance(a, FeatureGroupSubGroup)
        assert len(_clusters(m)) == 1
        assert a._group is b._group is _clusters(m)[0]

    def test_cluster_options(self):
        m = folium.Map()
        make_asset_group(m, "Properties")
        mc = _clusters(m)[0]
        assert mc.control is False  # the subgroups are what the layer control toggles
        assert mc.options["maxClusterRadius"] == MAX_CLUSTER_RADIUS_PX
        assert mc.options["disableClusteringAtZoom"] == DISABLE_CLUSTERING_AT_ZOOM
        assert mc.options["showCoverageOnHover"] is False

    def test_bubble_shows_total_and_split(self):
        m = folium.Map()
        make_asset_group(m, "Properties")
        fn = _clusters(m)[0].icon_create_function
        assert "getAllChildMarkers()" in fn
        assert "data-property" in fn and "data-commercial" in fn

    def test_stylesheet_added_once(self):
        m = folium.Map()
        make_asset_group(m, "Properties")
        make_asset_group(m, "Commercial Assets")
        assert _render(m).count(".mkm-cluster span") == 1


class TestEveryAssetIsClustered:

    def test_layers_hold_every_marker(self):
        m = _portfolio_map()
        groups = [c for c in m._children.values() if isinstance(c, FeatureGroupSubGroup)]
        assert sorted(g.layer_name for g in groups) == ["Commercial Assets", "Properties"]
        for g in groups:
            markers = [x for x in g._children.values() if isinstance(x, folium.Marker)]
            assert len(markers) == N_EACH

    def test_rendered_markers_join_the_shared_cluster(self):
        html = _render(_portfolio_map())
        cluster = re.findall(r"var (marker_cluster_\w+) = L\.markerClusterGroup", html)
        assert len(cluster) == 1
        subgroups = set(re.findall(
            r"var (feature_group_sub_group_\w+) = L\.featureGroup\.subGroup\(\s*"
            + cluster[0], html))
        assert len(subgroups) == 2
        targets = re.findall(r"var marker_\w+ = L\.marker\([^;]*?\)\.addTo\((\w+)\);", html, re.S)
        assert len(targets) == 2 * N_EACH
        assert set(targets) == subgroups

    def test_plugins_loaded(self):
        html = _render(_portfolio_map())
        assert "leaflet.markercluster" in html
        assert "leaflet.featuregroup.subgroup" in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
class TestBubbleIcon:
    """Run the bubble's icon function in node against a fake cluster."""

    def _icon(self, colours):
        m = folium.Map()
        make_asset_group(m, "Properties")
        fn = _clusters(m)[0].icon_create_function
        js = (
            "const L = {divIcon: o => o, point: (x, y) => [x, y]};"
            f"const kids = {json.dumps(colours)}.map(c => ({{options: {{icon: {{options: {{markerColor: c}}}}}}}}));"
            f"const icon = ({fn})({{getAllChildMarkers: () => kids}});"
            "console.log(JSON.stringify(icon));"
        )
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def test_mixed_bubble_counts_each_type(self):
        icon = self._icon(["green", "orange", "purple", "red", "purple"])
        assert 'data-property="3"' in icon["html"]
        assert 'data-commercial="2"' in icon["html"]
        assert "<span>5</span>" in icon["html"]
        assert 'title="3 properties, 2 commercial"' in icon["html"]

    def test_single_property_label(self):
        icon = self._icon(["green", "purple"])
        assert 'title="1 property, 1 commercial"' in icon["html"]
