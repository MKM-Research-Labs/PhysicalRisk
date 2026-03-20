"""Coverage expansion tests for book/book.py — missing lines 116, 133, 231-237."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from port.src.book.book import (
    generate_market_making_book,
    generate_trade_pdfs,
    print_book_summary,
)


def _write_gaugehc(tmp_path, num_gauges=3):
    """Write a minimal gaugehc.json with hazard curves."""
    curves = {}
    for i in range(num_gauges):
        gid = f"GAUGE-{i:04d}"
        curves[gid] = {
            "gauge_name": f"Test Gauge {i}",
            "annual_hazard_rate_alert": 0.04 + i * 0.01,
            "annual_hazard_rate_warning": 0.02 + i * 0.005,
            "annual_hazard_rate_severe": 0.005 + i * 0.001,
        }
    path = tmp_path / "gaugehc.json"
    path.write_text(json.dumps({"hazard_curves": curves}))
    return path


def _write_empty_gaugehc(tmp_path):
    """Write gaugehc.json with no hazard curves."""
    path = tmp_path / "gaugehc.json"
    path.write_text(json.dumps({"hazard_curves": {}}))
    return path


def _write_counterparty(tmp_path, count=0):
    """Write counterparty.json. If count=0, write empty list."""
    parties = []
    for i in range(count):
        parties.append({
            "CounterpartySet": {
                "Party": {"PartyID": f"CTPY-{i:03d}", "PartyName": f"Party {i}"},
                "_platform": {"ShortName": f"P{i}", "CreditRating": "AA"},
            }
        })
    path = tmp_path / "counterparty.json"
    path.write_text(json.dumps({"counterparties": parties}))
    return path


class TestEmptyCurvesRaises:
    """Line 116: empty hazard_curves dict raises ValueError."""

    def test_no_curves_raises_value_error(self, tmp_path):
        ghc_path = _write_empty_gaugehc(tmp_path)
        ctpy_path = _write_counterparty(tmp_path)
        out_dir = tmp_path / "prs"
        out_dir.mkdir()

        with pytest.raises(ValueError, match="No hazard curves"):
            generate_market_making_book(ghc_path, ctpy_path, out_dir)


class TestFallbackCounterparties:
    """Line 133: when counterparty file has no entries, fallback list is used."""

    def test_empty_counterparty_file_uses_fallback(self, tmp_path):
        ghc_path = _write_gaugehc(tmp_path, num_gauges=2)
        ctpy_path = _write_counterparty(tmp_path, count=0)
        out_dir = tmp_path / "prs"
        out_dir.mkdir()

        trades = generate_market_making_book(
            ghc_path, ctpy_path, out_dir, num_gauges=2, seed=1
        )
        assert len(trades) > 0
        # Fallback counterparties are CTPY-001..CTPY-021
        ctpy_ids = {
            t["PhysicalSwap"]["Header"]["CounterParty"] for t in trades
        }
        assert all(cid.startswith("CTPY-") for cid in ctpy_ids)

    def test_missing_counterparty_file_uses_fallback(self, tmp_path):
        ghc_path = _write_gaugehc(tmp_path, num_gauges=2)
        ctpy_path = tmp_path / "nonexistent.json"
        out_dir = tmp_path / "prs"
        out_dir.mkdir()

        trades = generate_market_making_book(
            ghc_path, ctpy_path, out_dir, num_gauges=2, seed=1
        )
        assert len(trades) > 0


class TestGenerateTradePdfsFailure:
    """Lines 231-237: PDF generation failure is logged, not raised."""

    def test_pdf_failure_returns_empty_list(self, tmp_path):
        # Build a minimal trade record
        trade = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-TEST0001"},
                "LegData": {"Payer": True, "Notional": 1000000},
                "Pricing": {"NPV": 100},
            }
        }

        with patch("routes.prs._generate_trade_pdf",
                    side_effect=Exception("pdf error")):
            pdfs = generate_trade_pdfs([trade], tmp_path)

        assert pdfs == []

    def test_pdf_partial_failure_returns_successful_only(self, tmp_path):
        trade1 = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-FAIL"},
                "LegData": {"Payer": True, "Notional": 1000000},
                "Pricing": {"NPV": 100},
            }
        }
        trade2 = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-OK"},
                "LegData": {"Payer": False, "Notional": 500000},
                "Pricing": {"NPV": -50},
            }
        }

        call_count = [0]

        def mock_pdf(record, _, output_dir):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("fail first")
            return tmp_path / "ok.pdf"

        with patch("routes.prs._generate_trade_pdf", side_effect=mock_pdf):
            pdfs = generate_trade_pdfs([trade1, trade2], tmp_path)

        assert len(pdfs) == 1
