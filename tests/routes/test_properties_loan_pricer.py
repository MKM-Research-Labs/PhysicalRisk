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

"""Tests for the residential loan-pricer routes in src/routes/properties.py.

Covers GET/POST /properties/<id>/loan-pricer and POST /loan-pricer
(standalone). The loader registry is mocked via the shared prop_client
fixture; compute_loan_pricing / compute_standalone_pricing are monkeypatched
so these tests exercise the HTTP/branching layer only.
"""

import pytest


PROP_ID = "PROP-0001"


# ---------------------------------------------------------------------------
# /properties/<id>/loan-pricer
# ---------------------------------------------------------------------------

def test_loan_pricer_options(prop_client):
    client, _ = prop_client
    r = client.options(f"/api/v1/properties/{PROP_ID}/loan-pricer")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_loan_pricer_no_mortgage_404(prop_client):
    client, reg = prop_client
    reg.get_rloan_loader.return_value.find_by_property_id.return_value = None
    r = client.get(f"/api/v1/properties/{PROP_ID}/loan-pricer")
    assert r.status_code == 404
    assert "No mortgage" in r.get_json()["message"]


def test_loan_pricer_get_success_wraps_rloan(prop_client, monkeypatch):
    client, reg = prop_client
    # loader returns a bare record (no RLoan wrapper) → route wraps it
    reg.get_rloan_loader.return_value.find_by_property_id.return_value = {
        "Header": {"PropertyID": PROP_ID}}
    captured = {}
    import routes._loan_pricing as lp
    def fake(cdm, overrides):
        captured["cdm"] = cdm
        captured["overrides"] = overrides
        return {"price": 100.0}
    monkeypatch.setattr(lp, "compute_loan_pricing", fake)
    r = client.get(f"/api/v1/properties/{PROP_ID}/loan-pricer")
    assert r.status_code == 200
    body = r.get_json()
    assert body["price"] == 100.0
    assert body["property_id"] == PROP_ID
    assert "RLoan" in captured["cdm"]
    assert captured["overrides"] is None


def test_loan_pricer_post_overrides(prop_client, monkeypatch):
    client, reg = prop_client
    reg.get_rloan_loader.return_value.find_by_property_id.return_value = {
        "RLoan": {"Header": {"PropertyID": PROP_ID}}}
    captured = {}
    import routes._loan_pricing as lp
    def fake(cdm, overrides):
        captured["overrides"] = overrides
        return {"price": 1}
    monkeypatch.setattr(lp, "compute_loan_pricing", fake)
    r = client.post(f"/api/v1/properties/{PROP_ID}/loan-pricer",
                    json={"overrides": {"rate": 0.04}})
    assert r.status_code == 200
    assert captured["overrides"] == {"rate": 0.04}


def test_loan_pricer_value_error_422(prop_client, monkeypatch):
    client, reg = prop_client
    reg.get_rloan_loader.return_value.find_by_property_id.return_value = {
        "RLoan": {}}
    import routes._loan_pricing as lp
    monkeypatch.setattr(lp, "compute_loan_pricing",
                        lambda c, o: (_ for _ in ()).throw(ValueError("bad")))
    r = client.get(f"/api/v1/properties/{PROP_ID}/loan-pricer")
    assert r.status_code == 422
    assert "bad" in r.get_json()["message"]


def test_loan_pricer_exception_500(prop_client, monkeypatch):
    client, reg = prop_client
    reg.get_rloan_loader.return_value.find_by_property_id.return_value = {
        "RLoan": {}}
    import routes._loan_pricing as lp
    monkeypatch.setattr(lp, "compute_loan_pricing",
                        lambda c, o: (_ for _ in ()).throw(RuntimeError("x")))
    r = client.get(f"/api/v1/properties/{PROP_ID}/loan-pricer")
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# /loan-pricer (standalone)
# ---------------------------------------------------------------------------

def test_standalone_options(prop_client):
    client, _ = prop_client
    r = client.options("/api/v1/loan-pricer")
    assert r.status_code == 200


def test_standalone_success(prop_client, monkeypatch):
    client, _ = prop_client
    captured = {}
    import routes._loan_pricing as lp
    def fake(inputs, asset_class):
        captured["inputs"] = inputs
        captured["asset_class"] = asset_class
        return {"price": 95.0}
    monkeypatch.setattr(lp, "compute_standalone_pricing", fake)
    r = client.post("/api/v1/loan-pricer",
                    json={"inputs": {"loan_amount": 100, "property_value": 200},
                          "asset_class": "commercial"})
    assert r.status_code == 200
    assert r.get_json()["price"] == 95.0
    assert captured["asset_class"] == "commercial"
    assert captured["inputs"] == {"loan_amount": 100, "property_value": 200}


def test_standalone_bare_body_defaults(prop_client, monkeypatch):
    client, _ = prop_client
    captured = {}
    import routes._loan_pricing as lp
    def fake(inputs, asset_class):
        captured["inputs"] = inputs
        captured["asset_class"] = asset_class
        return {"price": 1}
    monkeypatch.setattr(lp, "compute_standalone_pricing", fake)
    r = client.post("/api/v1/loan-pricer",
                    json={"loan_amount": 50, "property_value": 100})
    assert r.status_code == 200
    # no 'inputs'/'overrides' key → whole body used; default asset_class
    assert captured["inputs"] == {"loan_amount": 50, "property_value": 100}
    assert captured["asset_class"] == "residential"


def test_standalone_value_error_422(prop_client, monkeypatch):
    client, _ = prop_client
    import routes._loan_pricing as lp
    monkeypatch.setattr(lp, "compute_standalone_pricing",
                        lambda i, asset_class: (_ for _ in ()).throw(ValueError("missing")))
    r = client.post("/api/v1/loan-pricer", json={})
    assert r.status_code == 422
    assert "missing" in r.get_json()["message"]


def test_standalone_exception_500(prop_client, monkeypatch):
    client, _ = prop_client
    import routes._loan_pricing as lp
    monkeypatch.setattr(lp, "compute_standalone_pricing",
                        lambda i, asset_class: (_ for _ in ()).throw(RuntimeError("x")))
    r = client.post("/api/v1/loan-pricer", json={})
    assert r.status_code == 500
