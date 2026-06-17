# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Standalone CDM Property Editor — side tool.

A self-contained Flask app for browsing the residential property CDM as a
set of tabs (one per top-level CDM section) with a menu of all properties.
It is schema-driven: the form structure is generated from
``port.cdm.asset.residential.schema.PROPERTY_SCHEMA`` so every field's label,
widget and menu options come straight from the canonical CDM definition.

This is a sandbox tool, kept deliberately isolated from the production scene:
  * It reads/writes ONLY a sandbox copy of the data under
    ``tools/cdm_property_editor/data/property_sandbox.json``.
  * On first run the sandbox is seeded from the golden test fixture
    ``tests/port/cdm/golden/property.json``. The real ``data/`` tree and the
    test fixture itself are never modified.

Run:
    source .venv/bin/activate
    python tools/cdm_property_editor/app.py
    # then open http://127.0.0.1:5057
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# --- Locate the repo and make the CDM schema importable ---------------------
TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parent.parent
SRC_DIR = REPO_ROOT / "src"
# The CDM schema lives under src/, but importing it pulls in the wider `port`
# package whose __init__ chain reaches the top-level `config` package at the
# repo root — so both must be importable.
for _p in (str(SRC_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from port.cdm.asset.residential.schema import PROPERTY_SCHEMA  # noqa: E402

# --- Sandbox data -----------------------------------------------------------
# Seed source: prefer the existing simulated thames portfolio; fall back to the
# golden test fixture if the SSD-mounted data tree is unavailable. The sandbox
# is always a *copy* — edits never write back to data/ or the fixture.
CATCHMENT = "thames"
SEED_CANDIDATES = [
    REPO_ROOT / "data" / "input" / CATCHMENT / "property.json",
    REPO_ROOT / "tests" / "port" / "cdm" / "golden" / "property.json",
]
SANDBOX_DIR = TOOL_DIR / "data"
SANDBOX_FILE = SANDBOX_DIR / "property_sandbox.json"


def _seed_source() -> Path:
    for cand in SEED_CANDIDATES:
        if cand.exists():
            return cand
    raise FileNotFoundError(
        "No seed source found. Tried: "
        + ", ".join(str(c) for c in SEED_CANDIDATES)
        + " (is the data SSD mounted?)"
    )

# The top-level CDM sections, in display order — each becomes a tab.
SECTION_ORDER = list(PROPERTY_SCHEMA.keys())

app = Flask(__name__)
# Preserve the curated CDM key order (schema + records) instead of
# alphabetising it — the section/field order is meaningful.
app.json.sort_keys = False


def _ensure_sandbox() -> None:
    """Seed the sandbox from the simulated portfolio on first run (never overwrite)."""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    if not SANDBOX_FILE.exists():
        shutil.copyfile(_seed_source(), SANDBOX_FILE)


def _load() -> dict:
    _ensure_sandbox()
    with open(SANDBOX_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _properties(doc: dict) -> list:
    """Property records live under 'properties' (fall back to 'portfolio')."""
    return doc.get("properties") or doc.get("portfolio") or []


def _prop_id(prop: dict) -> str:
    return (
        prop.get("PropertyHeader", {}).get("Header", {}).get("PropertyID")
        or prop.get("PropertyHeader", {}).get("Header", {}).get("UPRN")
        or ""
    )


def _summary(prop: dict) -> dict:
    """A compact descriptor used to render the property menu entries."""
    header = prop.get("PropertyHeader", {})
    loc = header.get("Location", {})
    val = header.get("Valuation", {})
    address_bits = [
        loc.get("BuildingNumber"),
        loc.get("StreetName"),
        loc.get("TownCity"),
        loc.get("Postcode"),
    ]
    address = " ".join(str(b) for b in address_bits if b)
    return {
        "id": _prop_id(prop),
        "type": header.get("Header", {}).get("propertyType"),
        "status": header.get("Header", {}).get("propertyStatus"),
        "address": address or "(no address)",
        "value": val.get("PropertyValue"),
    }


# --- Routes -----------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/schema")
def api_schema():
    """The canonical CDM schema plus the tab/section order."""
    return jsonify({"sections": SECTION_ORDER, "schema": PROPERTY_SCHEMA})


@app.route("/api/properties")
def api_properties():
    """Menu data: a lightweight summary of every property in the sandbox."""
    doc = _load()
    return jsonify([_summary(p) for p in _properties(doc)])


@app.route("/api/properties/<pid>")
def api_property(pid: str):
    """Full CDM record for a single property."""
    doc = _load()
    for prop in _properties(doc):
        if _prop_id(prop) == pid:
            return jsonify(prop)
    return jsonify({"error": f"Property '{pid}' not found"}), 404


if __name__ == "__main__":
    _ensure_sandbox()
    print(f"CDM Property Editor — sandbox: {SANDBOX_FILE}")
    print("Open http://127.0.0.1:5057")
    app.run(host="127.0.0.1", port=5057, debug=True)
