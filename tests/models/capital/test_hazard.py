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

"""Site flood losses, the PRS payout and the borrower's year-end liquidity."""

import numpy as np
import pytest

from config.capital import BorrowerConfig, CapitalReliefConfig, HazardConfig, PRSConfig
from models.capital import flood_losses, prs_payout, simulate_drivers, year_end_liquidity
from models.capital.hazard import fixed_charges


def test_prs_payout_bounded_and_monotone():
    p = PRSConfig()
    levels = np.linspace(p.attach_level - 1, p.exhaust_level + 1, 500)
    pay = prs_payout(levels, p)
    assert pay.min() == 0.0 and pay.max() == pytest.approx(p.notional)
    assert np.all(np.diff(pay) >= 0)


def test_no_flood_losses_below_site_level_without_noise():
    b, h = BorrowerConfig(), HazardConfig()
    levels = np.array([h.site_flood_level - 0.5, h.site_flood_level])
    depth, rem, bi = flood_losses(levels, np.zeros(2), b, h)
    assert np.all(depth == 0) and np.all(rem == 0) and np.all(bi == 0)


def test_flood_losses_increase_with_depth():
    b, h = BorrowerConfig(), HazardConfig()
    levels = h.site_flood_level + np.array([0.1, 0.5, 1.0])
    _, rem, bi = flood_losses(levels, np.zeros(3), b, h)
    assert np.all(np.diff(rem) > 0) and np.all(np.diff(bi) > 0)


def test_insured_share_reduces_remediation_only():
    h = HazardConfig()
    levels = np.array([h.site_flood_level + 0.5])
    _, rem_half, bi_half = flood_losses(levels, np.zeros(1), BorrowerConfig(), h)
    _, rem_full, bi_full = flood_losses(
        levels, np.zeros(1), BorrowerConfig(insured_share_of_damage=1.0), h)
    assert rem_full[0] == 0.0 and rem_half[0] > 0.0
    assert bi_full[0] == bi_half[0]


def test_drivers_are_reproducible_and_sized():
    cfg = CapitalReliefConfig(n_paths=1_000)
    a, b = simulate_drivers(cfg), simulate_drivers(cfg)
    assert set(a) == {"z_ebitda", "gauge_level", "depth_noise"}
    for key in a:
        assert a[key].shape == (1_000,)
        assert np.array_equal(a[key], b[key])


def test_liquidity_is_opening_plus_earnings_less_charges_and_losses():
    b = BorrowerConfig()
    drivers = {"z_ebitda": np.zeros(1)}
    liq = year_end_liquidity(drivers, b, np.array([1.0]), np.array([0.5]),
                             np.array([2.0]), 0.25)
    expected = b.liquidity + b.ebitda - fixed_charges(b) - 0.25 - 1.0 - 0.5 + 2.0
    assert liq[0] == pytest.approx(expected)
