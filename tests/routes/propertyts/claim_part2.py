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

"""Tests for the property flood damage claim report route — part 2.

Helper exception branches: missing support files, corrupt JSON.
"""

import json

import pytest

from .conftest import (
    CLAIM_PROP_ID,
    CLAIM_PROP_FLOOD_DATA,
    CLAIM_PROPERTY_JSON,
    CLAIM_MORTGAGE_JSON,
)


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
        (pts_dir / f"{CLAIM_PROP_ID}.json").write_text(json.dumps(CLAIM_PROP_FLOOD_DATA))
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
        r = claim_env_no_support_files.get(f"/api/v1/properties/{CLAIM_PROP_ID}/claim-report")
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
        r = claim_env_no_support_files.get(f"/api/v1/properties/{CLAIM_PROP_ID}/claim-report")
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
        r = claim_env_no_support_files.get(f"/api/v1/properties/{CLAIM_PROP_ID}/claim-report")
        assert r.status_code == 200

    def test_corrupt_sequences_file_handled(self, tmp_path, monkeypatch):
        """Corrupt storm_sequences.json triggers the except in _load_sequence_lookup (L56-57)."""
        from config import config
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        (pts_dir / f"{CLAIM_PROP_ID}.json").write_text(json.dumps(CLAIM_PROP_FLOOD_DATA))
        (tmp_path / "property.json").write_text(json.dumps(CLAIM_PROPERTY_JSON))
        (tmp_path / "mortgage.json").write_text(json.dumps(CLAIM_MORTGAGE_JSON))
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
        r = client.get(f"/api/v1/properties/{CLAIM_PROP_ID}/claim-report")
        assert r.status_code == 200
