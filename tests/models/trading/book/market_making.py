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

"""Tests for market-making book generation, spread rounding, and summary printer."""

from port.src.book import generate_market_making_book, print_book_summary


class TestGenerateBook:
    """Tests for the full market-making book generation."""

    def test_balanced_book(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        payer = sum(1 for t in trades if t["PhysicalSwap"]["LegData"]["Payer"])
        rcv = sum(1 for t in trades if not t["PhysicalSwap"]["LegData"]["Payer"])
        assert payer == rcv
        assert len(trades) == 6

    def test_balanced_notional(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        payer_not = sum(
            t["PhysicalSwap"]["LegData"]["Notional"]
            for t in trades if t["PhysicalSwap"]["LegData"]["Payer"]
        )
        rcv_not = sum(
            t["PhysicalSwap"]["LegData"]["Notional"]
            for t in trades if not t["PhysicalSwap"]["LegData"]["Payer"]
        )
        assert payer_not == rcv_not

    def test_small_mtm(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        for t in trades:
            ps = t["PhysicalSwap"]
            assert abs(ps["Pricing"]["NPV"]) < ps["LegData"]["Notional"] * 0.015

    def test_payer_trades_below_fair(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        for t in trades:
            ps = t["PhysicalSwap"]
            if ps["LegData"]["Payer"]:
                assert ps["Pricing"]["SpreadBps"] < ps["Pricing"]["FairSpreadBps"]

    def test_receiver_trades_above_fair(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        for t in trades:
            ps = t["PhysicalSwap"]
            if not ps["LegData"]["Payer"]:
                assert ps["Pricing"]["SpreadBps"] > ps["Pricing"]["FairSpreadBps"]

    def test_files_saved(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        assert len(list(output_dir.glob("PRS-*.json"))) == 6

    def test_valid_cdm_structure(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=2, seed=42
        )
        for t in trades:
            ps = t["PhysicalSwap"]
            for key in ["Header", "LegData", "ScheduleData", "GaugeSet", "Pricing"]:
                assert key in ps
            assert ps["Header"]["SwapID"].startswith("PRS-")
            assert isinstance(ps["LegData"]["Payer"], bool)
            assert ps["Pricing"]["RiskyAnnuity"] > 0

    def test_counterparties_distributed(self, sample_gaugehc, sample_counterparties, tmp_path):
        output_dir = tmp_path / "prs"
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, output_dir, num_gauges=3, seed=42
        )
        ctpys = {t["PhysicalSwap"]["Header"]["CounterParty"] for t in trades}
        assert len(ctpys) == 2

    def test_reproducible_with_seed(self, sample_gaugehc, sample_counterparties, tmp_path):
        trades1 = generate_market_making_book(
            sample_gaugehc, sample_counterparties, tmp_path / "prs1", num_gauges=2, seed=99
        )
        trades2 = generate_market_making_book(
            sample_gaugehc, sample_counterparties, tmp_path / "prs2", num_gauges=2, seed=99
        )
        for t1, t2 in zip(trades1, trades2):
            assert (
                t1["PhysicalSwap"]["Pricing"]["SpreadBps"]
                == t2["PhysicalSwap"]["Pricing"]["SpreadBps"]
            )


class TestTradeSpreadRounding:
    """Tests for trade spread rounding to integer bps."""

    def test_market_making_spreads_are_integers(self, sample_gaugehc, sample_counterparties, tmp_path):
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, tmp_path / "prs", num_gauges=3, seed=42
        )
        for t in trades:
            spread = t["PhysicalSwap"]["Pricing"]["SpreadBps"]
            assert spread == round(spread)

    def test_thames_central_spreads_are_integers(
        self, thames_central_gaugehc, sample_counterparties, tmp_path
    ):
        from port.src.book import generate_thames_central_book

        trades = generate_thames_central_book(
            thames_central_gaugehc, sample_counterparties, tmp_path / "prs", seed=42
        )
        for t in trades:
            spread = t["PhysicalSwap"]["Pricing"]["SpreadBps"]
            assert spread == round(spread)


class TestPrintBookSummary:
    """Tests for the summary printer."""

    def test_summary_runs(self, sample_gaugehc, sample_counterparties, tmp_path, capsys):
        trades = generate_market_making_book(
            sample_gaugehc, sample_counterparties, tmp_path / "prs", num_gauges=2, seed=42
        )
        print_book_summary(trades)
        out = capsys.readouterr().out
        assert "Market-Making Book Summary" in out
        assert "Payer (short):" in out
        assert "Receiver (long):" in out
