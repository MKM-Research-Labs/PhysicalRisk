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

"""Tests for prs_capital_relief_example (run: pytest -q)."""

from dataclasses import replace

import numpy as np
import pytest

import prs_capital_relief_example as m

FAST = m.ExampleConfig(n_paths=200_000)


# --- building blocks -------------------------------------------------------
def test_irb_rw_matches_basel_reference_value():
    # Basel II illustrative table: corporate, PD 1%, LGD 45%, M 2.5 -> 92.32%
    assert m.irb_corporate_rw(0.01, 0.45, 2.5) == pytest.approx(0.9232, abs=5e-4)


def test_irb_rw_applies_pd_floor():
    assert m.irb_corporate_rw(0.0, 0.45, 2.5) == m.irb_corporate_rw(0.0005, 0.45, 2.5)


def test_prs_payout_bounded_and_monotone():
    p = m.PRSConfig()
    levels = np.linspace(p.attach_level - 1, p.exhaust_level + 1, 500)
    pay = m.prs_payout(levels, p)
    assert pay.min() == 0.0 and pay.max() == pytest.approx(p.notional)
    assert np.all(np.diff(pay) >= 0)


def test_no_flood_losses_below_site_level_without_noise():
    b, h = m.BorrowerConfig(), m.HazardConfig()
    levels = np.array([h.site_flood_level - 0.5, h.site_flood_level])
    depth, rem, bi = m.flood_losses(levels, np.zeros(2), b, h)
    assert np.all(depth == 0) and np.all(rem == 0) and np.all(bi == 0)


def test_flood_losses_increase_with_depth():
    b, h = m.BorrowerConfig(), m.HazardConfig()
    levels = h.site_flood_level + np.array([0.1, 0.5, 1.0])
    _, rem, bi = m.flood_losses(levels, np.zeros(3), b, h)
    assert np.all(np.diff(rem) > 0) and np.all(np.diff(bi) > 0)


@pytest.mark.parametrize("pd,grade", [(0.0030, "BBB-"), (0.0035, "BBB-"),
                                      (0.0036, "BB+"), (0.0060, "BB+")])
def test_master_scale_boundaries(pd, grade):
    assert m.grade_for_pd(pd)[0] == grade


def test_investment_grade_boundary_is_sa_cliff():
    assert m.grade_for_pd(0.0035)[1] == 0.75 and m.grade_for_pd(0.0036)[1] == 1.00


# --- orchestration ---------------------------------------------------------
def test_reproducible_for_same_seed():
    a, b = m.run(FAST), m.run(FAST)
    assert a["results"] == b["results"]
    assert a["audit"]["config_sha256"] == b["audit"]["config_sha256"]


def test_config_hash_changes_with_config():
    other = replace(FAST, prs=replace(FAST.prs, notional=5.0))
    assert other.fingerprint() != FAST.fingerprint()


def test_zero_notional_prs_reproduces_baseline():
    out = m.run(replace(FAST, prs=replace(FAST.prs, notional=0.0)))
    r = out["results"]
    assert r["with_prs"]["pd_1y"] == r["without_prs"]["pd_1y"]


def test_prs_only_changes_outcomes_through_payout_or_premium():
    out = m.run(FAST)
    a = out["attribution"]
    base, prs = out["results"]["without_prs"]["pd_1y"], out["results"]["with_prs"]["pd_1y"]
    assert prs == pytest.approx(base - a["defaults_averted_by_prs"]
                                + a["defaults_caused_by_premium"], abs=1e-12)


def test_pd_decomposition_adds_up():
    a = m.run(FAST)["attribution"]
    base = m.run(FAST)["results"]["without_prs"]["pd_1y"]
    assert a["pd_no_hazard_component"] + a["pd_hazard_attributable"] == pytest.approx(base)


def test_default_calibration_crosses_investment_grade():
    """Headline claim of the worked example, pinned so calibration drift is caught."""
    r = m.run(FAST)["results"]
    assert r["without_prs"]["grade"] == "BB+"
    assert r["with_prs"]["grade"] == "BBB-"


def test_audit_record_complete():
    audit = m.run(FAST)["audit"]
    for key in ("run_utc", "config_sha256", "seed", "n_paths", "status", "config"):
        assert key in audit
