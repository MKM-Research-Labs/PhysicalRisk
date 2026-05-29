# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Smoke tests for the commercial PDF report.

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
    original = config.catchment_id
    config.catchment_id = "halong"
    yield
    config.catchment_id = original


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


# ---------------------------------------------------------------------------
# /api/v1/commercial/loan-report — loan-focused PDF for the
# "Loan Details" + "Generate Loan Report" menu items.
# ---------------------------------------------------------------------------

def test_generate_loan_report_emits_pdf(first_commercial_id, tmp_path):
    from reports.commercial import generate_cloan_report
    pdf_path = generate_cloan_report(
        property_id=first_commercial_id, output_dir=tmp_path,
    )
    assert pdf_path is not None
    assert pdf_path.exists()
    assert pdf_path.name.startswith("commercial_loan_report_"), (
        f"Filename should be prefixed commercial_loan_report_, got {pdf_path.name}"
    )
    assert pdf_path.read_bytes()[:4] == b"%PDF"
    assert pdf_path.stat().st_size > 2000


def test_generate_loan_report_returns_none_for_unknown_id(halong_active, tmp_path):
    from reports.commercial import generate_cloan_report
    assert generate_cloan_report(
        property_id="CPROP-doesnotexist", output_dir=tmp_path,
    ) is None


def test_loan_report_route_returns_pdf_for_known_id(app, first_commercial_id):
    client = app.test_client()
    r = client.post("/api/v1/commercial/loan-report",
                    json={"propertyId": first_commercial_id})
    assert r.status_code == 200
    payload = r.get_json()
    assert payload["status"] == "success"
    pdf = base64.b64decode(payload["pdf_base64"])
    assert pdf[:4] == b"%PDF"


def test_loan_report_route_alias_works(app, first_commercial_id):
    """/generate_commercial_loan_report alias should mirror the canonical path."""
    client = app.test_client()
    r = client.post("/api/v1/generate_commercial_loan_report",
                    json={"propertyId": first_commercial_id})
    assert r.status_code == 200


def test_loan_report_route_returns_404_for_unknown_id(app):
    client = app.test_client()
    r = client.post("/api/v1/commercial/loan-report",
                    json={"propertyId": "CPROP-doesnotexist"})
    assert r.status_code == 404
    assert "not found" in r.get_json()["message"].lower()


def test_loan_report_route_rejects_missing_property_id(app):
    client = app.test_client()
    r = client.post("/api/v1/commercial/loan-report", json={})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/v1/commercial + /api/v1/commercial-loans — list endpoints used by
# the startup preloader / bottom-left status popup.
# ---------------------------------------------------------------------------

def test_list_commercial_returns_assets(app):
    """GET /api/v1/commercial returns count + commercial_assets list."""
    client = app.test_client()
    r = client.get("/api/v1/commercial")
    assert r.status_code == 200
    payload = r.get_json()
    assert payload["status"] == "success"
    assert "count" in payload
    assert "commercial_assets" in payload
    assert payload["count"] == len(payload["commercial_assets"])
    assert payload["count"] >= 1


def test_list_commercial_loans_returns_loans(app):
    """GET /api/v1/commercial-loans returns count + commercial_loans list."""
    client = app.test_client()
    r = client.get("/api/v1/commercial-loans")
    assert r.status_code == 200
    payload = r.get_json()
    assert payload["status"] == "success"
    assert "count" in payload
    assert "commercial_loans" in payload
    assert payload["count"] == len(payload["commercial_loans"])


def test_list_commercial_does_not_collide_with_per_asset_route(app, first_commercial_id):
    """``/commercial`` (list) and ``/commercial/<id>`` (record) must both
    resolve correctly — different segment counts, but Flask route
    ordering bugs are easy to introduce."""
    client = app.test_client()
    r_list = client.get("/api/v1/commercial")
    r_one = client.get(f"/api/v1/commercial/{first_commercial_id}")
    assert r_list.status_code == 200
    assert r_one.status_code == 200
    assert "commercial_assets" in r_list.get_json()
    assert "property" in r_one.get_json()


# ---------------------------------------------------------------------------
# Error-path coverage for commercial_report.py + generator.py + page modules.
# Each test below targets a specific branch that the happy-path tests don't
# exercise — missing files, broken records, open_pdf wrapper, etc.
# ---------------------------------------------------------------------------

def test_load_commercial_record_returns_none_when_file_missing(
    halong_active, tmp_path,
):
    """``_load_commercial_record`` logs + returns None when
    commercial.json is absent from the catchment dir."""
    from reports.commercial.commercial_report import _load_commercial_record
    assert _load_commercial_record("CPROP-anything", tmp_path) is None


def test_load_loan_record_returns_none_when_file_missing(
    halong_active, tmp_path,
):
    """``_load_cloan_record`` returns None when commercial_loan.json
    is absent (silent — same convention as a missing mortgage on the
    residential side)."""
    from reports.commercial.commercial_report import _load_cloan_record
    assert _load_cloan_record("CPROP-anything", tmp_path) is None


def test_load_loan_record_returns_none_when_id_not_in_file(
    halong_active,
):
    """``_load_cloan_record`` returns None when the file exists but no
    record matches the given PropertyID."""
    from pathlib import Path
    from reports.commercial.commercial_report import _load_cloan_record
    assert _load_cloan_record("CPROP-NOTREAL", Path("data/input/halong")) is None


def test_generate_commercial_report_open_pdf_branch(
    first_commercial_id, tmp_path, monkeypatch,
):
    """When ``open_pdf=True``, the PDF-opener is invoked. We monkeypatch
    open_pdf_file so the test stays headless."""
    calls = []
    import reports.utils.open_pdf as opener
    monkeypatch.setattr(opener, "open_pdf_file", lambda p: calls.append(p))
    from reports.commercial import generate_commercial_report
    path = generate_commercial_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None
    assert calls == [path], f"open_pdf_file was not called once: {calls}"


def test_generate_commercial_report_open_pdf_failure_is_swallowed(
    first_commercial_id, tmp_path, monkeypatch,
):
    """If the PDF opener raises, the function should still return the
    PDF path — the exception is logged at WARNING and absorbed."""
    import reports.utils.open_pdf as opener
    def _boom(_):
        raise RuntimeError("simulated opener failure")
    monkeypatch.setattr(opener, "open_pdf_file", _boom)
    from reports.commercial import generate_commercial_report
    path = generate_commercial_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None  # PDF was still produced


def test_generate_loan_report_returns_none_when_no_linked_loan(
    halong_active, tmp_path, monkeypatch,
):
    """Asset exists but has no commercial-loan record → returns None."""
    from reports.commercial import commercial_report as cr
    # Patch _load_cloan_record to simulate "no loan linked".
    monkeypatch.setattr(cr, "_load_cloan_record", lambda pid, _dir: None)
    # Use a real commercial id so _load_commercial_record finds the asset.
    import json as _json
    with open("data/input/halong/commercial.json") as f:
        pid = _json.load(f)["commercial_assets"][0]["CommercialAsset"]["Header"]["PropertyID"]
    assert cr.generate_cloan_report(pid, output_dir=tmp_path) is None


def test_generate_loan_report_open_pdf_branch(
    first_commercial_id, tmp_path, monkeypatch,
):
    """open_pdf=True path through generate_cloan_report."""
    calls = []
    import reports.utils.open_pdf as opener
    monkeypatch.setattr(opener, "open_pdf_file", lambda p: calls.append(p))
    from reports.commercial import generate_cloan_report
    path = generate_cloan_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None
    assert calls == [path]


def test_generate_loan_report_open_pdf_failure_is_swallowed(
    first_commercial_id, tmp_path, monkeypatch,
):
    import reports.utils.open_pdf as opener
    def _boom(_):
        raise RuntimeError("opener failure")
    monkeypatch.setattr(opener, "open_pdf_file", _boom)
    from reports.commercial import generate_cloan_report
    path = generate_cloan_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None


def test_commercial_generator_default_output_dir(halong_active):
    """``CommercialReportGenerator()`` with no output_dir uses
    config.get_reports_dir('commercial')."""
    from reports.commercial import CommercialReportGenerator
    from config import config as _cfg
    gen = CommercialReportGenerator()  # no output_dir
    assert gen.output_dir == _cfg.get_reports_dir("commercial")


def test_commercial_generator_filename_falls_back_when_no_property_id(tmp_path):
    """``_generate_filename`` handles malformed commercial records by
    falling back to ``unknown`` rather than crashing."""
    from reports.commercial import CommercialReportGenerator
    gen = CommercialReportGenerator(output_dir=tmp_path)
    name = gen._generate_filename({})  # no CommercialAsset key
    assert "unknown" in name
    name2 = gen._generate_filename({}, kind="loan_report")
    assert name2.startswith("commercial_loan_report_unknown_")


def test_loan_overview_page_renders_placeholder_for_no_loan():
    """``CLoanOverviewPage`` emits a 'No loan record linked' placeholder
    paragraph when loan_data is None — the only branch in the page
    not exercised by the happy-path PDF tests."""
    from reports.commercial.pages.loan_overview import CLoanOverviewPage
    from reportlab.platypus import Paragraph
    page = CLoanOverviewPage()
    flowables = page.generate_elements(commercial_data={}, loan_data=None)
    paragraphs = [f for f in flowables if isinstance(f, Paragraph)]
    text_blob = " ".join(p.text for p in paragraphs if hasattr(p, "text"))
    assert "No loan record" in text_blob


def test_asset_base_page_generate_elements_default():
    """``AssetBasePage.generate_elements()`` (called directly, no
    subclass override) returns an empty list — the no-op default."""
    from reports.asset import AssetBasePage
    assert AssetBasePage().generate_elements() == []


def test_commercial_generator_initialize_pages_populated():
    """Smoke check on _initialize_pages — both pages and categories
    dicts are populated immediately after construction."""
    from reports.commercial import CommercialReportGenerator
    gen = CommercialReportGenerator()
    assert len(gen.pages) > 10  # 14 pages registered
    assert "commercial" in gen.categories
    assert "loan" in gen.categories
    assert "loan_overview" in gen.categories["loan"]
