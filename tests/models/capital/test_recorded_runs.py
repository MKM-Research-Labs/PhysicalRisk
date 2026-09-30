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

"""The package reproduces the recorded study runs in ``docs/capital``.

The package is the governed form of those two studies. Its config hashes must
match the recorded ones exactly -- same parameters, same field names -- and its
figures must match to within the last floating-point digit: the runs were
recorded on another machine, and summation order in numpy differs slightly
between builds.
"""

import json
from pathlib import Path

import pytest

from config.capital import IG_CREDIT_SPREAD_BENEFIT, CapitalReliefConfig, OverTermConfig
from config.loan import CREDIT_RATING_SPREADS
from models.capital import one_year, over_term

CAPITAL_DOCS = Path(__file__).resolve().parents[3] / "docs" / "capital"


def _recorded(name):
    return json.loads((CAPITAL_DOCS / name).read_text())


def _assert_close(recorded, produced, path=""):
    if isinstance(recorded, dict):
        assert set(recorded) == set(produced), path
        for key in recorded:
            _assert_close(recorded[key], produced[key], f"{path}/{key}")
    elif isinstance(recorded, list):
        assert len(recorded) == len(produced), path
        for i, (a, b) in enumerate(zip(recorded, produced)):
            _assert_close(a, b, f"{path}[{i}]")
    elif isinstance(recorded, float):
        assert produced == pytest.approx(recorded, rel=1e-12, abs=1e-15), path
    else:
        assert produced == recorded, path


@pytest.mark.parametrize("name,module,cfg", [
    ("prs_capital_relief_audit.json", one_year, CapitalReliefConfig()),
    ("prs_multi_year_audit.json", over_term, OverTermConfig()),
])
def test_recorded_run_reproduces(name, module, cfg):
    recorded = _recorded(name)
    produced = json.loads(json.dumps(module.run(cfg), default=float))
    assert produced["audit"]["config_sha256"] == recorded["audit"]["config_sha256"]
    for part in (recorded, produced):
        part["audit"].pop("run_utc")
    _assert_close(recorded, produced)


def test_ig_spread_benefit_comes_from_the_loan_pricer():
    """One source for what a grade is worth: the loan pricer's rating spreads."""
    assert IG_CREDIT_SPREAD_BENEFIT == CREDIT_RATING_SPREADS["BB"] - CREDIT_RATING_SPREADS["BBB"]
    assert CapitalReliefConfig().capital.ig_credit_spread_benefit == IG_CREDIT_SPREAD_BENEFIT
