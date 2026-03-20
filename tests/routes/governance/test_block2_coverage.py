# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for Block 2 governance route files.

Targets missing lines in:
- src/routes/governance/mrc.py (lines 108,144,164-186,196)
- src/routes/governance/audit.py (lines 57,82,85,130,176,196,210,248,282,
  301,320-325,335-339,347,357)
"""

import io
import json
import os
from unittest.mock import patch

import pytest

from tests.routes.governance.conftest import create_meeting


# ---------------------------------------------------------------------------
# mrc.py — save failures + document upload/serve (lines 108,144,164-186,196)
# ---------------------------------------------------------------------------

class TestMrcCreateSaveFailure:

    def test_create_meeting_save_failure(self, mrc_client, mrc_env):
        """Line 108: _save_meetings fails → 500."""
        with patch("routes.governance.mrc._save_meetings", return_value=False):
            r = mrc_client.post("/api/v1/governance/mrc/meetings",
                                json={"title": "Failing"})
            assert r.status_code == 500
            assert "Failed" in r.get_json()["message"]


class TestMrcUpdateSaveFailure:

    def test_update_meeting_save_failure(self, mrc_client, mrc_env):
        """Line 144: _save_meetings fails on update → 500."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        with patch("routes.governance.mrc._save_meetings", return_value=False):
            r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/update",
                                json={"title": "Updated"})
            assert r.status_code == 500


class TestMrcDocumentUpload:

    def test_upload_document_success(self, mrc_client, mrc_env):
        """Lines 164-186: upload a file to a meeting."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {
            "file": (io.BytesIO(b"test content"), "report.pdf"),
            "user": "Tester",
            "description": "Test doc",
        }
        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 200
        doc = r.get_json()["document"]
        assert doc["filename"] == "report.pdf"

    def test_upload_document_meeting_not_found(self, mrc_client, mrc_env):
        """Line 155: meeting not found → 404."""
        data = {"file": (io.BytesIO(b"x"), "f.pdf")}
        r = mrc_client.post("/api/v1/governance/mrc/meetings/nonexistent/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 404

    def test_upload_document_no_file(self, mrc_client, mrc_env):
        """Line 158: no file in request → 400."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data={}, content_type="multipart/form-data")
        assert r.status_code == 400

    def test_upload_document_empty_filename(self, mrc_client, mrc_env):
        """Line 162: file with empty filename → 400."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {"file": (io.BytesIO(b"x"), "")}
        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 400

    def test_upload_document_save_failure(self, mrc_client, mrc_env):
        """Line 184: save failure after upload → 500."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {"file": (io.BytesIO(b"x"), "f.pdf")}
        with patch("routes.governance.mrc._save_meetings", return_value=False):
            r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                                data=data, content_type="multipart/form-data")
            assert r.status_code == 500


class TestMrcDocumentUploadNoDocsKey:

    def test_upload_creates_documents_list(self, mrc_client, mrc_env):
        """Line 179: meeting without 'documents' key gets it created."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        # Manually remove the documents key from the stored meeting
        import json
        with open(mrc_env["meetings_path"]) as f:
            meetings = json.load(f)
        del meetings[-1]["documents"]
        with open(mrc_env["meetings_path"], "w") as f:
            json.dump(meetings, f)

        data = {"file": (io.BytesIO(b"test"), "doc.pdf")}
        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 200


class TestMrcDocumentServe:

    def test_get_meeting_document_success(self, mrc_client, mrc_env):
        """Line 196: serve an uploaded document."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {"file": (io.BytesIO(b"PDF content"), "report.pdf")}
        mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                        data=data, content_type="multipart/form-data")

        r = mrc_client.get(f"/api/v1/governance/mrc/meetings/{mid}/documents/report.pdf")
        assert r.status_code == 200

    def test_get_meeting_document_not_found(self, mrc_client, mrc_env):
        """Line 195: document file not found → 404."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        r = mrc_client.get(f"/api/v1/governance/mrc/meetings/{mid}/documents/nonexistent.pdf")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# audit.py — missing edge cases and PDF serving
# ---------------------------------------------------------------------------

class TestAuditLogEdgeCases:

    def test_log_model_usage_inventory_not_found(self, gov_client, governance_env):
        """Line 57: inventory file empty/missing → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "usage"})
        assert r.status_code == 404

    def test_log_model_usage_audit_overflow_trim(self, gov_client, governance_env):
        """Line 82: audit log > 10000 entries gets trimmed."""
        big_log = [{"model_id": "X", "event_type": "usage"} for _ in range(10001)]
        with open(governance_env["audit_path"], "w") as f:
            json.dump(big_log, f)

        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "test"})
        assert r.status_code == 200

        with open(governance_env["audit_path"]) as f:
            log = json.load(f)
        assert len(log) <= 10000

    def test_log_model_usage_save_failure(self, gov_client, governance_env):
        """Line 85: save failure → 500."""
        with patch("routes.governance.audit._save_audit_log", return_value=False):
            r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                                json={"event_type": "usage"})
            assert r.status_code == 500


class TestValidationQuestionEdgeCases:

    def test_update_vq_inventory_not_found(self, gov_client, governance_env):
        """Line 130: inventory not found → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={"status": "Addressed", "evidence": "e", "reviewed_by": "u"})
        assert r.status_code == 404

    def test_update_vq_save_failure(self, gov_client, governance_env):
        """Line 176: save failure → 500."""
        with patch("routes.governance.audit._save_inventory", return_value=False):
            r = gov_client.post(
                "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
                json={"status": "Addressed", "evidence": "test", "reviewed_by": "u"})
            assert r.status_code == 500

    def test_update_vq_audit_overflow(self, gov_client, governance_env):
        """Line 196: audit log overflow during VQ update."""
        big_log = [{"model_id": "X"} for _ in range(10001)]
        with open(governance_env["audit_path"], "w") as f:
            json.dump(big_log, f)

        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={"status": "Addressed", "evidence": "e", "reviewed_by": "u"})
        assert r.status_code == 200


class TestRiskRatingEdgeCases:

    def test_get_risk_rating_inventory_not_found(self, gov_client, governance_env):
        """Line 210: inventory not found → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        assert r.status_code == 404


class TestOverrideRiskRatingEdgeCases:

    def test_override_inventory_not_found(self, gov_client, governance_env):
        """Line 248: inventory not found → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
                            json={"rating": "Acceptable", "reason": "test", "user": "u"})
        assert r.status_code == 404

    def test_override_save_failure(self, gov_client, governance_env):
        """Line 282: save failure → 500."""
        with patch("routes.governance.audit._save_inventory", return_value=False):
            r = gov_client.post(
                "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
                json={"rating": "Acceptable", "reason": "test reason", "user": "u"})
            assert r.status_code == 500

    def test_override_audit_overflow(self, gov_client, governance_env):
        """Line 301: audit overflow during override."""
        big_log = [{"model_id": "X"} for _ in range(10001)]
        with open(governance_env["audit_path"], "w") as f:
            json.dump(big_log, f)

        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": "Conditional", "reason": "test reason", "user": "u"})
        assert r.status_code == 200


class TestPdfServing:

    def test_model_doc_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 325: model documentation PDF served when file exists."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()
        pdf_file = doc_dir / "gev_hazard.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/documentation/pdf")
        assert r.status_code == 200

    def test_model_doc_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 323: valid model dir but PDF file missing → 404."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()  # dir exists but no PDF inside

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/documentation/pdf")
        assert r.status_code == 404
        assert "not found" in r.get_json()["message"].lower()

    def test_test_results_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 339: test results PDF served when file exists."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()
        pdf_file = doc_dir / "test_results.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/test-results/pdf")
        assert r.status_code == 200

    def test_test_results_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 337: valid model dir but test_results.pdf missing → 404."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/test-results/pdf")
        assert r.status_code == 404

    def test_parameter_inventory_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 349: parameter inventory PDF served."""
        import routes.governance._constants as gc

        pi_dir = tmp_path / "parameter_inventory"
        pi_dir.mkdir()
        pdf_file = pi_dir / "parameter_inventory.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/parameter-inventory/pdf")
        assert r.status_code == 200

    def test_parameter_inventory_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 347: parameter inventory PDF missing → 404."""
        import routes.governance._constants as gc

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/parameter-inventory/pdf")
        assert r.status_code == 404

    def test_mrc_tor_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 359: MRC ToR PDF served."""
        import routes.governance._constants as gc

        tor_dir = tmp_path / "mrc_tor"
        tor_dir.mkdir()
        pdf_file = tor_dir / "mrc_terms_of_reference.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/mrc/terms-of-reference/pdf")
        assert r.status_code == 200

    def test_mrc_tor_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 357: MRC ToR PDF missing → 404."""
        import routes.governance._constants as gc

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/mrc/terms-of-reference/pdf")
        assert r.status_code == 404
