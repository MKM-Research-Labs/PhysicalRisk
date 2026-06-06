# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.mortgage.* (part 3)

Halong mortgages use USD + 'halong' catchment ID — the only two lines
that distinguish them from the thames implementation. Tests exercise
every field-name branch in the per-type generators plus the high-level
generate_financial_data / quality_consistency_check entry points.
"""

import random

import pytest


@pytest.fixture(autouse=True)
def _seeded():
    random.seed(20260527)


# ---------------------------------------------------------------------------
# quality.py
# ---------------------------------------------------------------------------

class TestQualityConsistencyCheck:
    def _scaffold(self, original=400_000, current=380_000, ltv=80, rate=4.5):
        return {
            "RLoan": {
                "FinancialTerms": {"OriginalLoan": original},
                "CurrentStatus": {
                    "OutstandingBalance": current,
                    "CurrentLTV": ltv,
                    "CurrentInterestRate": rate,
                },
            }
        }

    def test_current_balance_capped_below_original(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        m = self._scaffold(original=400_000, current=500_000)
        out = quality_consistency_check(m, {})
        assert (
            out["RLoan"]["CurrentStatus"]["OutstandingBalance"]
            <= out["RLoan"]["FinancialTerms"]["OriginalLoan"]
        )

    def test_ltv_above_100_clamped_to_95(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(ltv=150), {})
        assert out["RLoan"]["CurrentStatus"]["CurrentLTV"] == 95

    def test_ltv_below_10_clamped_to_60(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(ltv=5), {})
        assert out["RLoan"]["CurrentStatus"]["CurrentLTV"] == 60

    def test_high_interest_capped_to_12(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(rate=18.0), {})
        assert out["RLoan"]["CurrentStatus"]["CurrentInterestRate"] == 12.0

    def test_low_interest_floored_to_2(self):
        from port.rand.halong.mortgage.quality import quality_consistency_check
        out = quality_consistency_check(self._scaffold(rate=0.5), {})
        assert out["RLoan"]["CurrentStatus"]["CurrentInterestRate"] == 2.0
