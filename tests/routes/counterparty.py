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
Tests for routes.counterparty — counterparty API endpoints.

Covers: list_counterparties (no file → empty list, with data → summary),
get_counterparty (not found → 404, found → 200).
"""

import json

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def ctpy_env(tmp_path, monkeypatch):
    """Counterparty test environment with a JSON file."""
    from config import config
    from jsonfiles import JSONFileConfig

    ctpy_data = {
        "counterparties": [
            {
                "CounterpartySet": {
                    "Party": {
                        "PartyID": "CTPY-001",
                        "PartyName": "Test Bank PLC",
                    },
                    "_platform": {
                        "ShortName": "TestBank",
                        "PartyType": "Bank",
                        "Status": "Active",
                        "CreditRating": "AA",
                        "MaxNotional": 10_000_000,
                        "MaxTenor": 5,
                    },
                }
            },
            {
                "CounterpartySet": {
                    "Party": {
                        "PartyID": "CTPY-002",
                        "PartyName": "Another Fund",
                    },
                    "_platform": {
                        "ShortName": "AnotherFund",
                        "PartyType": "HedgeFund",
                        "Status": "Active",
                        "CreditRating": "A",
                        "MaxNotional": 5_000_000,
                        "MaxTenor": 3,
                    },
                }
            },
        ]
    }
    ctpy_file = tmp_path / JSONFileConfig.COUNTERPARTY_PORTFOLIO
    ctpy_file.write_text(json.dumps(ctpy_data))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def ctpy_client_no_file(tmp_path, monkeypatch):
    """Flask client with no counterparty JSON file."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# GET /counterparties
# ===========================================================================

class TestListCounterparties:

    def test_no_file_returns_empty_list(self, ctpy_client_no_file):
        r = ctpy_client_no_file.get("/api/v1/counterparties")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert data["count"] == 0
        assert data["counterparties"] == []

    def test_with_data_returns_summary(self, ctpy_env):
        r = ctpy_env.get("/api/v1/counterparties")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert data["count"] == 2

    def test_summary_fields(self, ctpy_env):
        r = ctpy_env.get("/api/v1/counterparties")
        ctpies = json.loads(r.data)["counterparties"]
        first = ctpies[0]
        assert first["counterparty_id"] == "CTPY-001"
        assert first["name"] == "Test Bank PLC"
        assert first["credit_rating"] == "AA"
        assert first["status"] == "Active"


# ===========================================================================
# GET /counterparties/<ctpy_id>
# ===========================================================================

class TestGetCounterparty:

    def test_not_found_returns_404(self, ctpy_env):
        r = ctpy_env.get("/api/v1/counterparties/CTPY-NONEXISTENT")
        assert r.status_code == 404
        data = json.loads(r.data)
        assert data["status"] == "error"

    def test_found_returns_200(self, ctpy_env):
        r = ctpy_env.get("/api/v1/counterparties/CTPY-001")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert "counterparty" in data

    def test_found_second_counterparty(self, ctpy_env):
        r = ctpy_env.get("/api/v1/counterparties/CTPY-002")
        assert r.status_code == 200


# ===========================================================================
# Exception handling — lines 58-59, 74-75
# ===========================================================================

class TestCounterpartyErrors:

    @pytest.fixture
    def bad_json_client(self, tmp_path, monkeypatch):
        """Flask client where counterparty file has invalid JSON."""
        from config import config
        from jsonfiles import JSONFileConfig

        bad_file = tmp_path / JSONFileConfig.COUNTERPARTY_PORTFOLIO
        bad_file.write_text("NOT VALID JSON {{{")  # will raise json.JSONDecodeError

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_list_counterparties_error_returns_500(self, bad_json_client):
        """Lines 58-59: json.JSONDecodeError → 500."""
        r = bad_json_client.get("/api/v1/counterparties")
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data["status"] == "error"

    def test_get_counterparty_error_returns_500(self, bad_json_client):
        """Lines 74-75: json.JSONDecodeError in get_counterparty → 500."""
        r = bad_json_client.get("/api/v1/counterparties/CTPY-001")
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data["status"] == "error"
