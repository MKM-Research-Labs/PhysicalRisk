#!/usr/bin/env python3

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
Snap a catchment's gauge points to the nearest point on its river polyline.

Projects each gauge listed in ``data/catch/<catchment>/config.py`` onto the
cached river polyline at ``data/catch/<catchment>/river_polyline.json`` and
rewrites the GAUGE_POINTS block in-place. If the polyline cache is missing
and the catchment is Thames, the river geometry can be fetched from the
OpenStreetMap Overpass API as a fallback.

Usage:
    python tools/snap_gauges_to_river.py --catchment halong
    python tools/snap_gauges_to_river.py --catchment thames --dry-run
    python tools/snap_gauges_to_river.py --catchment thames --fetch-overpass
"""

import argparse
import json
import math
import re
import ssl
import sys
import urllib.request
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Polyline sources
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Read / write catchment config.py
# ---------------------------------------------------------------------------

def get_catchment_paths(catchment):
    """Resolve data/catch/<catchment>/ and its config.py."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    catchment_dir = project_root / "data" / "catch" / catchment
    config_path = catchment_dir / "config.py"
    if not catchment_dir.exists():
        sys.exit(f"ERROR: {catchment_dir} not found")
    if not config_path.exists():
        sys.exit(f"ERROR: {config_path} not found")
    return catchment_dir, config_path


def parse_gauge_points(source):
    """Extract GAUGE_POINTS list from a catchment config.py source."""
    pattern = r"(GAUGE_POINTS\s*=\s*\[)(.*?)(\n\])"
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        sys.exit("ERROR: Could not find GAUGE_POINTS in config.py")

    inner = match.group(2)
    tuples = re.findall(r"\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)", inner)
    points = [(float(lat), float(lon), float(elev)) for lat, lon, elev in tuples]
    return points, match


def format_gauge_points(points):
    """Format gauge points as Python source, 2 per line."""
    lines = []
    for i in range(0, len(points), 2):
        pair = []
        for j in range(2):
            if i + j < len(points):
                lat, lon, elev = points[i + j]
                pair.append(f"({lat:.4f}, {lon:.4f}, {elev:.2f})")
        lines.append("    " + ", ".join(pair) + ",")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Snap gauge points to a catchment river polyline")
    parser.add_argument("--catchment", required=True,
                        help="Catchment name (matches data/catch/<name>/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print corrections without updating the file")
    parser.add_argument("--fetch-overpass", action="store_true",
                        help="Force re-fetch from Overpass API (ignores cached polyline)")
    args = parser.parse_args()

    catchment_dir, config_path = get_catchment_paths(args.catchment)
    source = config_path.read_text()
    original_points, match = parse_gauge_points(source)

    print(f"Found {len(original_points)} gauge points in {args.catchment}/config.py")

    river = None
    fetched_fresh = False
    if not args.fetch_overpass:
        river = load_polyline_cache(catchment_dir)
    if river is None:
        river = fetch_river_geometry(args.catchment)
        fetched_fresh = True

    if len(river) < 2:
        sys.exit("ERROR: River polyline too short (need >= 2 points)")

    if fetched_fresh and not args.dry_run:
        polyline_path = catchment_dir / "river_polyline.json"
        with open(polyline_path, "w") as f:
            json.dump([[round(p[0], 7), round(p[1], 7)] for p in river], f, indent=2)
        print(f"Wrote {len(river)} points to {polyline_path}")

    print()
    print(f"{'#':>3}  {'Old Lat':>10} {'Old Lon':>10}  ->  {'New Lat':>10} {'New Lon':>10}  {'Moved':>8}")
    print("-" * 72)

    snapped = []
    total_moved = 0.0
    max_moved = 0.0

    for i, (lat, lon, elev) in enumerate(original_points):
        new_lat, new_lon, dist = snap_to_polyline(lat, lon, river)
        snapped.append((round(new_lat, 4), round(new_lon, 4), elev))
        total_moved += dist
        max_moved = max(max_moved, dist)

        flag = " ***" if dist > 500 else ""
        print(f"{i+1:3d}  {lat:10.4f} {lon:10.4f}  ->  {new_lat:10.4f} {new_lon:10.4f}  {dist:7.0f}m{flag}")

    avg_moved = total_moved / len(original_points) if original_points else 0
    print()
    print(f"Average move: {avg_moved:.0f}m | Max move: {max_moved:.0f}m")

    if args.dry_run:
        print("\n[DRY RUN] No files updated.")
        return

    new_block = format_gauge_points(snapped)
    new_source = (source[:match.start()]
                  + "GAUGE_POINTS = [\n"
                  + new_block + "\n"
                  + "]"
                  + source[match.end():])

    config_path.write_text(new_source)
    print(f"\nUpdated {config_path}")
    print(f"Run `python app.py port --all --no-backup` to regenerate "
          f"portfolio with corrected gauges.")


if __name__ == "__main__":
    main()
