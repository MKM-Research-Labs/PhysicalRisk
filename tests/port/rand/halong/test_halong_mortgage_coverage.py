# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for halong mortgage field generators — the InsuranceRate /
RecoveryHaircut decimal branches, the integer default branch and RLoanID."""

import random

import pytest

from port.rand.halong.mortgage import generators


@pytest.fixture(autouse=True)
def _seed():
    random.seed(20260614)


class TestHalongMortgageGeneratorsCoverage:
    def test_insurance_rate_decimal(self):
        v = generators.generate_decimal_value("InsuranceRate", {})  # line 93
        assert 0.0015 <= v <= 0.003

    def test_recovery_haircut_decimal(self):
        v = generators.generate_decimal_value("RecoveryHaircut", {})  # line 95
        assert 0.15 <= v <= 0.30

    def test_integer_unknown_field_default_branch(self):
        for _ in range(20):
            v = generators.generate_integer_value("UnknownIntField", {})  # line 150
            assert 1 <= v <= 10

    def test_text_rloan_id_uses_provided_id(self):
        assert generators.generate_text_value(
            "RLoanID", 0, {"mortgage_id": "RLOAN-X"}) == "RLOAN-X"  # line 175
        # falls back to a generated uuid when the id is absent
        v = generators.generate_text_value("RLoanID", 0, {})
        assert isinstance(v, str) and v
