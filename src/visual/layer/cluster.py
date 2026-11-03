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

"""Marker clustering shared by the property and commercial layers.

At the zoom the map fits the whole portfolio to, many assets sit a few
pixels apart along the river and their pins stack, so the landing view
showed about 25 distinguishable pins for 40 assets. Clustering replaces
each stack with a bubble carrying its child count, so the bubbles and
single pins on screen always add up to the number of assets loaded.

Properties and commercial assets share one cluster: two separate cluster
layers put their bubbles on the same spots, and the one painted on top
hid the other's count. Each layer is a subgroup of the shared cluster,
so the layer control still toggles each type. A bubble shows the total,
its ring is split by type, and its tooltip gives the two counts. The
bubble colours are neutral and purple so they cannot be read as the
green/orange/red flood-frequency colours of the pins.
"""

import folium
from folium.plugins import FeatureGroupSubGroup, MarkerCluster

# Pins closer than this many screen pixels are clustered. Leaflet's
# default of 80 swallows pins that are distinguishable on their own.
MAX_CLUSTER_RADIUS_PX = 40
# From this zoom (street level) every pin is drawn individually.
DISABLE_CLUSTERING_AT_ZOOM = 16

# Commercial pins are the only purple ones (commercial_layer/layer.py).
_ICON_CREATE_JS = """
function(cluster) {
    var kids = cluster.getAllChildMarkers(), nc = 0;
    for (var i = 0; i < kids.length; i++) {
        var o = kids[i].options.icon && kids[i].options.icon.options;
        if (o && o.markerColor === 'purple') nc++;
    }
    var n = kids.length, np = n - nc, deg = Math.round(360 * np / n);
    var label = np + (np === 1 ? ' property' : ' properties') + ', ' + nc + ' commercial';
    return L.divIcon({
        html: '<div title="' + label + '" data-property="' + np + '" data-commercial="' + nc + '"'
            + ' style="background: conic-gradient(var(--mkm-cl-prop) 0 ' + deg + 'deg,'
            + ' var(--mkm-cl-comm) ' + deg + 'deg 360deg)"><span>' + n + '</span></div>',
        className: 'marker-cluster mkm-cluster',
        iconSize: L.point(40, 40)
    });
}
"""

_CLUSTER_CSS = """
<style>
/* Above every pin (Leaflet sets marker z-index inline, by latitude), so a
   gauge pin never hides a bubble's count. */
.mkm-cluster {
    --mkm-cl-prop: rgb(55, 65, 81); --mkm-cl-comm: rgb(160, 50, 160);
    background: rgba(255, 255, 255, 0.6); z-index: 10000 !important;
}
.mkm-cluster div {
    width: 34px; height: 34px; margin-left: 3px; margin-top: 3px;
    border-radius: 17px; position: relative;
}
.mkm-cluster span {
    position: absolute; inset: 5px; border-radius: 12px;
    background: rgb(31, 41, 55); color: #fff; text-align: center;
    font: 600 12px/24px "Helvetica Neue", Arial, sans-serif;
}
</style>
"""


def _asset_cluster(folium_map: folium.Map) -> MarkerCluster:
    """The map's one property/commercial cluster, created on first use."""
    cluster = getattr(folium_map, "_mkm_asset_cluster", None)
    if cluster is None:
        folium_map.get_root().header.add_child(folium.Element(_CLUSTER_CSS))
        cluster = MarkerCluster(
            control=False,
            icon_create_function=_ICON_CREATE_JS,
            options={
                "maxClusterRadius": MAX_CLUSTER_RADIUS_PX,
                "disableClusteringAtZoom": DISABLE_CLUSTERING_AT_ZOOM,
                "showCoverageOnHover": False,
                "spiderfyOnMaxZoom": True,
            },
        )
        cluster.add_to(folium_map)
        folium_map._mkm_asset_cluster = cluster
    return cluster


def make_asset_group(folium_map: folium.Map, name: str) -> FeatureGroupSubGroup:
    """Return a layer named ``name`` whose markers join the map's shared
    property/commercial cluster. The caller adds it to the map."""
    return FeatureGroupSubGroup(_asset_cluster(folium_map), name=name)
