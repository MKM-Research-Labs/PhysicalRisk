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

"""The commercial portfolio stage must regenerate under --all (like the
property portfolio), not only when --commercial is passed.

Regression: previously `run_commercial_portfolio` was gated `if not
args.commercial`, so a default `port` run never regenerated commercial.json —
`-nc/--num-commercial` was silently ignored and the downstream commercial
hazard stages built on a stale commercial.json.
"""

from unittest.mock import MagicMock

from app.commands.port.stages import portfolios


def _ctx(run_all, commercial):
    ctx = MagicMock()
    ctx.run_all = run_all
    ctx.args.commercial = commercial
    ctx.args.num_commercial = 2
    gen = ctx.commercial_gen.CommercialPortfolioGenerator.return_value
    gen.generate.return_value = {
        "data": {"commercial_assets": [
            {"CommercialAsset": {"CommercialAttributes": {"CommercialType": "Office"}}},
            {"CommercialAsset": {"CommercialAttributes": {"CommercialType": "Retail"}}},
        ]},
        "processing_stats": {"successful_assets": 2, "total_assets": 2},
    }
    ctx.commercial_loan_gen_cls.return_value.generate.return_value = {
        "data": {"commercial_loans": []}
    }
    return ctx


def _generate_mock(ctx):
    return ctx.commercial_gen.CommercialPortfolioGenerator.return_value.generate


class TestCommercialPortfolioGating:
    def test_runs_under_run_all_without_flag(self):
        ctx = _ctx(run_all=True, commercial=False)
        portfolios.run_commercial_portfolio(ctx)
        _generate_mock(ctx).assert_called_once_with(2)  # -nc honoured

    def test_runs_when_commercial_flag_set(self):
        ctx = _ctx(run_all=False, commercial=True)
        portfolios.run_commercial_portfolio(ctx)
        _generate_mock(ctx).assert_called_once_with(2)

    def test_skipped_when_neither(self):
        ctx = _ctx(run_all=False, commercial=False)
        portfolios.run_commercial_portfolio(ctx)
        _generate_mock(ctx).assert_not_called()
