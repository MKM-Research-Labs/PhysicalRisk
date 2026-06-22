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

"""Smoke tests for the commercial PDF report. (part 1)

Covers the round trip we built in Phase A:
  - asset/ shared section renderers produce flowables against real data
  - CommercialReportGenerator emits a valid PDF that includes the
    commercial-only sections (CommercialAttributes, AccessibilityFeatures,
    Tenancy, LoanOverview)
  - the Flask route returns 200 with a base64 PDF for a real PropertyID
    and 404 for an unknown one.
"""

import base64
import json
from pathlib import Path

import pytest

from config import config


@pytest.fixture
def halong_active():
    """Switch to halong for these tests; restore at teardown."""
    with config.use_catchment("halong"):
        yield


@pytest.fixture
def first_commercial_id(halong_active):
    with open("data/input/halong/commercial.json") as f:
        data = json.load(f)
    return data["commercial_assets"][0]["CommercialAsset"]["Header"]["PropertyID"]


# ---------------------------------------------------------------------------
# Shared section renderers
# ---------------------------------------------------------------------------

def test_asset_renderers_produce_flowables_for_real_record(halong_active):
    from reports.asset import (
        AssetBasePage, render_header, render_location, render_construction,
        render_risk_assessment, render_valuation, render_energy,
        render_protection, render_history, render_transactions,
    )
    with open("data/input/halong/commercial.json") as f:
        rec = json.load(f)["commercial_assets"][0]
    asset = rec["CommercialAsset"]

    class _Page(AssetBasePage):
        pass
    page = _Page()

    # Every shared section produces at least the section header paragraph.
    assert len(render_header(asset["Header"], page)) > 0
    assert len(render_location(asset["Location"], page)) > 0
    assert len(render_construction(asset["Construction"], page)) > 0
    assert len(render_risk_assessment(asset["RiskAssessment"], page)) > 0
    assert len(render_valuation(asset["Valuation"], page)) > 0
    assert len(render_energy(rec["EnergyPerformance"], page)) > 0
    assert len(render_protection(rec["ProtectionMeasures"], page)) > 0
    assert len(render_history(rec["HistoryAndIncidents"], page)) > 0
    assert len(render_transactions(rec["TransactionHistory"], page)) > 0


# ---------------------------------------------------------------------------
# End-to-end PDF generation
# ---------------------------------------------------------------------------

def test_generator_emits_valid_pdf(first_commercial_id, tmp_path):
    from reports.commercial import generate_commercial_report

    pdf_path = generate_commercial_report(
        property_id=first_commercial_id,
        output_dir=tmp_path,
    )
    assert pdf_path is not None
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 5000, "PDF suspiciously small"
    # PDF magic number.
    assert pdf_path.read_bytes()[:4] == b"%PDF"


def test_generator_returns_none_for_unknown_id(halong_active, tmp_path):
    from reports.commercial import generate_commercial_report
    assert generate_commercial_report(
        property_id="CPROP-doesnotexist", output_dir=tmp_path,
    ) is None


# ---------------------------------------------------------------------------
# Flask route
# ---------------------------------------------------------------------------

@pytest.fixture
def app(halong_active):
    from flask import Flask
    from routes import register_blueprints
    a = Flask(__name__)
    register_blueprints(a)
    return a


def test_route_returns_pdf_for_known_id(app, first_commercial_id):
    client = app.test_client()
    r = client.post("/api/v1/commercial/report",
                    json={"propertyId": first_commercial_id})
    assert r.status_code == 200
    payload = r.get_json()
    assert payload["status"] == "success"
    pdf = base64.b64decode(payload["pdf_base64"])
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000


def test_route_alias_works(app, first_commercial_id):
    """The /generate_commercial_report alias should match /commercial/report."""
    client = app.test_client()
    r = client.post("/api/v1/generate_commercial_report",
                    json={"propertyId": first_commercial_id})
    assert r.status_code == 200


def test_route_returns_404_for_unknown_id(app):
    client = app.test_client()
    r = client.post("/api/v1/commercial/report",
                    json={"propertyId": "CPROP-doesnotexist"})
    assert r.status_code == 404


def test_route_rejects_missing_property_id(app):
    client = app.test_client()
    r = client.post("/api/v1/commercial/report", json={})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/v1/commercial/<id>/storms — storm-scenarios endpoint
# ---------------------------------------------------------------------------

def test_storms_route_returns_expected_shape(app, first_commercial_id):
    client = app.test_client()
    r = client.get(f"/api/v1/commercial/{first_commercial_id}/storms")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "success"
    assert data["property_id"] == first_commercial_id
    # Same shape as /properties/<id>/storms so the frontend panel works
    # against either endpoint without branching.
    for key in (
        "property_address", "property_info", "nearest_gauges",
        "flood_events", "summary",
    ):
        assert key in data, f"Missing key: {key}"
    assert isinstance(data["nearest_gauges"], list)
    assert isinstance(data["flood_events"], list)
    assert "severe_at_nearest_gauge" in data["summary"]


def test_storms_route_enriches_flood_events(app, first_commercial_id):
    """Each flood_event should be tagged with sequence_type + metadata."""
    client = app.test_client()
    r = client.get(f"/api/v1/commercial/{first_commercial_id}/storms")
    events = r.get_json()["flood_events"]
    if not events:
        pytest.skip("No flood events for this asset")
    sample = events[0]
    # sequence_type comes from storm_sequences.json enrichment.
    assert "sequence_type" in sample
    # gauges_severe comes from stress_storms enrichment.
    assert "gauges_severe" in sample


def test_storms_route_returns_404_for_unknown_id(app):
    client = app.test_client()
    r = client.get("/api/v1/commercial/CPROP-doesnotexist/storms")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# /api/v1/commercial/<id>/{hazard,she,shd} + base record
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("subpath", ["hazard", "she", "shd"])
def test_hazard_routes_return_data_payload(app, first_commercial_id, subpath):
    client = app.test_client()
    r = client.get(f"/api/v1/commercial/{first_commercial_id}/{subpath}")
    assert r.status_code == 200, f"{subpath}: {r.status_code}"
    payload = r.get_json()
    assert payload["status"] == "success"
    assert "data" in payload
    assert "flood_count" in payload["data"], f"{subpath} missing flood_count"


def test_hazard_attaches_terrain_grid_metadata(app, first_commercial_id):
    """/hazard should embed _metadata.terrain_grid when present in commercialhc."""
    client = app.test_client()
    r = client.get(f"/api/v1/commercial/{first_commercial_id}/hazard")
    data = r.get_json()["data"]
    if "_metadata" in data:
        assert "terrain_grid" in data["_metadata"]


@pytest.mark.parametrize("subpath", ["hazard", "she", "shd"])
def test_hazard_routes_return_404_for_unknown_id(app, subpath):
    client = app.test_client()
    r = client.get(f"/api/v1/commercial/CPROP-doesnotexist/{subpath}")
    assert r.status_code == 404


def test_base_record_route_returns_full_record(app, first_commercial_id):
    """GET /api/v1/commercial/<id> returns the bare record by PropertyID."""
    client = app.test_client()
    r = client.get(f"/api/v1/commercial/{first_commercial_id}")
    assert r.status_code == 200
    payload = r.get_json()
    assert payload["status"] == "success"
    record = payload["property"]
    assert "CommercialAsset" in record
    assert record["CommercialAsset"]["Header"]["PropertyID"] == first_commercial_id


def test_base_record_route_returns_404_for_unknown_id(app):
    client = app.test_client()
    r = client.get("/api/v1/commercial/CPROP-doesnotexist")
    assert r.status_code == 404
