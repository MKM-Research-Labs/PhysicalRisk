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

"""Unit tests for the src/routes/commercial/ package (part 5).

Covers the hazard.py ``_attach_seismic`` read-time join: the malformed-file and
no-matching-asset early returns, the success path that folds the seismic
model's full-collapse (DS3) leg into the asset spread_decomposition, and the
fire+seismic co-existence (both independent legs attach side by side).
Catchment-agnostic: all hazard / seismic files are synthesised in tmp_path.
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


def _write_seismic(tmp_path, **asset):
    seismic_dir = tmp_path / "seismic"
    seismic_dir.mkdir(exist_ok=True)
    (seismic_dir / "seismic.json").write_text(json.dumps({"assets": [asset]}))


def _seismic_record(**overrides):
    base = dict(
        asset_id=CPID, n_sim=10000, n_events=800,
        seismic_spread_bps=12.5,
        damage_state_counts={"0": 100, "1": 300, "2": 387, "3": 13},
        no_collapse_rate=0.984, loss_frequency=0.003, rating="NR",
        zone="High", site_class="B", pml_475=0.4, pml_2475=0.9,
        mean_resilience_index=0.7, n_cascade_fire=2,
    )
    base.update(overrides)
    return base


def test_hazard_seismic_malformed_json_tolerated(client, cfg_tmp):
    """_attach_seismic: corrupt seismic.json is swallowed; hazard still serves."""
    _write_hazard(cfg_tmp, flood_count=4)
    seismic_dir = cfg_tmp / "seismic"
    seismic_dir.mkdir()
    (seismic_dir / "seismic.json").write_text("{not valid json")
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    assert "spread_decomposition" not in resp.get_json()["data"]


def test_hazard_seismic_no_matching_asset(client, cfg_tmp):
    """_attach_seismic: asset absent from seismic.json → no seismic fields."""
    _write_hazard(cfg_tmp, flood_count=4)
    _write_seismic(cfg_tmp, **_seismic_record(asset_id="CPROP-9999"))
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "seismic" not in data
    assert "spread_decomposition" not in data


def test_hazard_seismic_missing_spread_is_noop(client, cfg_tmp):
    """_attach_seismic: a record without seismic_spread_bps attaches nothing."""
    _write_hazard(cfg_tmp, flood_count=4)
    rec = _seismic_record()
    rec.pop("seismic_spread_bps")
    _write_seismic(cfg_tmp, **rec)
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    assert "seismic" not in resp.get_json()["data"]


def test_hazard_seismic_attached(client, cfg_tmp):
    """_attach_seismic: matching asset folds the collapse leg into the
    spread_decomposition and exposes the raw seismic summary."""
    _write_hazard(cfg_tmp, flood_count=4)
    _write_seismic(cfg_tmp, **_seismic_record())
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    sd = data["spread_decomposition"]
    assert sd["seismic_spread_bps"] == 12.5
    assert sd["peril_outcomes"]["seismic"] == {"count": 13, "spread_bps": 12.5}
    assert data["seismic"]["zone"] == "High"
    assert data["seismic"]["rating"] == "NR"
    assert data["seismic"]["n_events"] == 800
    assert data["seismic"]["pml_2475"] == 0.9


def test_hazard_fire_and_seismic_coexist(client, cfg_tmp):
    """Both independent legs attach to the same spread_decomposition."""
    _write_hazard(cfg_tmp, flood_count=4)
    fire_dir = cfg_tmp / "fire"
    fire_dir.mkdir()
    (fire_dir / "fire.json").write_text(json.dumps({"assets": [{
        "asset_id": CPID, "n_sim": 1000, "n_point_of_no_return": 20,
    }]}))
    _write_seismic(cfg_tmp, **_seismic_record())
    resp = client.get(f"/api/v1/commercial/{CPID}/hazard")
    assert resp.status_code == 200
    sd = resp.get_json()["data"]["spread_decomposition"]
    assert sd["fire_spread_bps"] == 200.0
    assert sd["seismic_spread_bps"] == 12.5
    assert set(sd["peril_outcomes"]) == {"fire_conflagration", "seismic"}
