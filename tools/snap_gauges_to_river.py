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
Snap gauge points to the nearest point on the River Thames.

Queries the Thames waterway geometry from OpenStreetMap via the Overpass API,
then projects each gauge point onto the nearest river segment. Updates
data/catch/thames/config.py with corrected coordinates in-place.

Usage:
    python tools/snap_gauges_to_river.py          # run with auto-update
    python tools/snap_gauges_to_river.py --dry-run # print only, no file update
"""

import argparse
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Bounding box for the Thames from Richmond to Tilbury (S,W,N,E)
THAMES_BBOX = "51.41,-0.35,51.52,0.35"

# Overpass query: get the River Thames waterway within the bounding box
# Fetch ways tagged as river/canal named Thames, then resolve their nodes
OVERPASS_QUERY = (
    '[out:json][timeout:120];'
    f'way["waterway"]["name"~"Thames"]({THAMES_BBOX});'
    'out body;>;out skel qt;'
)


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
    # Scale longitude by cos(latitude) so 1 degree lon ~ 1 degree lat
    cos_lat = math.cos(math.radians(px))
    dx = (bx - ax)          # lat difference (already ~111 km / deg)
    dy = (by - ay) * cos_lat  # lon scaled

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
# Overpass API
# ---------------------------------------------------------------------------

def fetch_thames_geometry():
    """Fetch Thames river nodes from Overpass API."""
    print("Fetching Thames geometry from OpenStreetMap...")
    data = urllib.request.urlopen(
        urllib.request.Request(
            OVERPASS_URL,
            data=f"data={OVERPASS_QUERY}".encode(),
            method="POST",
        ),
        timeout=90,
    ).read()

    result = json.loads(data)
    elements = result.get("elements", [])

    # Separate nodes and ways
    nodes = {}
    ways = []
    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            ways.append(el)

    print(f"  Received {len(ways)} way(s) and {len(nodes)} node(s)")

    # Build polylines from ways, resolving node refs to coordinates
    polylines = []
    for way in ways:
        coords = []
        for nid in way.get("nodes", []):
            if nid in nodes:
                coords.append(nodes[nid])
        if len(coords) >= 2:
            polylines.append(coords)

    # Merge into one big polyline sorted roughly west-to-east
    all_points = []
    for pl in polylines:
        all_points.extend(pl)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for p in all_points:
        key = (round(p[0], 7), round(p[1], 7))
        if key not in seen:
            seen.add(key)
            unique.append(p)

    # Sort west to east by longitude
    unique.sort(key=lambda p: p[1])
    print(f"  River polyline: {len(unique)} unique points")
    return unique


# ---------------------------------------------------------------------------
# Read / write thames.py
# ---------------------------------------------------------------------------

def get_thames_path():
    """Locate data/catch/thames/config.py from project root."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    path = project_root / "data" / "catch" / "thames" / "config.py"
    if not path.exists():
        sys.exit(f"ERROR: {path} not found")
    return path


def parse_gauge_points(source):
    """Extract GAUGE_POINTS list from thames.py source text."""
    # Match the GAUGE_POINTS = [...] block
    pattern = r"(GAUGE_POINTS\s*=\s*\[)(.*?)(\])"
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        sys.exit("ERROR: Could not find GAUGE_POINTS in thames.py")

    inner = match.group(2)
    # Parse tuples: (lat, lon, elev)
    tuples = re.findall(r"\(\s*([\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*([\d.]+)\s*\)", inner)
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
    parser = argparse.ArgumentParser(description="Snap gauge points to River Thames")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print corrections without updating the file")
    args = parser.parse_args()

    thames_path = get_thames_path()
    source = thames_path.read_text()
    original_points, match = parse_gauge_points(source)

    print(f"Found {len(original_points)} gauge points in {thames_path.name}")
    print()

    # Fetch river geometry
    river = fetch_thames_geometry()
    if len(river) < 10:
        sys.exit("ERROR: River polyline too short — Overpass query may have failed")

    # Snap each gauge point
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

    # Update thames.py
    new_block = format_gauge_points(snapped)
    new_source = (source[:match.start()]
                  + "GAUGE_POINTS = [\n"
                  + new_block + "\n"
                  + "]"
                  + source[match.end():])

    thames_path.write_text(new_source)
    print(f"\nUpdated {thames_path}")
    print("Run `python app.py port --all --no-backup` to regenerate portfolio with corrected gauges.")


if __name__ == "__main__":
    main()
