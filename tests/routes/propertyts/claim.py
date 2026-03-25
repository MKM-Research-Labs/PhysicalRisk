# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for the property flood damage claim report route.

GET /api/v1/properties/<prop_id>/claim-report
"""

import json

import pytest


PROP_ID = "PROP-001"

PROP_FLOOD_DATA = {
    "property_id": PROP_ID,
    "location": {"lat": 51.5, "lon": -0.1},
    "elevation_m": 3.0,
    "floor_level_m": 3.2,
    "flood_events": [{
        "storm_id": "STORM-0001",
        "sequence_id": "STORM-seq0001",
        "flood_depth_m": 0.5,
        "damage_ratio": 0.1,
        "arrival_time_hrs": 5,
        "peak_time_hrs": 12,
        "travel_time_hrs": 5,
        "retention_factor": 0.9,
        "readings": [{"wse_m": 3.4, "depth_m": 0.2, "flooded": True}],
    }],
}

PROPERTY_JSON = {"properties": [{"PropertyHeader": {
    "Header": {"PropertyID": PROP_ID},
    "Valuation": {"PropertyValue": 400000},
}}]}

MORTGAGE_JSON = {"mortgages": [{"Mortgage": {
    "Header": {"MortgageID": "MORT-001", "PropertyID": PROP_ID},
    "FinancialTerms": {"OriginalBalance": 300000},
    "CurrentStatus": {"OutstandingBalance": 280000},
}}]}

SEQUENCES_JSON = {"sequences": [{"sequence_id": "STORM-seq0001", "sequence_type": "isolated",
                                  "num_storms": 1, "intensity_category": "moderate",
                                  "storms": [{"storm_id": "STORM-0001"}]}]}


@pytest.fixture
def claim_no_pts_dir(tmp_path, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def claim_env(tmp_path, monkeypatch):
    from config import config
    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir()
    (pts_dir / f"{PROP_ID}.json").write_text(json.dumps(PROP_FLOOD_DATA))
    (tmp_path / "property.json").write_text(json.dumps(PROPERTY_JSON))
    (tmp_path / "mortgage.json").write_text(json.dumps(MORTGAGE_JSON))
    (tmp_path / "storm_sequences.json").write_text(json.dumps(SEQUENCES_JSON))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def claim_env_no_floods(tmp_path, monkeypatch):
    from config import config
    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir()
    (pts_dir / f"{PROP_ID}.json").write_text(json.dumps({**PROP_FLOOD_DATA, "flood_events": []}))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestClaimReportNoDir:

    def test_no_dir_returns_404(self, claim_no_pts_dir):
        r = claim_no_pts_dir.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 404

    def test_no_dir_status_error(self, claim_no_pts_dir):
        r = claim_no_pts_dir.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.get_json()["status"] == "error"

    def test_no_dir_message_mentions_propertyts(self, claim_no_pts_dir):
        r = claim_no_pts_dir.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        msg = r.get_json()["message"].lower()
        assert "propertyts" in msg or "property" in msg or "not found" in msg


class TestClaimReportNotFound:

    def test_unknown_property_returns_404(self, claim_env):
        r = claim_env.get("/api/v1/properties/PROP-GHOST/claim-report")
        assert r.status_code == 404

    def test_unknown_property_status_error(self, claim_env):
        r = claim_env.get("/api/v1/properties/PROP-GHOST/claim-report")
        assert r.get_json()["status"] == "error"

    def test_unknown_property_message_contains_id(self, claim_env):
        r = claim_env.get("/api/v1/properties/PROP-GHOST/claim-report")
        assert "PROP-GHOST" in r.get_json()["message"]


class TestClaimReportNoFloodEvents:

    def test_no_floods_returns_404(self, claim_env_no_floods):
        r = claim_env_no_floods.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 404

    def test_no_floods_status_error(self, claim_env_no_floods):
        r = claim_env_no_floods.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.get_json()["status"] == "error"

    def test_no_floods_message_mentions_events(self, claim_env_no_floods):
        r = claim_env_no_floods.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        msg = r.get_json()["message"].lower()
        assert "flood" in msg or "event" in msg


class TestClaimReportHappyPath:

    @pytest.fixture
    def claim_with_mock_pdf(self, claim_env, monkeypatch):
        fake_pdf = b"%PDF-1.4 fake pdf content"

        class FakeGenerator:
            def generate(self, *args, **kwargs):
                return fake_pdf

        import reports.property.claim as claim_mod
        monkeypatch.setattr(claim_mod, "ClaimReportGenerator", FakeGenerator)
        return claim_env, fake_pdf

    def test_success_returns_200(self, claim_with_mock_pdf):
        client, _ = claim_with_mock_pdf
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 200

    def test_response_is_pdf_content_type(self, claim_with_mock_pdf):
        client, _ = claim_with_mock_pdf
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.content_type == "application/pdf"

    def test_response_has_content_disposition(self, claim_with_mock_pdf):
        client, _ = claim_with_mock_pdf
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        cd = r.headers.get("Content-Disposition", "")
        assert "attachment" in cd
        assert PROP_ID in cd

    def test_response_body_is_pdf_bytes(self, claim_with_mock_pdf):
        client, fake_pdf = claim_with_mock_pdf
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.data == fake_pdf

    def test_content_length_header_set(self, claim_with_mock_pdf):
        client, fake_pdf = claim_with_mock_pdf
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.headers.get("Content-Length") == str(len(fake_pdf))

    def test_filename_contains_prop_id(self, claim_with_mock_pdf):
        client, _ = claim_with_mock_pdf
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        cd = r.headers.get("Content-Disposition", "")
        assert PROP_ID in cd


class TestClaimReportGenerationError:

    @pytest.fixture
    def claim_with_failing_pdf(self, claim_env, monkeypatch):
        class FailingGenerator:
            def generate(self, *args, **kwargs):
                raise RuntimeError("PDF generation failed")

        import reports.property.claim as claim_mod
        monkeypatch.setattr(claim_mod, "ClaimReportGenerator", FailingGenerator)
        return claim_env

    def test_generator_error_returns_500(self, claim_with_failing_pdf):
        r = claim_with_failing_pdf.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 500

    def test_generator_error_status_is_error(self, claim_with_failing_pdf):
        r = claim_with_failing_pdf.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.get_json()["status"] == "error"

    def test_generator_error_has_message(self, claim_with_failing_pdf):
        r = claim_with_failing_pdf.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.get_json().get("message")


class TestClaimReportHelperExceptions:
    """Cover exception branches in _load_sequence_lookup (L56-57),
    _load_prop_record (L71-73), and _load_mortgage_record (L89-91).

    These paths are hit when the underlying JSON files are missing or corrupt,
    but the propertyts flood data file itself is present with flood events.
    """

    @pytest.fixture
    def claim_env_no_support_files(self, tmp_path, monkeypatch):
        """Propertyts file present with floods, but property.json / mortgage.json /
        storm_sequences.json are all missing so the helpers hit their except branches."""
        from config import config
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        (pts_dir / f"{PROP_ID}.json").write_text(json.dumps(PROP_FLOOD_DATA))
        # Deliberately do NOT create property.json, mortgage.json, storm_sequences.json
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)
        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_missing_sequences_file_still_generates(self, claim_env_no_support_files, monkeypatch):
        """_load_sequence_lookup exception (L56-57) returns empty dict; report still generated."""
        fake_pdf = b"%PDF-1.4 fake"
        class FakeGen:
            def generate(self, *a, **kw):
                return fake_pdf
        import reports.property.claim as claim_mod
        monkeypatch.setattr(claim_mod, "ClaimReportGenerator", FakeGen)
        r = claim_env_no_support_files.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 200

    def test_missing_property_json_still_generates(self, claim_env_no_support_files, monkeypatch):
        """_load_prop_record exception (L71-73) returns {}; report still generated."""
        fake_pdf = b"%PDF-1.4 fake"
        class FakeGen:
            def generate(self, prop_data, prop_record, mort_record, seq_lookup):
                assert prop_record == {}
                return fake_pdf
        import reports.property.claim as claim_mod
        monkeypatch.setattr(claim_mod, "ClaimReportGenerator", FakeGen)
        r = claim_env_no_support_files.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 200

    def test_missing_mortgage_json_still_generates(self, claim_env_no_support_files, monkeypatch):
        """_load_mortgage_record exception (L89-91) returns None; report still generated."""
        fake_pdf = b"%PDF-1.4 fake"
        class FakeGen:
            def generate(self, prop_data, prop_record, mort_record, seq_lookup):
                assert mort_record is None
                return fake_pdf
        import reports.property.claim as claim_mod
        monkeypatch.setattr(claim_mod, "ClaimReportGenerator", FakeGen)
        r = claim_env_no_support_files.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 200

    def test_corrupt_sequences_file_handled(self, tmp_path, monkeypatch):
        """Corrupt storm_sequences.json triggers the except in _load_sequence_lookup (L56-57)."""
        from config import config
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        (pts_dir / f"{PROP_ID}.json").write_text(json.dumps(PROP_FLOOD_DATA))
        (tmp_path / "property.json").write_text(json.dumps(PROPERTY_JSON))
        (tmp_path / "mortgage.json").write_text(json.dumps(MORTGAGE_JSON))
        (tmp_path / "storm_sequences.json").write_text("NOT VALID JSON {{{")
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        fake_pdf = b"%PDF-1.4 fake"
        class FakeGen:
            def generate(self, prop_data, prop_record, mort_record, seq_lookup):
                assert seq_lookup == {}
                return fake_pdf
        import reports.property.claim as claim_mod
        monkeypatch.setattr(claim_mod, "ClaimReportGenerator", FakeGen)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        r = client.get(f"/api/v1/properties/{PROP_ID}/claim-report")
        assert r.status_code == 200
