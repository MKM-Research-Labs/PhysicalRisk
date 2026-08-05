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

"""Tests for routes/propertyts/risk.py — portfolio VaR/ES endpoint (part 3).

Seam-failure degradation paths: storm-sequence load raising, property/loan
portfolio loads raising, and a property-timeseries id that resolves to None.
These branches cannot be reached through the file fixtures alone (a missing
file returns None rather than raising), so the database seam functions are
monkeypatched at call time.
"""

import database

from tests.routes.propertyts.conftest import (
    make_prop_flood as _make_prop_flood,
    make_property_json as _make_property_json,
    make_risk_client as _make_client,
    make_storm_sequences as _make_sequences,
    PORTFOLIO_VAR_URL as URL,
)


def _raise(*_a, **_k):
    raise RuntimeError("seam read failed")


# ===========================================================================
# storm_sequences load raises → 404 (lines 61-63)
# ===========================================================================

class TestStormSequencesLoadRaises:

    def test_returns_404(self, tmp_path, monkeypatch):
        client = _make_client(tmp_path, monkeypatch, pts_dir=True,
                              sequences=_make_sequences("STORM-0001"))
        monkeypatch.setattr(database, "get_storm_sequences", _raise)
        assert client.get(URL).status_code == 404

    def test_status_error(self, tmp_path, monkeypatch):
        client = _make_client(tmp_path, monkeypatch, pts_dir=True,
                              sequences=_make_sequences("STORM-0001"))
        monkeypatch.setattr(database, "get_storm_sequences", _raise)
        assert client.get(URL).get_json()["status"] == "error"


# ===========================================================================
# property portfolio load raises → still 200, zero portfolio value (lines 81-82)
# ===========================================================================

class TestPropertyPortfolioLoadRaises:

    def _client(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            prop_floods={"PROP-001.json": _make_prop_flood("PROP-001", [
                {"storm_id": "STORM-0001", "flood_depth_m": 0.5, "damage_ratio": 0.1}
            ])},
            property_json=_make_property_json("PROP-001", 400000),
        )
        monkeypatch.setattr(database, "get_property_portfolio", _raise)
        return client

    def test_returns_200(self, tmp_path, monkeypatch):
        assert self._client(tmp_path, monkeypatch).get(URL).status_code == 200

    def test_zero_portfolio_value(self, tmp_path, monkeypatch):
        # Valuations never loaded → no property matches → no damage recorded.
        data = self._client(tmp_path, monkeypatch).get(URL).get_json()
        assert data["total_portfolio_value"] == 0.0
        assert data["storms_with_damage"] == 0


# ===========================================================================
# loan portfolio load raises → still 200, zero mortgages (lines 93-94)
# ===========================================================================

class TestLoanPortfolioLoadRaises:

    def _client(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            prop_floods={"PROP-001.json": _make_prop_flood("PROP-001", [
                {"storm_id": "STORM-0001", "flood_depth_m": 0.5, "damage_ratio": 0.1}
            ])},
            property_json=_make_property_json("PROP-001", 400000),
        )
        monkeypatch.setattr(database, "get_loan_portfolio", _raise)
        return client

    def test_returns_200(self, tmp_path, monkeypatch):
        assert self._client(tmp_path, monkeypatch).get(URL).status_code == 200

    def test_zero_portfolio_mortgages(self, tmp_path, monkeypatch):
        data = self._client(tmp_path, monkeypatch).get(URL).get_json()
        assert data["total_portfolio_mortgages"] == 0.0

    def test_property_damage_still_computed(self, tmp_path, monkeypatch):
        # Property valuations still load, so property damage is unaffected.
        data = self._client(tmp_path, monkeypatch).get(URL).get_json()
        assert data["storms_with_damage"] == 1


# ===========================================================================
# property timeseries id resolves to None → skipped (line 106)
# ===========================================================================

class TestPropertyTimeseriesNone:

    def test_none_timeseries_skipped(self, tmp_path, monkeypatch):
        client = _make_client(
            tmp_path, monkeypatch,
            sequences=_make_sequences("STORM-0001"),
            prop_floods={"PROP-001.json": _make_prop_flood("PROP-001", [
                {"storm_id": "STORM-0001", "flood_depth_m": 0.5, "damage_ratio": 0.1}
            ])},
            property_json=_make_property_json("PROP-001", 400000),
        )
        # The id still iterates (PROP-001) but its payload resolves to None.
        monkeypatch.setattr(database, "get_property_timeseries", lambda *a, **k: None)
        data = client.get(URL).get_json()
        assert data["status"] == "success"
        assert data["storms_with_damage"] == 0
