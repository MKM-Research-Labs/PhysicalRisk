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
