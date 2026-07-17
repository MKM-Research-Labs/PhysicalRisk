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

"""Smoke tests for the commercial PDF report. (part 2)

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



@pytest.fixture
def app(halong_active):
    from flask import Flask
    from routes import register_blueprints
    a = Flask(__name__)
    register_blueprints(a)
    return a


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
