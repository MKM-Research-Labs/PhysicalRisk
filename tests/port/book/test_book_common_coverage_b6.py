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

"""Coverage expansion tests for book_common.py — Block B6.

Targets missing lines:
  - 186: CDM validation warning logged when _build_cdm_record produces invalid record
  - 208: Fallback counterparties when counterparty file exists but has empty list
"""

import logging
from datetime import datetime
from unittest.mock import patch

import pytest
from db_helpers import tmp_catchment

import database
from port.src.book.book_common import _build_cdm_record, _load_counterparties

_CATCHMENT = "thames"


@pytest.fixture
def backend(tmp_path):
    """Bind a scratch backend so counterparties seed/read through the seam."""
    with tmp_catchment(tmp_path, _CATCHMENT) as repo:
        yield repo


# ---------------------------------------------------------------------------
# Line 186: CDM validation warning in _build_cdm_record
# ---------------------------------------------------------------------------

class TestBuildCdmRecordValidationWarning:

    def test_cdm_validation_warning_logged(self, caplog):
        """Line 186: when CDM validation returns errors, a warning is logged."""
        # Force the CDM validator to return errors by mocking it
        with patch("port.src.book.book_common._records._cdm") as mock_cdm:
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

    def test_empty_counterparty_list_uses_fallback(self, backend):
        """Empty counterparties list → fallback list."""
        database.save_counterparties(_CATCHMENT, {"counterparties": []})

        result = _load_counterparties(_CATCHMENT)
        assert len(result) == 21
        assert result[0]["id"] == "CTPY-001"
        assert result[-1]["id"] == "CTPY-021"

    def test_nonexistent_file_uses_fallback(self, backend):
        """No counterparties seeded → seam returns nothing → fallback list."""
        result = _load_counterparties(_CATCHMENT)
        assert len(result) == 21

    def test_populated_file_returns_loaded_data(self, backend):
        """When counterparties exist, those are returned (not fallback)."""
        parties = [{
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-REAL", "PartyName": "Real Bank"},
                "_platform": {"ShortName": "RealB", "CreditRating": "AA"},
            }
        }]
        database.save_counterparties(_CATCHMENT, {"counterparties": parties})

        result = _load_counterparties(_CATCHMENT)
        assert len(result) == 1
        assert result[0]["id"] == "CTPY-REAL"
        assert "RealB" in result[0]["name"]


class TestPriceAndSaveTradePersists:
    """_price_and_save_trade persists the priced trade through the prs_trade seam
    (the blotter/client/routes read it back via database.iter_prs_trade_ids)."""

    def test_trade_saved_to_seam(self, tmp_path):
        from port.src.book.book_common._pricing import _price_and_save_trade

        with tmp_catchment(tmp_path, _CATCHMENT):
            record, _ = _price_and_save_trade(
                gauge_id="GAUGE-0001",
                gauge_name="Test Gauge",
                catchment_id=_CATCHMENT,
                is_payer=True,
                tenor=5,
                notional=1_000_000,
                trigger="alert",
                hazard_rate=0.05,
                counterparties=[{"id": "CTPY-001", "name": "Test Party"}],
                ctpy_idx=0,
                base_date=datetime(2026, 1, 15),
                output_dir=tmp_path,
                fair_spread_override=45.0,
            )

            trades = database.list_prs_trades(_CATCHMENT)
            assert record is not None
            assert len(trades) == 1
