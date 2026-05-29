# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Tests for LoanCDM.to_pricer_inputs — the CDM -> LoanPricer adapter."""

import pytest

from config.models import (
    LOAN_DEFAULT_INSURANCE_RATE,
    LOAN_DEFAULT_RECOVERY_HAIRCUT,
)
from models.loan import LoanPricer
from port.cdm import LoanCDM


def _record(**overrides):
    rec = {
        "Mortgage": {
            "Header": {"MortgageID": "MORT-1", "PropertyID": "PROP-1"},
            "FinancialTerms": {
                "OriginalLoan": 400_000,
                "OriginalTerm": 300,        # months -> 25 years
                "OriginalLendingRate": 3.5,  # percent
                "InsuranceRate": 0.0025,
            },
            "CurrentStatus": {
                "OutstandingBalance": 350_000,
                "CurrentLTV": 70.0,          # percent -> property value 500_000
                "CurrentInterestRate": 5.0,  # percent -> 0.05
                "RemainingTerm": 240,        # months -> 20 years
            },
            "BorrowerDetails": {"BorrowerIncome": 90_000},
            "RiskAssessment": {
                "FloodRiskCategory": "High",
                "RecoveryHaircut": 0.25,
            },
        }
    }
    for section, fields in overrides.items():
        rec["Mortgage"].setdefault(section, {}).update(fields)
    return rec


class TestToPricerInputs:

    def test_renames_and_passthrough(self):
        out = LoanCDM().to_pricer_inputs(_record())
        assert out["mortgage_id"] == "MORT-1"
        assert out["property_id"] == "PROP-1"
        assert out["loan_amount"] == 350_000
        assert out["gross_annual_income"] == 90_000
        assert out["flood_risk_category"] == "High"

    def test_rate_percent_to_decimal(self):
        out = LoanCDM().to_pricer_inputs(_record())
        assert out["interest_rate"] == pytest.approx(0.05)

    def test_term_months_to_years(self):
        out = LoanCDM().to_pricer_inputs(_record())
        assert out["original_maturity"] == pytest.approx(25.0)
        assert out["current_term"] == pytest.approx(20.0)

    def test_property_value_derived_from_ltv(self):
        out = LoanCDM().to_pricer_inputs(_record())
        # 350_000 / (70/100) == 500_000
        assert out["property_value"] == pytest.approx(500_000)

    def test_property_value_falls_back_to_purchase_value(self):
        rec = _record()
        rec["Mortgage"]["CurrentStatus"]["CurrentLTV"] = None
        rec["Mortgage"]["FinancialTerms"]["PurchaseValue"] = 480_000
        out = LoanCDM().to_pricer_inputs(rec)
        assert out["property_value"] == pytest.approx(480_000)

    def test_per_loan_insurance_and_recovery_used(self):
        out = LoanCDM().to_pricer_inputs(_record())
        assert out["insurance_rate"] == pytest.approx(0.0025)
        assert out["recovery_haircut"] == pytest.approx(0.25)

    def test_insurance_and_recovery_fall_back_to_config(self):
        rec = _record()
        del rec["Mortgage"]["FinancialTerms"]["InsuranceRate"]
        del rec["Mortgage"]["RiskAssessment"]["RecoveryHaircut"]
        out = LoanCDM().to_pricer_inputs(rec)
        assert out["insurance_rate"] == pytest.approx(LOAN_DEFAULT_INSURANCE_RATE)
        assert out["recovery_haircut"] == pytest.approx(LOAN_DEFAULT_RECOVERY_HAIRCUT)

    def test_current_rate_falls_back_to_original(self):
        rec = _record()
        del rec["Mortgage"]["CurrentStatus"]["CurrentInterestRate"]
        out = LoanCDM().to_pricer_inputs(rec)
        assert out["interest_rate"] == pytest.approx(0.035)

    def test_output_feeds_pricer(self):
        out = LoanCDM().to_pricer_inputs(_record())
        result = LoanPricer().price_loan(
            **{k: v for k, v in out.items()
               if k not in ("mortgage_id", "property_id")}
        )
        assert result["mortgage_value"] > 0
        assert result["ltv_ratio"] == pytest.approx(0.7)

    def test_batch_price_consumes_adapter_output(self):
        inputs = LoanCDM().to_pricer_inputs(_record())
        results = LoanPricer().batch_price_loans([inputs])
        assert len(results) == 1
        assert results[0]["mortgage_id"] == "MORT-1"
        assert "error" not in results[0]
