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

"""The import fallback in LoanCDM.to_pricer_inputs.

``to_pricer_inputs`` reads two defaults from ``config.models`` and falls back
to literals if that import fails. The fallback had no test, so it could have
drifted from the config values without anything noticing — and a silent
drift in an insurance rate or a recovery haircut is a pricing error, not a
cosmetic one.
"""

import sys

import pytest

from port.cdm.asset.loan.cdm import LoanCDM


_MORTGAGE = {
    "Mortgage": {
        "Header": {"MortgageID": "RLOAN-TEST", "PropertyID": "PROP-TEST"},
        "FinancialTerms": {"OriginalLoan": 250000, "LoanTerm": 25,
                           "InterestRate": 4.5},
        "CurrentStatus": {"OutstandingBalance": 200000, "CurrentLTV": 0.8,
                          "RemainingTerm": 240},
        "Application": {},
    }
}


def test_the_fallback_matches_the_configured_values():
    """The literals must equal what config.models holds.

    This is the check that makes the fallback safe. If someone retunes the
    insurance rate in config and leaves the literal behind, a run that could
    not import config would price on the stale number and say nothing.
    """
    from config.models import (
        LOAN_DEFAULT_INSURANCE_RATE,
        LOAN_DEFAULT_RECOVERY_HAIRCUT,
    )
    import inspect

    source = inspect.getsource(LoanCDM.to_pricer_inputs)
    assert f"LOAN_DEFAULT_INSURANCE_RATE = {LOAN_DEFAULT_INSURANCE_RATE}" in source
    assert f"LOAN_DEFAULT_RECOVERY_HAIRCUT = {LOAN_DEFAULT_RECOVERY_HAIRCUT}" in source


def test_pricer_inputs_are_produced_when_config_is_unimportable(monkeypatch):
    """A broken config import must not stop a loan being priced."""
    monkeypatch.setitem(sys.modules, "config.models", None)
    inputs = LoanCDM().to_pricer_inputs(_MORTGAGE)
    assert isinstance(inputs, dict)
    assert inputs


def test_the_same_inputs_are_produced_either_way(monkeypatch):
    """The fallback is a substitute, not a different pricing path."""
    with_config = LoanCDM().to_pricer_inputs(_MORTGAGE)
    monkeypatch.setitem(sys.modules, "config.models", None)
    without_config = LoanCDM().to_pricer_inputs(_MORTGAGE)
    assert with_config == without_config
