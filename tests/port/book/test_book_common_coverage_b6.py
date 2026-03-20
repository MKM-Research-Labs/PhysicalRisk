"""Coverage expansion tests for book_common.py — Block B6.

Targets missing lines:
  - 186: CDM validation warning logged when _build_cdm_record produces invalid record
  - 208: Fallback counterparties when counterparty file exists but has empty list
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from port.src.book.book_common import _build_cdm_record, _load_counterparties


# ---------------------------------------------------------------------------
# Line 186: CDM validation warning in _build_cdm_record
# ---------------------------------------------------------------------------

class TestBuildCdmRecordValidationWarning:

    def test_cdm_validation_warning_logged(self, caplog):
        """Line 186: when CDM validation returns errors, a warning is logged."""
        # Force the CDM validator to return errors by mocking it
        with patch("port.src.book.book_common._cdm") as mock_cdm:
            mock_cdm.validate.return_value = {"Header": ["Missing SwapID"]}

            with caplog.at_level(logging.WARNING):
                record = _build_cdm_record(
                    swap_id="PRS-TEST001",
                    gauge_id="GAUGE-0001",
                    gauge_name="Test Gauge",
                    catchment_id="thames",
                    counterparty_id="CTPY-001",
                    counterparty_name="Test Party",
                    is_payer=True,
                    notional=1_000_000,
                    tenor=5,
                    trigger="alert",
                    trade_spread_bps=50.0,
                    fair_spread_bps=45.0,
                    npv=1234.56,
                    premium_leg_pv=5000.0,
                    protection_leg_pv=6234.56,
                    risky_annuity=4.5,
                    trade_date=datetime(2026, 1, 15),
                )

            assert record is not None
            assert "PhysicalSwap" in record
            assert "CDM validation" in caplog.text


# ---------------------------------------------------------------------------
# Line 208: Fallback counterparties when file has empty counterparties list
# ---------------------------------------------------------------------------

class TestLoadCounterpartiesFallback:

    def test_empty_counterparty_list_uses_fallback(self, tmp_path):
        """Line 208: file exists with empty counterparties → fallback list."""
        path = tmp_path / "counterparty.json"
        path.write_text(json.dumps({"counterparties": []}))

        result = _load_counterparties(path)
        assert len(result) == 21
        assert result[0]["id"] == "CTPY-001"
        assert result[-1]["id"] == "CTPY-021"

    def test_nonexistent_file_uses_fallback(self, tmp_path):
        """Line 207-209: file doesn't exist → fallback list."""
        path = tmp_path / "nonexistent.json"
        result = _load_counterparties(path)
        assert len(result) == 21

    def test_populated_file_returns_loaded_data(self, tmp_path):
        """When file has entries, those are returned (not fallback)."""
        parties = [{
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-REAL", "PartyName": "Real Bank"},
                "_platform": {"ShortName": "RealB", "CreditRating": "AA"},
            }
        }]
        path = tmp_path / "counterparty.json"
        path.write_text(json.dumps({"counterparties": parties}))

        result = _load_counterparties(path)
        assert len(result) == 1
        assert result[0]["id"] == "CTPY-REAL"
        assert "RealB" in result[0]["name"]
