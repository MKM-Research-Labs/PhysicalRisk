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

"""Shared fixtures and constants for governance route tests."""

import copy
import json
import pathlib

import pytest


_BASE_MODEL = {
    "model_id": "MKM-TEST-001",
    "name": "Test Model",
    "short_name": "Test",
    "description": "A test model",
    "category": "Hazard",
    "tier": 2,
    "materiality": "Medium",
    "complexity": "Medium",
    "tier_rationale": "Test rationale",
    "status": "Active",
    "lifecycle_stage": "Production",
    "version": "1.0.0",
    "owner": "Test Owner",
    "model_owner_role": "Tester",
    "peer_reviewer": "TBD",
    "source_module": "src/models/test.py",
    "methodology": "Test methodology",
    "validation_status": "Validated",
    "next_review_date": "2027-01-15",
    "last_review_date": "2026-02-01",
    "rag_rating": "Green",
    "mrc_signoff_date": "2026-02-01",
    "recertification_date": "2027-02-01",
    "review_frequency": "Annual",
    "assumptions": [
        {"id": "T-A1", "description": "Test assumption", "impact": "High",
         "monitoring": "Check regularly", "mitigation": "Adjust if needed"},
    ],
    "limitations": [
        {"id": "T-L1", "description": "Test limitation", "impact": "High",
         "monitoring_trigger": "Threshold breach", "compensating_control": "Manual review"},
    ],
    "remediation_steps": [
        {"id": "T-R1", "description": "Fix something", "owner": "Test Owner",
         "priority": "High", "due_date": "2026-06-01", "status": "Open"},
    ],
    "validation_questions": [
        {"question_id": i, "short_label": f"Q{i}", "question": f"Question {i}?",
         "handbook_ref": f"Ch5 Q{i}", "status": "Not Addressed",
         "evidence": "", "last_reviewed": None, "reviewed_by": None}
        for i in range(1, 10)
    ],
    "overall_risk_rating": {
        "calculated_rating": "Not Rated",
        "calculated_score": None,
        "component_scores": {
            "validation_coverage": None, "remediation_health": None,
            "review_currency": None, "assumption_risk": None,
            "limitation_risk": None,
        },
        "effective_rating": "Not Rated",
        "mrc_override": None, "mrc_override_reason": None,
        "mrc_override_date": None, "mrc_override_by": None,
        "last_calculated": None,
    },
    "upstream_models": [],
    "downstream_models": [],
    "test_coverage": {"unit_tests": True, "integration_tests": False,
                      "benchmark_tests": False, "test_file": "tests/test.py"},
    "change_history": [],
    "version_history": [],
    "documents": [],
    "known_failure_modes": [],
    "key_parameters": [],
    "input_data": "",
    "output_data": "",
    "methodology_rationale": "",
    "alternatives_considered": [],
}

_BASE_INVENTORY = {
    "metadata": {
        "framework": "Test Framework",
        "version": "1.0.0",
        "last_updated": "2026-02-18",
        "handbook_reference": "Test Handbook",
        "tiering_methodology": "Test methodology",
    },
    "models": [copy.deepcopy(_BASE_MODEL)],
    "model_chain": {"description": "Test chain", "links": []},
    "tiering_matrix": {"description": "Test matrix", "matrix": {}},
    "audit_trail": [],
}

_BASE_RACI = {
    "metadata": {
        "framework": "Test RACI",
        "version": "1.0.0",
        "last_updated": "2026-02-18",
        "handbook_reference": "Chapter 10",
    },
    "roles": [
        {
            "role_id": "operations_lead",
            "label": "Operations Lead",
            "raci_code": "R",
            "description": "Responsible",
            "assigned_to": "TBD",
            "backup": None,
        },
        {
            "role_id": "model_owner",
            "label": "Model Owner",
            "raci_code": "A",
            "description": "Accountable",
            "assigned_to": "Test Owner",
            "backup": None,
        },
    ],
    "activities": [
        {
            "activity_id": "ACT-01",
            "category": "Production Operations",
            "activity": "Rerun failed jobs",
            "R": "operations_lead",
            "A": "model_owner",
            "C": None,
            "I": None,
            "tier_emphasis": None,
            "notes": "Routine",
        },
    ],
    "escalation_triggers": [
        {
            "trigger_id": "ESC-01",
            "trigger": "Results outside normal ranges",
            "from_role": "operations_lead",
            "to_role": "model_owner",
            "tier_threshold": {"1": "Immediate", "2": "Same day", "3": "Next business day"},
            "response_required": "Investigation",
        },
    ],
}


@pytest.fixture
def governance_env(tmp_path, monkeypatch):
    """Set up isolated governance data files for testing."""
    import routes.governance._constants as gov_constants

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")

    with open(inv_path, "w") as f:
        json.dump(copy.deepcopy(_BASE_INVENTORY), f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)

    return {"inv_path": inv_path, "audit_path": audit_path}


@pytest.fixture
def gov_client(governance_env, monkeypatch):
    """Flask test client with isolated governance data."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir",
                        lambda: pathlib.Path(governance_env["inv_path"]).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def raci_env(governance_env, monkeypatch):
    """Extend governance_env with RACI matrix data."""
    import routes.governance._constants as gov_constants

    raci_path = str(pathlib.Path(governance_env["inv_path"]).parent / "raci_matrix.json")
    with open(raci_path, "w") as f:
        json.dump(copy.deepcopy(_BASE_RACI), f)

    monkeypatch.setattr(gov_constants, "RACI_PATH", raci_path)
    governance_env["raci_path"] = raci_path
    return governance_env


@pytest.fixture
def raci_client(raci_env, monkeypatch):
    """Flask test client with isolated RACI data."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir",
                        lambda: pathlib.Path(raci_env["inv_path"]).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def mrc_env(tmp_path, monkeypatch):
    """Set up isolated MRC meetings data."""
    import routes.governance._constants as gov_constants
    meetings_path = str(tmp_path / "mrc_meetings.json")
    uploads_dir = str(tmp_path / "mrc_uploads")
    with open(meetings_path, "w") as f:
        json.dump([], f)
    monkeypatch.setattr(gov_constants, "MRC_MEETINGS_PATH", meetings_path)
    monkeypatch.setattr(gov_constants, "MRC_UPLOADS_DIR", uploads_dir)
    return {"meetings_path": meetings_path, "uploads_dir": uploads_dir}


@pytest.fixture
def mrc_client(mrc_env, monkeypatch):
    """Flask test client with isolated MRC data."""
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def create_meeting(client, **overrides):
    """Helper: POST to create a meeting and return parsed JSON."""
    data = {"title": "Test MRC Meeting", "date": "2026-03-07", **overrides}
    r = client.post(
        "/api/v1/governance/mrc/meetings",
        json=data,
        content_type="application/json",
    )
    return r, r.get_json()


# ── Lineage fixtures ─────────────────────────────────────────────

@pytest.fixture
def lineage_env(tmp_path, monkeypatch):
    """Set up isolated lineage data files and input directory for testing."""
    import routes.governance._constants as gov_constants

    lineage_path = str(tmp_path / "data_lineage.json")
    field_lineage_path = str(tmp_path / "field_lineage_registry.json")

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")
    with open(inv_path, "w") as f:
        json.dump({"metadata": {}, "models": []}, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(gov_constants, "LINEAGE_PATH", lineage_path)
    monkeypatch.setattr(gov_constants, "FIELD_LINEAGE_PATH", field_lineage_path)

    return {
        "tmp_path": tmp_path,
        "lineage_path": lineage_path,
        "field_lineage_path": field_lineage_path,
    }


@pytest.fixture
def lineage_client(lineage_env, monkeypatch):
    """Flask test client with isolated lineage data."""
    from config import config

    monkeypatch.setattr(
        config, "get_input_dir",
        lambda: pathlib.Path(lineage_env["tmp_path"]),
    )

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


