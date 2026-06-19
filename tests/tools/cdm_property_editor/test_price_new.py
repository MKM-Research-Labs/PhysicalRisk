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

"""Tests for the new-asset scoped-batch pricer (price_new.py).

The real path shells out to a fresh interpreter that re-runs the timeseries +
hazard-curve generators over a 1-asset workspace. Here the subprocess is stubbed
so every branch of ``price_asset`` is exercised — unsupported asset, missing
hazard-curve output, asset absent from the generated curves, timeout, and the
happy path — without running a generator. ``_subprocess_code`` is checked as a
pure string builder.
"""

import json
import subprocess
import types


def test_subprocess_code_contains_modes_and_overrides(price_new_mod, tmp_path):
    cfg = price_new_mod._ASSET["property"]
    code = price_new_mod._subprocess_code(
        tmp_path, cfg, tmp_path / "src", tmp_path / "repo")
    assert "MKM_CATCHMENT_INPUT_OVERRIDE" in code
    assert cfg["ts_cls"] in code and cfg["hc_cls"] in code
    for mode in ("normal", "shd", "she", "bri"):
        assert mode in code
    assert "attach_spread_decomposition" in code


def test_price_asset_unsupported_asset(price_new_mod, tmp_path):
    res = price_new_mod.price_asset(
        "gauge", "G1", {}, input_dir=tmp_path, src_dir=tmp_path,
        repo_root=tmp_path)
    assert res == {"ok": False, "curve": None,
                   "error": "Pricing 'gauge' is not supported."}


def _patch_run(monkeypatch, price_new_mod, side_effect=None, stderr=""):
    """Stub subprocess.run; return a recorder of the workspace it was given."""
    captured = {}

    def fake_run(argv, capture_output, text, timeout):
        if side_effect:
            side_effect(captured)
        return types.SimpleNamespace(stderr=stderr, stdout="")

    monkeypatch.setattr(price_new_mod.subprocess, "run", fake_run)
    return captured


def test_price_asset_no_hazard_curve_output(price_new_mod, monkeypatch, tmp_path):
    # subprocess "runs" but writes no hazard-curve file -> error w/ stderr tail
    _patch_run(monkeypatch, price_new_mod, stderr="boom-traceback")
    res = price_new_mod.price_asset(
        "property", "PROP-1", {"PropertyHeader": {}}, input_dir=tmp_path,
        src_dir=tmp_path, repo_root=tmp_path)
    assert res["ok"] is False and "no hazard curve" in res["error"]
    assert "boom-traceback" in res["error"]


def test_price_asset_id_absent_from_curves(price_new_mod, monkeypatch, tmp_path):
    def write_empty_hc(captured):
        # locate the temp workspace via the records file the function wrote
        import glob
        import os
        import tempfile
        for d in glob.glob(os.path.join(tempfile.gettempdir(), "price_property_*")):
            with open(os.path.join(d, "propertyhc.json"), "w") as fh:
                json.dump({"property_hazard_curves": {}}, fh)

    _patch_run(monkeypatch, price_new_mod, side_effect=write_empty_hc)
    res = price_new_mod.price_asset(
        "property", "PROP-X", {"PropertyHeader": {}}, input_dir=tmp_path,
        src_dir=tmp_path, repo_root=tmp_path)
    assert res["ok"] is False and "not in generated curves" in res["error"]


def test_price_asset_happy_path(price_new_mod, monkeypatch, tmp_path):
    curve = {"flood_zone": "3", "spread_decomposition": {"property_spread_bps": 42}}

    def write_hc(captured):
        import glob
        import os
        import tempfile
        for d in glob.glob(os.path.join(tempfile.gettempdir(), "price_property_*")):
            with open(os.path.join(d, "propertyhc.json"), "w") as fh:
                json.dump({"property_hazard_curves": {"PROP-OK": curve}}, fh)

    _patch_run(monkeypatch, price_new_mod, side_effect=write_hc)
    res = price_new_mod.price_asset(
        "property", "PROP-OK", {"PropertyHeader": {}}, input_dir=tmp_path,
        src_dir=tmp_path, repo_root=tmp_path)
    assert res["ok"] is True and res["error"] is None
    assert res["curve"]["flood_zone"] == "3"


def test_price_asset_timeout(price_new_mod, monkeypatch, tmp_path):
    def boom(argv, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=timeout)

    monkeypatch.setattr(price_new_mod.subprocess, "run", boom)
    res = price_new_mod.price_asset(
        "property", "PROP-1", {"PropertyHeader": {}}, input_dir=tmp_path,
        src_dir=tmp_path, repo_root=tmp_path)
    assert res["ok"] is False and res["error"] == "pricing timed out."


def test_price_asset_symlinks_existing_inputs(price_new_mod, monkeypatch, tmp_path):
    """An existing baseline input is symlinked into the workspace."""
    (tmp_path / "gauge.json").write_text("{}")
    seen = {}

    def record(argv, capture_output, text, timeout):
        # the symlink should exist in the workspace at call time
        import glob
        import os
        import tempfile
        for d in glob.glob(os.path.join(tempfile.gettempdir(), "price_property_*")):
            seen["linked"] = os.path.islink(os.path.join(d, "gauge.json"))
            with open(os.path.join(d, "propertyhc.json"), "w") as fh:
                json.dump({"property_hazard_curves":
                           {"PROP-OK": {"spread_decomposition": {}}}}, fh)
        return types.SimpleNamespace(stderr="", stdout="")

    monkeypatch.setattr(price_new_mod.subprocess, "run", record)
    price_new_mod.price_asset(
        "property", "PROP-OK", {"PropertyHeader": {}}, input_dir=tmp_path,
        src_dir=tmp_path, repo_root=tmp_path)
    assert seen["linked"] is True
