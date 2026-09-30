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

"""One-year capital relief: PD, grade, attribution and economics."""

import math
from dataclasses import replace

import pytest

from config.capital import STATUS, CapitalReliefConfig
from models.capital import one_year

FAST = CapitalReliefConfig(n_paths=200_000)


@pytest.fixture(scope="module")
def fast():
    return one_year.run(FAST)


def test_reproducible_for_same_seed(fast):
    again = one_year.run(FAST)
    assert again["results"] == fast["results"]
    assert again["audit"]["config_sha256"] == fast["audit"]["config_sha256"]


def test_config_hash_changes_with_config():
    other = replace(FAST, prs=replace(FAST.prs, notional=5.0))
    assert other.fingerprint() != FAST.fingerprint()


def test_zero_notional_prs_reproduces_baseline():
    out = one_year.run(replace(FAST, prs=replace(FAST.prs, notional=0.0)))
    r = out["results"]
    assert r["with_prs"]["pd_1y"] == r["without_prs"]["pd_1y"]
    assert out["economics"]["prs_rate_on_line"] == 0.0


def test_prs_only_changes_outcomes_through_payout_or_premium(fast):
    a = fast["attribution"]
    base = fast["results"]["without_prs"]["pd_1y"]
    prs = fast["results"]["with_prs"]["pd_1y"]
    assert prs == pytest.approx(
        base - a["defaults_averted_by_prs"] + a["defaults_caused_by_premium"], abs=1e-12)


def test_pd_decomposition_adds_up(fast):
    a = fast["attribution"]
    assert (a["pd_no_hazard_component"] + a["pd_hazard_attributable"]
            == pytest.approx(fast["results"]["without_prs"]["pd_1y"]))


def test_default_calibration_crosses_investment_grade(fast):
    """The headline claim, pinned so that calibration drift is caught."""
    r = fast["results"]
    assert r["without_prs"]["grade"] == "BB+"
    assert r["with_prs"]["grade"] == "BBB-"
    assert fast["economics"]["borrower_funding_saving_if_ig"] > 0.0


def test_no_funding_saving_without_a_grade_crossing():
    out = one_year.run(replace(FAST, prs=replace(FAST.prs, notional=0.5)))
    assert out["results"]["with_prs"]["grade"].startswith("BB")
    assert out["economics"]["borrower_funding_saving_if_ig"] == 0.0


def test_pd_given_flood_is_undefined_when_the_site_never_floods():
    dry = replace(FAST, hazard=replace(FAST.hazard, site_flood_level=50.0))
    r = one_year.run(dry)["results"]["without_prs"]
    assert math.isnan(r["pd_given_site_flood"])
    assert r["pd_given_no_flood"] == r["pd_1y"]


def test_audit_record_complete(fast):
    audit = fast["audit"]
    for key in ("run_utc", "config_sha256", "seed", "n_paths", "status", "config"):
        assert key in audit
    assert audit["status"] == STATUS
    assert audit["n_paths"] == FAST.n_paths


def test_notional_sweep_is_monotone_in_premium():
    small = CapitalReliefConfig(n_paths=50_000)
    rows = one_year.notional_sweep([0, 3, 6], small)
    assert [r["notional"] for r in rows] == [0.0, 3.0, 6.0]
    premiums = [r["premium"] for r in rows]
    assert premiums == sorted(premiums) and premiums[0] == 0.0
    assert rows[-1]["pd_1y"] <= rows[0]["pd_1y"]


def test_notional_sweep_defaults_to_the_standard_config(monkeypatch):
    seen = []
    monkeypatch.setattr(one_year, "run", lambda cfg: seen.append(cfg) or {
        "results": {"with_prs": {"pd_1y": 0.0, "grade": "A-"}},
        "economics": {"prs_premium": 0.0}})
    one_year.notional_sweep([1])
    assert seen[0].n_paths == CapitalReliefConfig().n_paths
    assert seen[0].prs.notional == 1.0
