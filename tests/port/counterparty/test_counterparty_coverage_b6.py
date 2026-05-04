"""Coverage expansion tests for counterparty.py — Block B6.

Targets missing lines:
  - 169-170: Verbose logging inside the generate loop (logger.info per counterparty)
  - 187: Verbose logging at the end of generate (logger.info summary)
"""

import logging

import pytest

from port.src.counterparty import CounterpartyPortfolioGenerator


class TestVerboseLogging:

    def test_verbose_true_logs_per_counterparty(self, tmp_path, caplog):
        """Lines 169-170: when verbose=True, each counterparty is logged."""
        gen = CounterpartyPortfolioGenerator(output_dir=tmp_path, verbose=True)
        with caplog.at_level(logging.INFO):
            result = gen.generate(count=3)

        # 1 REIT + 3 externals = 4 records
        assert len(result["data"]) == 4
        # The REIT line is logged separately, then [1/3]..[3/3] for externals
        assert "[REIT]" in caplog.text
        assert "[1/3]" in caplog.text
        assert "[2/3]" in caplog.text
        assert "[3/3]" in caplog.text

    def test_verbose_true_logs_summary(self, tmp_path, caplog):
        """Line 187: verbose=True logs final summary with count and path."""
        gen = CounterpartyPortfolioGenerator(output_dir=tmp_path, verbose=True)
        with caplog.at_level(logging.INFO):
            gen.generate(count=2)

        # 1 REIT + 2 externals = 3 total
        assert "Wrote 3 counterparties" in caplog.text

    def test_verbose_false_no_per_counterparty_log(self, tmp_path, caplog):
        """When verbose=False, the per-counterparty log lines are absent."""
        gen = CounterpartyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        with caplog.at_level(logging.INFO):
            gen.generate(count=2)

        assert "[REIT]" not in caplog.text
        assert "[1/2]" not in caplog.text
        assert "Wrote 3 counterparties" not in caplog.text
