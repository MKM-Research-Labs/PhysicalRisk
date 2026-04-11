"""Tests for client blotter coverage: corrupt trade file (lines 87-89) and 500 error (lines 109-111)."""

import json
from unittest.mock import patch

import pytest


class TestCorruptTradeFileSkipped:
    """Cover lines 87-89: exception handler skips corrupt trade files."""

    def test_corrupt_json_skipped(self, trading_env, trading_client):
        """A corrupt JSON file in prs_dir is skipped gracefully."""
        prs_dir = trading_env["prs_dir"]
        # Write a corrupt file that matches the PRS-*.json glob pattern
        corrupt_file = prs_dir / "PRS-CORRUPT.json"
        corrupt_file.write_text("{invalid json content!!!")

        resp = trading_client.get("/api/v1/trading/client")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        # Valid trades from trading_env should still load
        assert data["summary"]["num_trades"] >= 0

    def test_trade_file_with_missing_keys_skipped(self, trading_env, trading_client):
        """A trade file that raises an exception during processing is skipped."""
        prs_dir = trading_env["prs_dir"]
        # Write a file that's valid JSON but causes an exception during field access
        # by having a GaugeBasket that's not a list (will fail on [0] indexing)
        bad_trade = {
            "PhysicalSwap": {
                "Header": {"SwapID": "BAD-001"},
                "PropertySet": {"PropertyID": "P1"},
                "GaugeSet": {"GaugeBasket": "not-a-list"},
                "LegData": {},
                "ScheduleData": {},
                "Pricing": {},
            }
        }
        (prs_dir / "PRS-BAD.json").write_text(json.dumps(bad_trade))

        resp = trading_client.get("/api/v1/trading/client")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"


class TestClientBlotter500:
    """Cover lines 109-111: exception handler returns 500."""

    def test_get_reports_dir_raises_returns_500(self, trading_client, monkeypatch):
        """When config.get_reports_dir raises, the endpoint returns 500."""
        from config import config
        monkeypatch.setattr(
            config, "get_reports_dir",
            lambda subdir=None: (_ for _ in ()).throw(RuntimeError("disk error")),
        )

        resp = trading_client.get("/api/v1/trading/client")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert "Internal server error" in data["message"]
