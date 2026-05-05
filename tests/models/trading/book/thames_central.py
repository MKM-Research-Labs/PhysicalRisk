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

"""Tests for the Thames Central book generator."""

from datetime import datetime

from port.src.book import THAMES_CENTRAL_AREAS, generate_thames_central_book


class TestThamesCentralBook:
    """Tests for the Thames Central book generator."""

    def test_uses_central_gauges(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        trades = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs", seed=42
        )
        gauge_ids = {
            t["PhysicalSwap"]["GaugeSet"]["GaugeBasket"][0]["GaugeID"] for t in trades
        }
        expected_ids = {f"GAUGE-test{i:04d}" for i in range(len(THAMES_CENTRAL_AREAS))}
        assert gauge_ids.issubset(expected_ids)

    def test_trade_count(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        trades = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs", seed=42
        )
        assert len(trades) == 50

    def test_has_calendar_spreads(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        trades = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs", seed=42
        )
        by_gauge = {}
        for t in trades:
            ps = t["PhysicalSwap"]
            gid = ps["GaugeSet"]["GaugeBasket"][0]["GaugeID"]
            start = ps["ScheduleData"]["StartDate"]
            end = ps["ScheduleData"]["EndDate"]
            days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
            tenor = round(days / 365.25)
            is_payer = ps["LegData"]["Payer"]
            by_gauge.setdefault(gid, []).append((tenor, is_payer))

        calendar_spread_gauges = sum(
            1 for positions in by_gauge.values()
            if len({t for t, _ in positions}) >= 2 and len({d for _, d in positions}) == 2
        )
        assert calendar_spread_gauges >= 5

    def test_westminster_is_net_short(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        trades = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs", seed=42
        )
        westminster_notional = 0
        for t in trades:
            ps = t["PhysicalSwap"]
            gname = ps["GaugeSet"]["GaugeBasket"][0].get("GaugeName", "")
            if "westminster" not in gname.lower():
                continue
            notional = ps["LegData"]["Notional"]
            if ps["LegData"]["Payer"]:
                westminster_notional += notional
            else:
                westminster_notional -= notional
        assert westminster_notional < 0

    def test_files_saved(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, output_dir, seed=42
        )
        assert len(list(output_dir.glob("PRS-*.json"))) == 50

    def test_valid_cdm_structure(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        trades = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs", seed=42
        )
        for t in trades:
            ps = t["PhysicalSwap"]
            for key in ["Header", "LegData", "ScheduleData", "GaugeSet", "Pricing"]:
                assert key in ps
            assert ps["Header"]["SwapID"].startswith("PRS-")
            assert ps["Pricing"]["RiskyAnnuity"] > 0

    def test_reproducible_with_seed(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        trades1 = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs1", seed=99
        )
        trades2 = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs2", seed=99
        )
        for t1, t2 in zip(trades1, trades2):
            assert (
                t1["PhysicalSwap"]["Pricing"]["SpreadBps"]
                == t2["PhysicalSwap"]["Pricing"]["SpreadBps"]
            )


class TestThamesCentralBookEdgeCases:
    """Edge cases — empty hazard curves, missing gauge areas, no-seed mode."""

    def test_empty_hazard_curves_raises(self, sample_counterparties, tmp_path):
        """Line 181: empty hazard_curves dict raises ValueError."""
        import json
        import pytest

        gaugehc = {"metadata": {"catchment": "thames"}, "hazard_curves": {}}
        gauge_path = tmp_path / "gaugehc.json"
        gauge_path.write_text(json.dumps(gaugehc))

        with pytest.raises(ValueError, match="No hazard curves found"):
            generate_thames_central_book(
                gauge_path, sample_counterparties, tmp_path / "prs", seed=42
            )

    def test_missing_areas_warning_and_skip(
        self, sample_counterparties, tmp_path, caplog
    ):
        """Lines 195, 208-209: areas not matched → warning + skip trade specs."""
        import json
        import logging

        # Build hazard curves with only ONE matching gauge (Westminster).
        # All other areas in THAMES_CENTRAL_AREAS are unmatched, so:
        #  - line 195: 'Area %s not matched...' (per missing area)
        #  - lines 208-209: per trade spec for missing areas, log + continue
        gaugehc = {
            "metadata": {"catchment": "thames"},
            "hazard_curves": {
                "GAUGE-westminster": {
                    "gauge_id": "GAUGE-westminster",
                    "gauge_name": "Westminster Bridge Test",
                    "annual_hazard_rate_severe": 0.015,
                    "annual_hazard_rate_warning": 0.025,
                    "annual_hazard_rate_alert": 0.04,
                },
            },
        }
        gauge_path = tmp_path / "gaugehc.json"
        gauge_path.write_text(json.dumps(gaugehc))

        with caplog.at_level(logging.WARNING, logger="port.src.book.book_thames"):
            trades = generate_thames_central_book(
                gauge_path, sample_counterparties, tmp_path / "prs", seed=42
            )

        # Only Westminster trades should be generated (some specs match)
        assert len(trades) > 0
        # Each generated trade is for the Westminster gauge
        for t in trades:
            gname = t["PhysicalSwap"]["GaugeSet"]["GaugeBasket"][0].get("GaugeName", "")
            assert "westminster" in gname.lower()

        # Both kinds of warnings were emitted
        messages = [r.message for r in caplog.records]
        assert any("not matched to any gauge" in m for m in messages)
        assert any("Skipping trade spec" in m for m in messages)

    def test_seed_none_runs(self, thames_central_gaugehc, sample_counterparties, tmp_path):
        """Line 173 branch (seed is None): random isn't reseeded."""
        trades = generate_thames_central_book(
            thames_central_gaugehc,
            sample_counterparties,
            tmp_path / "prs",
            seed=None,
        )
        assert len(trades) == 50
