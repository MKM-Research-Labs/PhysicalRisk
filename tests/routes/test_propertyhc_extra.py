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

"""Coverage for the hazard-route metadata attach branch and the
/properties/<id>/bri route in src/routes/propertyhc.py."""

import json

import pytest


@pytest.fixture
def cfg_tmp(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def client(cfg_tmp):
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


PID = "PROP-0001"


def test_hazard_attaches_metadata(client, cfg_tmp):
    (cfg_tmp / "propertyhc.json").write_text(json.dumps({
        "property_hazard_curves": {PID: {"flood_count": 5}},
        "metadata": {"terrain_grid": {"cells": 4}, "num_storms": 20000},
    }))
    resp = client.get(f"/api/v1/properties/{PID}/hazard")
    assert resp.status_code == 200
    md = resp.get_json()["data"]["_metadata"]
    assert md["terrain_grid"] == {"cells": 4}
    assert md["num_storms"] == 20000


def test_hazard_no_metadata_block(client, cfg_tmp):
    (cfg_tmp / "propertyhc.json").write_text(json.dumps({
        "property_hazard_curves": {PID: {"flood_count": 5}},
        "metadata": {},
    }))
    resp = client.get(f"/api/v1/properties/{PID}/hazard")
    assert resp.status_code == 200
    assert "_metadata" not in resp.get_json()["data"]


# ---------------------------------------------------------------------------
# /properties/<id>/bri
# ---------------------------------------------------------------------------

def test_bri_options(client):
    resp = client.options(f"/api/v1/properties/{PID}/bri")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_bri_file_missing(client, cfg_tmp):
    resp = client.get(f"/api/v1/properties/{PID}/bri")
    assert resp.status_code == 404
    assert "not yet generated" in resp.get_json()["message"]


def test_bri_property_missing(client, cfg_tmp):
    (cfg_tmp / "propertybri.json").write_text(json.dumps(
        {"property_hazard_curves": {}}))
    resp = client.get(f"/api/v1/properties/{PID}/bri")
    assert resp.status_code == 404
    assert "bri curves" in resp.get_json()["message"]


def test_bri_success(client, cfg_tmp):
    (cfg_tmp / "propertybri.json").write_text(json.dumps(
        {"property_hazard_curves": {PID: {"resilient_flood_count": 2}}}))
    resp = client.get(f"/api/v1/properties/{PID}/bri")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["resilient_flood_count"] == 2
