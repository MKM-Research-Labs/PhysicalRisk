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

"""Unit tests for the src/routes/commercial/ package (part 4).

Covers the hazard.py ``_attach_fire`` read-time join: the malformed-file
and no-matching-asset early returns plus the success path that folds the
fire model's full-conflagration leg into the asset spread_decomposition.
Catchment-agnostic: all hazard / fire files are synthesised in tmp_path.
"""

import json

import pytest


@pytest.fixture
def cfg_tmp(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    monkeypatch.setattr(config, "get_reports_dir", lambda *a, **k: tmp_path)
    return tmp_path


@pytest.fixture
def client(cfg_tmp):
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


CPID = "CPROP-0001"


def _write_hazard(tmp_path, **asset):
    (tmp_path / "commercialhc.json").write_text(json.dumps({
        "property_hazard_curves": {CPID: dict(asset)}}))


def test_hazard_fire_malformed_json_tolerated(client, cfg_tmp):
    """_attach_fire: corrupt fire/fire.json is swallowed; hazard still serves."""
    _write_hazard(cfg_tmp, flood_count=4)
    fire_dir = cfg_tmp / "fire"
    fire_dir.mkdir()
    (fire_dir / "fire.json").write_text("{not valid json")
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    assert "spread_decomposition" not in resp.get_json()["data"]


def test_hazard_fire_no_matching_asset(client, cfg_tmp):
    """_attach_fire: asset absent from fire.json → no fire fields attached."""
    _write_hazard(cfg_tmp, flood_count=4)
    fire_dir = cfg_tmp / "fire"
    fire_dir.mkdir()
    (fire_dir / "fire.json").write_text(json.dumps({
        "assets": [{"asset_id": "CPROP-9999", "n_sim": 100,
                    "n_point_of_no_return": 5}]}))
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "fire" not in data
    assert "spread_decomposition" not in data


def test_hazard_fire_attached(client, cfg_tmp):
    """_attach_fire: matching asset folds the conflagration leg into the
    spread_decomposition and exposes the raw fire summary."""
    _write_hazard(cfg_tmp, flood_count=4)
    fire_dir = cfg_tmp / "fire"
    fire_dir.mkdir()
    (fire_dir / "fire.json").write_text(json.dumps({"assets": [{
        "asset_id": CPID, "n_sim": 1000, "n_fires": 40,
        "n_point_of_no_return": 20, "n_total": 8,
        "total_loss_frequency": 0.008, "containment_rate": 0.5,
    }]}))
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    # pnr_frequency = 20/1000 = 0.02 → 0.02 * 1.0 * 10000 = 200.0 bps
    sd = data["spread_decomposition"]
    assert sd["fire_spread_bps"] == 200.0
    assert sd["peril_outcomes"]["fire_conflagration"] == {
        "count": 20, "spread_bps": 200.0}
    assert data["fire"]["n_sim"] == 1000
    assert data["fire"]["pnr_frequency"] == 0.02
