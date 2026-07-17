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

"""
Generate worked examples for the property hazard decomposition document.

Picks two random properties (one Zone 3a/3b, one Zone 2/1) and prints
the full diagnostic tables ready to paste into the LaTeX document.

Usage:
    python docs/models/prs_pricing/generate_decomposition_examples.py
"""

import json
import math
import random
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from config import config
from models.floodrisk.spatial import haversine_distance


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    base = config.get_input_root() / "thames"
    gauge_data = load(f"{base}/gauge.json")
    prop_data = load(f"{base}/property.json")
    hc_data = load(f"{base}/propertyhc.json")
    shd_data = load(f"{base}/propertyshd.json")
    she_data = load(f"{base}/propertyshe.json")

    hc_curves = hc_data.get("property_hazard_curves", {})
    shd_curves = shd_data.get("property_hazard_curves", {})
    she_curves = she_data.get("property_hazard_curves", {})

    # Build synthetic lookup
    synth_lookup = {}
    for g in gauge_data["flood_gauges"]:
        gid = g["FloodGauge"]["Header"]["GaugeID"]
        if gid.startswith("SYNTH"):
            loc = g["FloodGauge"]["Location"]
            synth_lookup[gid] = {
                "lat": loc["GaugeLatitude"],
                "lon": loc["GaugeLongitude"],
                "elev": loc["GaugeElevation"],
            }

    # Collect properties with full data
    candidates = {"high": [], "low": []}
    for p in prop_data["properties"]:
        ph = p["PropertyHeader"]
        pid = ph["Header"]["PropertyID"]
        zone = ph.get("RiskAssessment", {}).get("EAFloodZone", "?")
        refs = ph.get("ReferenceGauges", [])

        if pid not in hc_curves:
            continue
        pc = hc_curves[pid]
        if not pc.get("spread_decomposition"):
            continue
        if not refs or not refs[0].startswith("SYNTH"):
            continue

        bucket = "high" if zone in ("Zone 3b", "Zone 3a") else "low"
        candidates[bucket].append((p, pc))

    # Pick one from each bucket
    picks = []
    for bucket in ["high", "low"]:
        if candidates[bucket]:
            picks.append(random.choice(candidates[bucket]))

    for label, (prop, pc) in zip(["A", "B"], picks):
        ph = prop["PropertyHeader"]
        pid = ph["Header"]["PropertyID"]
        zone = ph.get("RiskAssessment", {}).get("EAFloodZone", "?")
        refs = ph.get("ReferenceGauges", [])
        synth_id = refs[0]
        sg = synth_lookup.get(synth_id, {})

        plat = ph["Location"]["LatitudeDegrees"]
        plon = ph["Location"]["LongitudeDegrees"]
        pelev = ph.get("RiskAssessment", {}).get("GroundLevelMeters", 0)
        floor = prop.get("PropertyHeader", {}).get("Construction", {}).get("FloorLevelMeters", 0)
        dist = haversine_distance(plat, plon, sg.get("lat", 0), sg.get("lon", 0))
        offset = pelev - sg.get("elev", 0)
        threshold = offset + floor

        shd_pc = shd_curves.get(pid, {})
        she_pc = she_curves.get(pid, {})

        sd = pc.get("spread_decomposition", {})

        print(f"\n{'='*70}")
        print(f"Property {label}: {pid}")
        print(f"{'='*70}")

        print(f"\n--- Spatial Context ---")
        print(f"  Property ID:         {pid}")
        print(f"  EA Flood Zone:       {zone}")
        print(f"  Synthetic Gauge:     {synth_id}")
        print(f"  Distance to Synth:   {dist:.0f} m")
        print(f"  Property Elevation:  {pelev:.2f} m AOD")
        print(f"  Synthetic Elevation: {sg.get('elev', 0):.2f} m AOD")
        print(f"  Offset Above Synth:  {offset:.2f} m")
        print(f"  Floor Level:         {floor:.2f} m")
        print(f"  Flood Threshold:     {threshold:.2f} m")

        print(f"\n--- Flood Simulation (storms / floods / rate / max depth) ---")
        for mode_label, mode_pc in [
            ("Normal", pc),
            ("SHD", shd_pc),
            ("SHE", she_pc),
        ]:
            fc = mode_pc.get("flood_count", 0)
            gev = mode_pc.get("gev_params", {})
            # Estimate total storms from nearest gauge
            ngs = mode_pc.get("nearest_gauges", [])
            gauge_floods = ngs[0].get("gauge_flood_count", 0) if ngs else 0
            print(f"  {mode_label:8s}: floods={fc:>5}  "
                  f"gauge_floods={gauge_floods:>5}  "
                  f"rate={fc/20000*100:.2f}%  "
                  f"GEV(xi={gev.get('shape', '—')}, "
                  f"mu={gev.get('loc', '—')}, "
                  f"sig={gev.get('scale', '—')})")

        print(f"\n--- Annual Probabilities & 5yr Spreads ---")
        print(f"  {'Threshold':12s} {'Normal':>12} {'SHD':>12} {'SHE':>12} {'Gauge':>12}")
        for trigger in ["any_flood", "severe"]:
            vals = []
            for mode_pc in [pc, shd_pc, she_pc]:
                dt = mode_pc.get("depth_thresholds", {}).get(trigger, {})
                ts = mode_pc.get("term_structure", {}).get(trigger, {})
                prob = dt.get("annual_probability", 0)
                spreads = ts.get("prs_spread_bps", [])
                s5 = spreads[4] if len(spreads) > 4 else 0
                vals.append(f"{prob:.6f}/{s5:.1f}")
            # Gauge spread from decomposition
            gs = sd.get("gauge_spread_bps", 0)
            vals.append(f"—/{gs:.1f}")
            print(f"  {trigger:12s} {vals[0]:>12} {vals[1]:>12} {vals[2]:>12} {vals[3]:>12}")

        print(f"\n--- Spread Decomposition Waterfall (severe, 5yr) ---")
        gs = sd.get("gauge_spread_bps", 0)
        ps = sd.get("property_spread_bps", 0)
        shd_s = sd.get("shd_spread_bps", 0)
        she_s = sd.get("she_spread_bps", 0)
        df = sd.get("distance_first", {})
        ef = sd.get("elevation_first", {})

        print(f"  Gauge Spread:        {gs:>8.1f} bp  (baseline)")
        print(f"  Path 1: Distance First")
        print(f"    Distance Effect:   {df.get('distance_effect_bps', 0):>+8.1f} bp  (SHE={she_s:.1f}bp)")
        print(f"    Elevation Effect:  {df.get('elevation_effect_bps', 0):>+8.1f} bp  -> property")
        print(f"  Path 2: Elevation First")
        print(f"    Elevation Effect:  {ef.get('elevation_effect_bps', 0):>+8.1f} bp  (SHD={shd_s:.1f}bp)")
        print(f"    Distance Effect:   {ef.get('distance_effect_bps', 0):>+8.1f} bp  -> property")
        print(f"  Property Spread:     {ps:>8.1f} bp")
        print(f"  Total Basis:         {gs - ps:>+8.1f} bp")

        # Peril outcomes fan (Stage 6/7) — only present for catchments whose
        # typhoon stage has run. The flood spine fans into the four PRS peril
        # outcomes at the property/BRI node (inclusion-exclusion holds:
        # union = flood + wind - joint).
        po = sd.get("peril_outcomes") or pc.get("prs_perils")
        if po:
            def _po(key):
                o = po.get(key, {}) or {}
                return o.get("count", 0), o.get("spread_bps", 0.0)

            f_c, f_s = _po("flood_only")
            w_c, w_s = _po("wind_only")
            u_c, u_s = _po("flood_or_wind")
            j_c, j_s = _po("flood_and_wind")
            print(f"\n--- Peril Outcomes (property node, count / 5yr spread) ---")
            print(f"  Flood only:          {f_c:>5}  {f_s:>8.1f} bp")
            print(f"  Wind only:           {w_c:>5}  {w_s:>8.1f} bp")
            print(f"  Flood OR Wind:       {u_c:>5}  {u_s:>8.1f} bp  (headline PRS)")
            print(f"  Flood AND Wind:      {j_c:>5}  {j_s:>8.1f} bp")
            print(f"  Inclusion-exclusion: union {u_c} == flood {f_c} + wind {w_c} - joint {j_c}"
                  f"  [{'OK' if u_c == f_c + w_c - j_c else 'MISMATCH'}]")


if __name__ == "__main__":
    main()
