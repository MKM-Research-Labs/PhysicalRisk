# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Shared helpers for ID consistency tests — constants and loader functions.
"""

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
# Catchment-aware: lineage checks run against whichever catchment the rest
# of the stack is pinned to (MKM_CATCHMENT), defaulting to thames. Previously
# this was hardcoded to "thames", so `MKM_CATCHMENT=halong app.py test
# --lineage` silently validated the wrong catchment's data.
CATCHMENT = os.getenv("MKM_CATCHMENT", "thames")
INPUT_DIR = ROOT / "data" / "input" / CATCHMENT
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


# ---------------------------------------------------------------------------
# Additional loaders for expanded lineage tests
# ---------------------------------------------------------------------------

def _catchment_coord_bounds(margin: float = 0.5):
    """Derive (lat_bounds, lon_bounds) for the active catchment.

    Reads ``catch.<MKM_CATCHMENT>.GAUGE_POINTS`` (list of ``(lat, lon, elev)``)
    and returns padded min/max envelopes, so gauge.json coordinates can be
    sanity-checked against the catchment's own gauge definitions. This is
    catchment-agnostic and replaces the previously hardcoded Thames bounds.
    Falls back to global bounds if the catchment module / GAUGE_POINTS is
    unavailable.
    """
    try:
        import importlib
        import sys

        # Catchment params live at data/catch/<id>.py; data/ is added to
        # sys.path by config.path._setup_paths. Trigger it here in case this
        # helper is imported before config (e.g. test collection in isolation).
        data_dir_str = str(ROOT / "data")
        if data_dir_str not in sys.path:
            sys.path.insert(0, data_dir_str)

        mod = importlib.import_module(f"catch.{CATCHMENT}")
        pts = getattr(mod, "GAUGE_POINTS", []) or []
        lats = [p[0] for p in pts]
        lons = [p[1] for p in pts]
        if lats and lons:
            return (
                (min(lats) - margin, max(lats) + margin),
                (min(lons) - margin, max(lons) + margin),
            )
    except Exception:
        pass
    return ((-90.0, 90.0), (-180.0, 180.0))


CATCHMENT_LAT_BOUNDS, CATCHMENT_LON_BOUNDS = _catchment_coord_bounds()


def _load_mortgage_ids() -> set:
    """Load all RLoanIDs from loan.json."""
    path = INPUT_DIR / "loan.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return {
        m.get("RLoan", {}).get("Header", {}).get("RLoanID", "")
        for m in data.get("loans", [])
    } - {""}


def _load_mortgage_property_ids() -> set:
    """Load PropertyIDs referenced by residential loans."""
    path = INPUT_DIR / "loan.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return {
        m.get("RLoan", {}).get("Header", {}).get("PropertyID", "")
        for m in data.get("loans", [])
    } - {""}


def _load_counterparty_ids() -> set:
    """Load all PartyIDs from counterparty.json."""
    path = INPUT_DIR / "counterparty.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return {
        c.get("CounterpartySet", {}).get("Party", {}).get("PartyID", "")
        for c in data.get("counterparties", [])
    } - {""}


def _load_trade_counterparty_ids() -> set:
    """Load CounterParty IDs referenced by open PRS trades."""
    prs_dir = INPUT_DIR / "prs"
    if not prs_dir.exists():
        return set()
    ids = set()
    for f in prs_dir.glob("PRS-*.json"):
        try:
            d = json.load(open(f))
            ps = d.get("PhysicalSwap", {})
            ctpy = ps.get("Header", {}).get("CounterParty", "")
            if ctpy:
                ids.add(ctpy)
        except Exception:
            continue
    return ids


def _load_trade_ids() -> set:
    """Load all SwapIDs from PRS-*.json files."""
    prs_dir = INPUT_DIR / "prs"
    if not prs_dir.exists():
        return set()
    ids = set()
    for f in prs_dir.glob("PRS-*.json"):
        try:
            d = json.load(open(f))
            sid = d.get("PhysicalSwap", {}).get("Header", {}).get("SwapID", "")
            if sid:
                ids.add(sid)
        except Exception:
            continue
    return ids


def _load_market_state_gauge_ids() -> set:
    """Load gauge IDs from blotter/market_state.json hazard_term_structure."""
    path = INPUT_DIR / "blotter" / "market_state.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return set(data.get("hazard_term_structure", {}).keys())


def _load_propertyhc_ids() -> set:
    """Load property IDs from propertyhc.json."""
    path = INPUT_DIR / "propertyhc.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return set(data.get("property_hazard_curves", {}).keys())


def _load_propertyshd_ids() -> set:
    """Load property IDs from propertyshd.json."""
    path = INPUT_DIR / "propertyshd.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return set(data.get("property_hazard_curves", {}).keys())


def _load_propertyshe_ids() -> set:
    """Load property IDs from propertyshe.json."""
    path = INPUT_DIR / "propertyshe.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return set(data.get("property_hazard_curves", {}).keys())
