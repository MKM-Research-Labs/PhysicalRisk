#!/usr/bin/env python3

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

"""Geometry + Overpass-fetch helpers for snap_gauges_to_river."""

import json
import math
import ssl
import sys
import urllib.request

try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

# ---------------------------------------------------------------------------
# Overpass presets — add a catchment entry to enable --fetch-overpass for it
# ---------------------------------------------------------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "PhysicalRisk/1.0 (research; risk@kerrshearer.co.uk)"

OVERPASS_PRESETS = {
    "thames": {
        "bbox": "51.41,-0.35,51.52,0.35",  # S,W,N,E — Richmond to Tilbury
        "name_regex": "Thames",
    },
    "halong": {
        "bbox": "20.90,105.70,21.15,106.05",  # S,W,N,E — Red River through Hanoi
        "relation_id": 2377017,  # OSM relation: Red River / Sông Hồng
    },
}


def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in metres between two WGS84 points."""
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_point_on_segment(px, py, ax, ay, bx, by):
    """
    Project point P onto segment AB.  Returns (nearest_x, nearest_y, t).
    Coordinates are in degrees but the projection is done in a locally
    scaled Cartesian frame so the result is accurate for small distances.
    """
    cos_lat = math.cos(math.radians(px))
    dx = (bx - ax)
    dy = (by - ay) * cos_lat

    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-18:
        return ax, ay, 0.0

    t = ((px - ax) * dx + (py - ay) * cos_lat * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))

    nx = ax + t * (bx - ax)
    ny = ay + t * (by - ay)
    return nx, ny, t


def snap_to_polyline(lat, lon, polyline):
    """
    Find the closest point on a polyline to (lat, lon).
    polyline: list of (lat, lon) tuples.
    Returns (snapped_lat, snapped_lon, distance_m).
    """
    best_lat, best_lon = lat, lon
    best_dist = float("inf")

    for i in range(len(polyline) - 1):
        ax, ay = polyline[i]
        bx, by = polyline[i + 1]
        nx, ny, _ = nearest_point_on_segment(lat, lon, ax, ay, bx, by)
        d = haversine_m(lat, lon, nx, ny)
        if d < best_dist:
            best_dist = d
            best_lat = nx
            best_lon = ny

    return best_lat, best_lon, best_dist


def load_polyline_cache(catchment_dir):
    """Load polyline from data/catch/<catchment>/river_polyline.json."""
    path = catchment_dir / "river_polyline.json"
    if not path.exists():
        return None
    with open(path) as f:
        raw = json.load(f)
    points = [(float(p[0]), float(p[1])) for p in raw]
    print(f"Loaded {len(points)} points from {path.name}")
    return points


def fetch_river_geometry(catchment):
    """Fetch river polyline from Overpass for a known preset."""
    preset = OVERPASS_PRESETS.get(catchment)
    if not preset:
        sys.exit(f"ERROR: no Overpass preset for catchment '{catchment}'. "
                 f"Add one to OVERPASS_PRESETS or provide a river_polyline.json.")

    bbox = preset["bbox"]
    if "relation_id" in preset:
        # Fetch via OSM relation — picks up unnamed segments too
        query = (
            '[out:json][timeout:120];'
            f'relation({preset["relation_id"]});way(r)({bbox});'
            'out body;>;out skel qt;'
        )
    else:
        query = (
            '[out:json][timeout:120];'
            f'way["waterway"]["name"~"{preset["name_regex"]}"]({bbox});'
            'out body;>;out skel qt;'
        )

    print(f"Fetching {catchment} river geometry from OpenStreetMap...")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=f"data={query}".encode(),
        method="POST",
        headers={"User-Agent": USER_AGENT},
    )
    data = urllib.request.urlopen(req, timeout=90, context=_SSL_CTX).read()

    result = json.loads(data)
    elements = result.get("elements", [])

    nodes = {}
    ways = []
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            ways.append(el)

    print(f"  Received {len(ways)} way(s) and {len(nodes)} node(s)")

    all_points = []
    for way in ways:
        for nid in way.get("nodes", []):
            if nid in nodes:
                all_points.append(nodes[nid])

    seen = set()
    unique = []
    for p in all_points:
        key = (round(p[0], 7), round(p[1], 7))
        if key not in seen:
            seen.add(key)
            unique.append(p)

    unique.sort(key=lambda p: p[1])
    print(f"  River polyline: {len(unique)} unique points")
    return unique
