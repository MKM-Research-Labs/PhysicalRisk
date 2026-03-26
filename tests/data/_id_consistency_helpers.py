# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Shared helpers for ID consistency tests — constants and loader functions.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "input" / "thames"
OUTPUT_DIR = ROOT / "data" / "output"


def _load_gauge_ids() -> set:
    """Load all gauge IDs from gauge.json (source of truth)."""
    path = INPUT_DIR / "gauge.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    ids = set()
    for g in data.get("flood_gauges", []):
        fg = g.get("FloodGauge", g)
        gid = fg.get("Header", {}).get("GaugeID", "")
        if gid:
            ids.add(gid)
    return ids


def _load_hazard_curve_ids() -> set:
    """Load all gauge IDs from gaugehc.json."""
    path = INPUT_DIR / "gaugehc.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return set(data.get("hazard_curves", {}).keys())


def _load_trade_gauge_ids() -> set:
    """Load all gauge IDs referenced by open trades."""
    # Trades live in data/input/<catchment>/prs/
    prs_dir = INPUT_DIR / "prs"
    if not prs_dir.exists():
        # Fallback to legacy location
        prs_dir = OUTPUT_DIR / "prs"
    if not prs_dir.exists():
        return set()
    ids = set()
    for f in prs_dir.glob("PRS-*.json"):
        try:
            d = json.load(open(f))
            ps = d.get("PhysicalSwap", {})
            if ps.get("Header", {}).get("TradeStatus") == "Closed":
                continue
            for g in ps.get("GaugeSet", {}).get("GaugeBasket", []):
                gid = g.get("GaugeID", "")
                if gid:
                    ids.add(gid)
        except Exception:
            continue
    return ids


def _load_gaugets_ids() -> set:
    """Load all gauge IDs from gaugets/ directory."""
    gaugets_dir = INPUT_DIR / "gaugets"
    if not gaugets_dir.exists():
        return set()
    ids = set()
    for f in gaugets_dir.glob("GAUGE-*.json"):
        try:
            d = json.load(open(f))
            gid = d.get("gauge_id", "")
            if gid:
                ids.add(gid)
        except Exception:
            continue
    return ids


def _load_property_ids() -> set:
    """Load all property IDs from property.json."""
    path = INPUT_DIR / "property.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    ids = set()
    for p in data.get("properties", []):
        pid = (p.get("PropertyHeader", {})
                .get("Header", {})
                .get("PropertyID", ""))
        if pid:
            ids.add(pid)
    return ids
