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

"""
Tests for models.audit — model usage audit trail.

Covers: resolve_model_id, _sanitise_params, log_model_usage,
_get_audit_path.
"""

import json
import os

import pytest


# ===========================================================================
# resolve_model_id
# ===========================================================================

class TestResolveModelId:

    def test_mkm_prefix_returned_as_is(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("MKM-GH-001") == "MKM-GH-001"

    def test_shorthand_gev_resolved(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("gev") == "MKM-GH-001"

    def test_shorthand_prs_resolved(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("prs") == "MKM-PR-001"

    def test_shorthand_intensity_resolved(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("intensity") == "MKM-SI-001"

    def test_shorthand_mortgage_resolved(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("mortgage") == "MKM-MP-001"

    def test_unknown_shorthand_returned_as_is(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("unknown_model") == "unknown_model"

    def test_case_insensitive(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("GEV") == "MKM-GH-001"

    def test_distribution_maps_to_si(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("distribution") == "MKM-SI-001"

    def test_spatial_maps_to_sp(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("spatial") == "MKM-SP-001"

    def test_depth_damage_maps_to_dd(self):
        from models.audit import resolve_model_id
        assert resolve_model_id("depth_damage") == "MKM-DD-001"


# ===========================================================================
# _sanitise_params
# ===========================================================================

class TestSanitiseParams:

    def test_int_passed_through(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"n": 42})
        assert result["n"] == 42

    def test_float_passed_through(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"rate": 0.05})
        assert result["rate"] == 0.05

    def test_string_passed_through(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"name": "test"})
        assert result["name"] == "test"

    def test_bool_passed_through(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"flag": True})
        assert result["flag"] is True

    def test_none_passed_through(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"x": None})
        assert result["x"] is None

    def test_short_list_converted_to_str(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"items": [1, 2, 3]})
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 3

    def test_long_list_summarised(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"items": list(range(15))})
        assert isinstance(result["items"], str)
        assert "15 items" in result["items"]

    def test_tuple_treated_like_list(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({"t": (1, 2, 3)})
        assert isinstance(result["t"], list)

    def test_object_converted_to_string(self):
        from models.audit import _sanitise_params

        class Obj:
            def __str__(self):
                return "my_object"

        result = _sanitise_params({"obj": Obj()})
        assert result["obj"] == "my_object"

    def test_empty_params(self):
        from models.audit import _sanitise_params
        result = _sanitise_params({})
        assert result == {}


# ===========================================================================
# log_model_usage
# ===========================================================================

class TestLogModelUsage:

    def test_creates_audit_file(self, tmp_path, monkeypatch):
        from models import audit as audit_mod
        audit_path = str(tmp_path / "data" / "model_audit_log.json")
        monkeypatch.setattr(audit_mod, "_get_audit_path", lambda: audit_path)
        from models.audit import log_model_usage
        log_model_usage("MKM-GH-001", "gev_fit", parameters={"n": 10})
        assert os.path.exists(audit_path)

    def test_appends_entry(self, tmp_path, monkeypatch):
        from models import audit as audit_mod
        audit_path = str(tmp_path / "data" / "model_audit_log.json")
        monkeypatch.setattr(audit_mod, "_get_audit_path", lambda: audit_path)
        from models.audit import log_model_usage
        log_model_usage("gev", "test_action")
        with open(audit_path) as f:
            entries = json.load(f)
        assert len(entries) == 1
        assert entries[0]["action"] == "test_action"
        assert entries[0]["model_id"] == "MKM-GH-001"

    def test_multiple_calls_accumulate(self, tmp_path, monkeypatch):
        from models import audit as audit_mod
        audit_path = str(tmp_path / "data" / "model_audit_log.json")
        monkeypatch.setattr(audit_mod, "_get_audit_path", lambda: audit_path)
        from models.audit import log_model_usage
        log_model_usage("gev", "action1")
        log_model_usage("prs", "action2")
        with open(audit_path) as f:
            entries = json.load(f)
        assert len(entries) == 2

    def test_entry_has_required_keys(self, tmp_path, monkeypatch):
        from models import audit as audit_mod
        audit_path = str(tmp_path / "data" / "model_audit_log.json")
        monkeypatch.setattr(audit_mod, "_get_audit_path", lambda: audit_path)
        from models.audit import log_model_usage
        log_model_usage("prs", "test", parameters={"k": "v"},
                        context="unit test", user="tester")
        with open(audit_path) as f:
            entry = json.load(f)[0]
        assert "timestamp" in entry
        assert "model_id" in entry
        assert "event_type" in entry
        assert entry["user"] == "tester"
        assert entry["context"] == "unit test"

    def test_bad_audit_path_does_not_raise(self, monkeypatch):
        """Failures in audit logging must not propagate."""
        from models import audit as audit_mod
        monkeypatch.setattr(audit_mod, "_get_audit_path",
                            lambda: "/nonexistent_dir/file.json")
        from models.audit import log_model_usage
        # Should NOT raise
        log_model_usage("gev", "test_action")

    def test_existing_file_appended(self, tmp_path, monkeypatch):
        from models import audit as audit_mod
        audit_path = str(tmp_path / "data" / "model_audit_log.json")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "w") as f:
            json.dump([{"existing": "entry"}], f)
        monkeypatch.setattr(audit_mod, "_get_audit_path", lambda: audit_path)
        from models.audit import log_model_usage
        log_model_usage("prs", "action")
        with open(audit_path) as f:
            entries = json.load(f)
        assert len(entries) == 2
        assert "existing" in entries[0]

    def test_corrupted_file_restarted(self, tmp_path, monkeypatch):
        """Corrupted audit log → start fresh, don't raise."""
        from models import audit as audit_mod
        audit_path = str(tmp_path / "data" / "model_audit_log.json")
        os.makedirs(os.path.dirname(audit_path), exist_ok=True)
        with open(audit_path, "w") as f:
            f.write("not json {{}")
        monkeypatch.setattr(audit_mod, "_get_audit_path", lambda: audit_path)
        from models.audit import log_model_usage
        log_model_usage("gev", "test")
        with open(audit_path) as f:
            entries = json.load(f)
        assert len(entries) == 1
