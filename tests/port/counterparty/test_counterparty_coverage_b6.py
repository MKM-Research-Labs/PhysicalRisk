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

"""Coverage expansion tests for counterparty.py — Block B6.

Targets missing lines:
  - 169-170: Verbose logging inside the generate loop (logger.info per counterparty)
  - 187: Verbose logging at the end of generate (logger.info summary)
"""

import logging

import pytest

from port.src.counterparty import CounterpartyPortfolioGenerator
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend for every test (the writer now persists via database)."""
    with tmp_catchment(tmp_path):
        yield


class TestVerboseLogging:

    def test_verbose_true_logs_per_counterparty(self, tmp_path, caplog):
        """Lines 169-170: when verbose=True, each counterparty is logged."""
        gen = CounterpartyPortfolioGenerator(verbose=True)
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
        gen = CounterpartyPortfolioGenerator(verbose=True)
        with caplog.at_level(logging.INFO):
            gen.generate(count=2)

        # 1 REIT + 2 externals = 3 total
        assert "Wrote 3 counterparties" in caplog.text

    def test_verbose_false_no_per_counterparty_log(self, tmp_path, caplog):
        """When verbose=False, the per-counterparty log lines are absent."""
        gen = CounterpartyPortfolioGenerator(verbose=False)
        with caplog.at_level(logging.INFO):
            gen.generate(count=2)

        assert "[REIT]" not in caplog.text
        assert "[1/2]" not in caplog.text
        assert "Wrote 3 counterparties" not in caplog.text
