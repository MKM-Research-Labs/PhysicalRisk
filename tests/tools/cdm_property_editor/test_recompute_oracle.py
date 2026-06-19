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

"""Tests for the recompute oracle check (_recompute_oracle.py).

This is a dev validation script that compares the instant re-depth shortcut
against a real generator re-run. The generator subprocess is stubbed so the
file plumbing — severe counting, property picking, the temp-workspace oracle
(success + no-output error), and the ``main`` comparison loop (all-match and
mismatch exit codes) — runs hermetically with no data tree and no generator.
"""

import json
import types

import pytest


def _ts(events):
    return {"flood_events": events}


# --- _count_severe ----------------------------------------------------------
def test_count_severe(oracle_mod, tmp_path):
    p = tmp_path / "ts.json"
    p.write_text(json.dumps(_ts([
        {"flooded": True, "exceeded_severe": True},
        {"flooded": True, "exceeded_severe": False},
        {"flooded": False, "exceeded_severe": True}])))
    assert oracle_mod._count_severe(p) == 1


# --- _pick_property ---------------------------------------------------------
def test_pick_property_chooses_max_severe(oracle_mod, tmp_path, monkeypatch):
    thames = tmp_path / "thames"
    (thames / "propertyts").mkdir(parents=True)
    prop = {"properties": [
        {"PropertyHeader": {"Header": {"PropertyID": "PROP-A"},
                            "Construction": {"FloorLevelMeters": 1.0}}},
        {"PropertyHeader": {"Header": {"PropertyID": "PROP-B"},
                            "Construction": {"FloorLevelMeters": 2.0}}}]}
    (thames / "property.json").write_text(json.dumps(prop))
    # PROP-A: 0 severe, PROP-B: 2 severe -> B wins
    (thames / "propertyts" / "PROP-A.json").write_text(json.dumps(_ts([
        {"flooded": False, "exceeded_severe": True}])))
    (thames / "propertyts" / "PROP-B.json").write_text(json.dumps(_ts([
        {"flooded": True, "exceeded_severe": True},
        {"flooded": True, "exceeded_severe": True}])))
    monkeypatch.setattr(oracle_mod, "THAMES", thames)
    pid, floor, n = oracle_mod._pick_property()
    assert pid == "PROP-B" and floor == 2.0 and n == 2


# --- _oracle_count ----------------------------------------------------------
def _stub_workspace(oracle_mod, monkeypatch, tmp_path, write_output):
    """Point tempfile.mkdtemp at a known dir and stub the generator subprocess."""
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(oracle_mod.tempfile, "mkdtemp",
                        lambda prefix="": str(work))

    def fake_run(argv, capture_output, text, timeout):
        if write_output:
            out = work / "propertyts"
            out.mkdir(exist_ok=True)
            (out / "PROP-B.json").write_text(json.dumps(_ts([
                {"flooded": True, "exceeded_severe": True}])))
        return types.SimpleNamespace(stderr="boom", stdout="")

    monkeypatch.setattr(oracle_mod.subprocess, "run", fake_run)
    return work


def _thames_with_property(oracle_mod, monkeypatch, tmp_path):
    thames = tmp_path / "thames"
    thames.mkdir()
    (thames / "property.json").write_text(json.dumps({"properties": [
        {"PropertyHeader": {"Header": {"PropertyID": "PROP-B"},
                            "Construction": {"FloorLevelMeters": 2.0}}}]}))
    # one symlink-able input present, the rest absent (exercises the skip)
    (thames / "gauge.json").write_text("{}")
    monkeypatch.setattr(oracle_mod, "THAMES", thames)
    return thames


def test_oracle_count_reads_generated_output(oracle_mod, monkeypatch, tmp_path):
    _thames_with_property(oracle_mod, monkeypatch, tmp_path)
    _stub_workspace(oracle_mod, monkeypatch, tmp_path, write_output=True)
    assert oracle_mod._oracle_count("PROP-B", 2.5) == 1


def test_oracle_count_raises_when_no_output(oracle_mod, monkeypatch, tmp_path):
    _thames_with_property(oracle_mod, monkeypatch, tmp_path)
    _stub_workspace(oracle_mod, monkeypatch, tmp_path, write_output=False)
    with pytest.raises(RuntimeError, match="no output"):
        oracle_mod._oracle_count("PROP-B", 2.5)


# --- main -------------------------------------------------------------------
def _seed_main(oracle_mod, monkeypatch, tmp_path):
    thames = tmp_path / "thames"
    (thames / "propertyts").mkdir(parents=True)
    (thames / "propertyhc.json").write_text(json.dumps(
        {"metadata": {"num_storms": 100}}))
    monkeypatch.setattr(oracle_mod, "THAMES", thames)
    monkeypatch.setattr(oracle_mod, "_pick_property",
                        lambda: ("PROP-B", 2.0, 3))
    (thames / "propertyts" / "PROP-B.json").write_text(json.dumps(_ts([
        {"attenuated_wse_m": 5.0, "flood_depth_m": 1.0,
         "exceeded_severe": True}])))


def test_main_all_match_returns_zero(oracle_mod, monkeypatch, tmp_path, capsys):
    _seed_main(oracle_mod, monkeypatch, tmp_path)
    # oracle agrees with the shortcut on every delta
    monkeypatch.setattr(oracle_mod, "_oracle_count",
                        lambda pid, floor: oracle_mod.recompute.severe_count(
                            json.loads((oracle_mod.THAMES / "propertyts" /
                                        f"{pid}.json").read_text()),
                            round(floor - 2.0, 4)))
    assert oracle_mod.main() == 0
    assert "ALL MATCH" in capsys.readouterr().out


def test_main_mismatch_returns_one(oracle_mod, monkeypatch, tmp_path, capsys):
    _seed_main(oracle_mod, monkeypatch, tmp_path)
    monkeypatch.setattr(oracle_mod, "_oracle_count", lambda pid, floor: 999)
    assert oracle_mod.main() == 1
    assert "MISMATCH" in capsys.readouterr().out
