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
Tests for routes.governance.documents — document upload/download/delete.

Covers: GET documents (empty), POST upload (no file, empty filename, valid),
GET download (not found, file missing, valid), POST delete (not found, valid).
"""

import io
import json

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def doc_env(tmp_path, monkeypatch):
    """Governance documents environment with empty documents list."""
    import routes.governance._constants as gov_constants

    docs_path = str(tmp_path / "governance_documents.json")
    docs_dir = str(tmp_path / "governance_docs")

    with open(docs_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_PATH", docs_path)
    monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_DIR", docs_dir)

    return {"docs_path": docs_path, "docs_dir": docs_dir, "tmp_path": tmp_path}


@pytest.fixture
def doc_client(doc_env, monkeypatch):
    """Flask test client with isolated document storage."""
    import pathlib
    from config import config
    monkeypatch.setattr(config, "get_input_dir",
                        lambda: pathlib.Path(doc_env["docs_path"]).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# GET /api/v1/governance/documents
# ===========================================================================

class TestGetDocuments:

    def test_empty_list_returns_success(self, doc_client):
        r = doc_client.get("/api/v1/governance/documents")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert data["documents"] == []


# ===========================================================================
# POST /api/v1/governance/documents/upload
# ===========================================================================

class TestUploadDocument:

    def test_no_file_returns_400(self, doc_client):
        r = doc_client.post("/api/v1/governance/documents/upload")
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data["status"] == "error"

    def test_empty_filename_returns_400(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b""), "")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 400

    def test_valid_upload_returns_200(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={
                "file": (io.BytesIO(b"PDF content"), "test_doc.pdf"),
                "description": "Test governance document",
            },
            content_type="multipart/form-data",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert "document" in data

    def test_upload_response_has_id(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"data"), "report.pdf")},
            content_type="multipart/form-data",
        )
        data = json.loads(r.data)
        assert "id" in data["document"]

    def test_upload_appears_in_list(self, doc_client):
        doc_client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"data"), "myfile.pdf")},
            content_type="multipart/form-data",
        )
        r = doc_client.get("/api/v1/governance/documents")
        data = json.loads(r.data)
        assert len(data["documents"]) == 1

    def test_upload_stores_description(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={
                "file": (io.BytesIO(b"data"), "file.pdf"),
                "description": "My description",
            },
            content_type="multipart/form-data",
        )
        data = json.loads(r.data)
        assert data["document"]["description"] == "My description"


# ===========================================================================
# GET /api/v1/governance/documents/<doc_id>/download
# ===========================================================================

class TestDownloadDocument:

    def _upload(self, client, content=b"pdf bytes", name="test.pdf"):
        r = client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(content), name)},
            content_type="multipart/form-data",
        )
        return json.loads(r.data)["document"]["id"]

    def test_not_found_returns_404(self, doc_client):
        r = doc_client.get("/api/v1/governance/documents/nonexistent/download")
        assert r.status_code == 404

    def test_valid_download_returns_200(self, doc_client):
        doc_id = self._upload(doc_client)
        r = doc_client.get(f"/api/v1/governance/documents/{doc_id}/download")
        assert r.status_code == 200


# ===========================================================================
# POST /api/v1/governance/documents/<doc_id>/delete
# ===========================================================================

class TestDeleteDocument:

    def _upload(self, client):
        r = client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"data"), "del.pdf")},
            content_type="multipart/form-data",
        )
        return json.loads(r.data)["document"]["id"]

    def test_not_found_returns_404(self, doc_client):
        r = doc_client.post("/api/v1/governance/documents/nonexistent/delete")
        assert r.status_code == 404

    def test_valid_delete_returns_success(self, doc_client):
        doc_id = self._upload(doc_client)
        r = doc_client.post(f"/api/v1/governance/documents/{doc_id}/delete")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"

    def test_deleted_doc_not_in_list(self, doc_client):
        doc_id = self._upload(doc_client)
        doc_client.post(f"/api/v1/governance/documents/{doc_id}/delete")
        r = doc_client.get("/api/v1/governance/documents")
        data = json.loads(r.data)
        ids = [d["id"] for d in data["documents"]]
        assert doc_id not in ids


# ===========================================================================
# Coverage expansion: save metadata failures (L76, L111), file missing on disk (L91)
# ===========================================================================

class TestUploadSaveMetadataFails:
    """Line 76: _save_gov_documents returns False → 500."""

    def test_upload_save_failure_returns_500(self, doc_env, monkeypatch):
        import pathlib
        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(doc_env["docs_path"]).parent)

        # Patch _save_gov_documents where it's imported in the documents module
        import routes.governance.documents as docs_mod
        monkeypatch.setattr(docs_mod, "_save_gov_documents", lambda docs: False)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"content"), "test.pdf")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data["status"] == "error"
        assert "metadata" in data["message"].lower() or "save" in data["message"].lower()


class TestDownloadFileMissingOnDisk:
    """Line 91: document metadata exists but file is missing on disk → 404."""

    def test_file_missing_on_disk_returns_404(self, doc_env, monkeypatch):
        import pathlib
        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(doc_env["docs_path"]).parent)

        # Write metadata for a document whose file does NOT exist on disk
        docs = [{"id": "ghost-doc", "filename": "ghost.pdf",
                 "stored_as": "ghost-doc_ghost.pdf",
                 "description": "", "uploaded_at": "2026-01-01T00:00:00",
                 "size": 100}]
        with open(doc_env["docs_path"], "w") as f:
            json.dump(docs, f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/governance/documents/ghost-doc/download")
        assert r.status_code == 404
        data = json.loads(r.data)
        assert "not found" in data["message"].lower()


class TestDeleteSaveMetadataFails:
    """Line 111: _save_gov_documents returns False on delete → 500."""

    def test_delete_save_failure_returns_500(self, doc_env, monkeypatch):
        import os
        import pathlib
        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(doc_env["docs_path"]).parent)

        # First create a document via metadata
        docs_dir = doc_env["docs_dir"]
        os.makedirs(docs_dir, exist_ok=True)
        stored_name = "deltest_test.pdf"
        with open(os.path.join(docs_dir, stored_name), "w") as f:
            f.write("content")
        docs = [{"id": "deltest", "filename": "test.pdf",
                 "stored_as": stored_name,
                 "description": "", "uploaded_at": "2026-01-01T00:00:00",
                 "size": 7}]
        with open(doc_env["docs_path"], "w") as f:
            json.dump(docs, f)

        # Patch _save_gov_documents where it's imported in the documents module
        import routes.governance.documents as docs_mod
        monkeypatch.setattr(docs_mod, "_save_gov_documents", lambda docs: False)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post("/api/v1/governance/documents/deltest/delete")
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data["status"] == "error"
