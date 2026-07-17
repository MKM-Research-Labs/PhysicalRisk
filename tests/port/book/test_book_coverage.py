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

"""Coverage expansion tests for book/book.py — empty-curves raise, counterparty
fallback, and PDF-failure handling.

Gauge hazard curves and counterparties are served through the ``database`` seam;
the ``backend`` fixture binds a scratch catchment and the ``_seed_*`` helpers
save into it, so the generator (defaulting to ``catchment_id='thames'``) reads
them back."""

from unittest.mock import patch

import pytest
from db_helpers import tmp_catchment

import database
from port.src.book.book import (
    generate_market_making_book,
    generate_trade_pdfs,
    print_book_summary,
)

_CATCHMENT = "thames"


@pytest.fixture
def backend(tmp_path):
    """Bind a scratch backend so the _seed_* helpers and generator share state."""
    with tmp_catchment(tmp_path, _CATCHMENT) as repo:
        yield repo


def _seed_gaugehc(num_gauges=3):
    """Seed a minimal gauge hazard-curve set through the seam."""
    curves = {}
    for i in range(num_gauges):
        gid = f"GAUGE-{i:04d}"
        curves[gid] = {
            "gauge_name": f"Test Gauge {i}",
            "annual_hazard_rate_alert": 0.04 + i * 0.01,
            "annual_hazard_rate_warning": 0.02 + i * 0.005,
            "annual_hazard_rate_severe": 0.005 + i * 0.001,
        }
    database.save_gauge_hazard_curves(_CATCHMENT, {"hazard_curves": curves})


def _seed_empty_gaugehc():
    """Seed an empty hazard-curve set through the seam."""
    database.save_gauge_hazard_curves(_CATCHMENT, {"hazard_curves": {}})


def _seed_counterparty(count=0):
    """Seed a counterparty set through the seam (empty when count=0)."""
    parties = []
    for i in range(count):
        parties.append({
            "CounterpartySet": {
                "Party": {"PartyID": f"CTPY-{i:03d}", "PartyName": f"Party {i}"},
                "_platform": {"ShortName": f"P{i}", "CreditRating": "AA"},
            }
        })
    database.save_counterparties(_CATCHMENT, {"counterparties": parties})


class TestEmptyCurvesRaises:
    """Empty hazard_curves dict raises ValueError."""

    def test_no_curves_raises_value_error(self, backend, tmp_path):
        _seed_empty_gaugehc()
        _seed_counterparty()

        with pytest.raises(ValueError, match="No hazard curves"):
            generate_market_making_book(tmp_path / "prs")


class TestFallbackCounterparties:
    """When no counterparties exist, the fallback list is used."""

    def test_empty_counterparty_file_uses_fallback(self, backend, tmp_path):
        _seed_gaugehc(num_gauges=2)
        _seed_counterparty(count=0)

        trades = generate_market_making_book(tmp_path / "prs", num_gauges=2, seed=1)
        assert len(trades) > 0
        # Fallback counterparties are CTPY-001..CTPY-021
        ctpy_ids = {
            t["PhysicalSwap"]["Header"]["CounterParty"] for t in trades
        }
        assert all(cid.startswith("CTPY-") for cid in ctpy_ids)

    def test_missing_counterparty_file_uses_fallback(self, backend, tmp_path):
        _seed_gaugehc(num_gauges=2)
        # No counterparties seeded — the seam returns nothing, fallback applies.

        trades = generate_market_making_book(tmp_path / "prs", num_gauges=2, seed=1)
        assert len(trades) > 0


class TestGenerateTradePdfsFailure:
    """PDF generation failure is logged, not raised."""

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
