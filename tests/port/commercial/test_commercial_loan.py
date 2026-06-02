# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the commercial loan generator."""

import json
import re

import pytest

from port.cdm import LoanCDM
from port.src.commercial import CommercialPortfolioGenerator
from port.src.commercial_loan import (
    CommercialLoanPortfolioGenerator,
    _build_commercial_loan,
    generate_commercial_loans,
)


# ---------------------------------------------------------------------------
# _build_commercial_loan — unit tests on a single asset stub
# ---------------------------------------------------------------------------


def _stub_asset(commercial_type: str = "Office", value: float = 50_000_000):
    return {
        "CommercialAsset": {
            "Header": {"PropertyID": "CPROP-stub0001", "CatchmentID": "thames",
                       "UPRN": "UPRN-CPROP-stub0001"},
            "Valuation": {"PropertyValue": value},
            "CommercialAttributes": {"CommercialType": commercial_type},
            "RiskAssessment": {"OverallFloodRisk": "Low"},
        }
    }


class TestBuildCommercialLoan:

    def test_returns_mortgage_root(self):
        loan = _build_commercial_loan(_stub_asset())
        assert "Mortgage" in loan

    def test_loan_id_format(self):
        loan = _build_commercial_loan(_stub_asset())
        lid = loan["Mortgage"]["Header"]["MortgageID"]
        assert re.match(r"^CLOAN-[a-f0-9]{8}$", lid)

    def test_property_id_passthrough(self):
        loan = _build_commercial_loan(_stub_asset())
        assert loan["Mortgage"]["Header"]["PropertyID"] == "CPROP-stub0001"

    def test_uprn_passthrough(self):
        loan = _build_commercial_loan(_stub_asset())
        assert loan["Mortgage"]["Header"]["UPRN"] == "UPRN-CPROP-stub0001"

    def test_ltv_in_commercial_range(self):
        for _ in range(40):
            loan = _build_commercial_loan(_stub_asset())
            ltv = loan["Mortgage"]["FinancialTerms"]["OriginalLTV"]
            assert 0.55 <= ltv <= 0.70

    def test_original_loan_matches_ltv_and_value(self):
        loan = _build_commercial_loan(_stub_asset(value=100_000_000))
        terms = loan["Mortgage"]["FinancialTerms"]
        # Loan = round(value * ltv, -3) — allow ±1000 rounding tolerance.
        expected = round(100_000_000 * terms["OriginalLTV"], -3)
        assert terms["OriginalLoan"] == expected

    def test_term_is_5_7_10_or_15_years(self):
        seen = set()
        for _ in range(60):
            loan = _build_commercial_loan(_stub_asset())
            t = loan["Mortgage"]["FinancialTerms"]["OriginalTerm"]
            assert t in (60, 84, 120, 180)
            seen.add(t)
        # Sanity: across 60 draws we should hit at least 3 of 4 buckets.
        assert len(seen) >= 3

    def test_rate_in_commercial_range(self):
        for _ in range(40):
            loan = _build_commercial_loan(_stub_asset())
            rate = loan["Mortgage"]["FinancialTerms"]["OriginalLendingRate"]
            assert 0.045 <= rate <= 0.07

    def test_occupancy_type_is_investment(self):
        for ctype in ("Office", "Retail", "Hotel", "MultiFamily", "MixedUse"):
            loan = _build_commercial_loan(_stub_asset(ctype))
            assert loan["Mortgage"]["Application"]["OccupancyType"] == "Investment"

    def test_repayment_type_in_allowed_set(self):
        allowed = {"Interest only", "Part and part", "Repayment"}
        for _ in range(40):
            loan = _build_commercial_loan(_stub_asset())
            rt = loan["Mortgage"]["Features"]["RepaymentType"]
            assert rt in allowed

    def test_currency_matches_catchment(self):
        from config import config
        loan = _build_commercial_loan(_stub_asset())
        assert loan["Mortgage"]["FinancialTerms"]["currency"] == config.CURRENCY

    def test_flood_risk_category_inherited_from_asset(self):
        asset = _stub_asset()
        asset["CommercialAsset"]["RiskAssessment"]["OverallFloodRisk"] = "High"
        loan = _build_commercial_loan(asset)
        assert loan["Mortgage"]["RiskAssessment"]["FloodRiskCategory"] == "High"

    def test_outstanding_balance_le_original_loan(self):
        for _ in range(40):
            loan = _build_commercial_loan(_stub_asset())
            ol = loan["Mortgage"]["FinancialTerms"]["OriginalLoan"]
            ob = loan["Mortgage"]["CurrentStatus"]["OutstandingBalance"]
            assert ob <= ol

    def test_interest_only_outstanding_equals_original(self):
        # Force interest-only by exhaustion: try until we see one.
        # With 55% prior for interest-only, ~10 trials suffices.
        for _ in range(30):
            loan = _build_commercial_loan(_stub_asset())
            if loan["Mortgage"]["Features"]["RepaymentType"] == "Interest only":
                ol = loan["Mortgage"]["FinancialTerms"]["OriginalLoan"]
                ob = loan["Mortgage"]["CurrentStatus"]["OutstandingBalance"]
                assert ob == ol
                return
        pytest.skip("no interest-only draw in 30 trials (unexpected)")

    def test_loan_validates_against_loan_cdm(self):
        cdm = LoanCDM()
        loan = _build_commercial_loan(_stub_asset())
        # _commercial_meta is a side-channel — strip before CDM validate.
        loan.pop("_commercial_meta", None)
        errors = cdm.validate(loan)
        assert errors == {}, f"validation errors: {errors}"


# ---------------------------------------------------------------------------
# CommercialLoanPortfolioGenerator end-to-end with a real commercial.json
# ---------------------------------------------------------------------------


@pytest.fixture
def commercial_portfolio_in_tmp(tmp_path):
    """Generate a real commercial.json under tmp_path."""
    gen = CommercialPortfolioGenerator(output_dir=tmp_path, verbose=False)
    gen.generate(count=10)
    return tmp_path


@pytest.mark.generator
class TestCommercialLoanPortfolioGenerator:

    def test_writes_commercial_loan_json(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        gen = CommercialLoanPortfolioGenerator(output_dir=tmp_dir, verbose=False)
        result = gen.generate()
        assert (tmp_dir / "commercial_loan.json").exists()
        assert result["file_path"] == tmp_dir / "commercial_loan.json"

    def test_one_loan_per_asset(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        result = CommercialLoanPortfolioGenerator(output_dir=tmp_dir, verbose=False).generate()
        assert len(result["data"]["commercial_loans"]) == 10

    def test_1_to_1_linkage_with_assets(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        result = CommercialLoanPortfolioGenerator(output_dir=tmp_dir, verbose=False).generate()
        commercial = json.loads((tmp_dir / "commercial.json").read_text())
        asset_ids = {a["CommercialAsset"]["Header"]["PropertyID"]
                     for a in commercial["commercial_assets"]}
        loan_pids = {l["Mortgage"]["Header"]["PropertyID"]
                     for l in result["data"]["commercial_loans"]}
        assert asset_ids == loan_pids

    def test_loan_ids_unique(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        result = CommercialLoanPortfolioGenerator(output_dir=tmp_dir, verbose=False).generate()
        ids = [l["Mortgage"]["Header"]["MortgageID"]
               for l in result["data"]["commercial_loans"]]
        assert len(ids) == len(set(ids))

    def test_processing_stats(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        result = CommercialLoanPortfolioGenerator(output_dir=tmp_dir, verbose=False).generate()
        assert result["processing_stats"]["successful"] == 10
        assert result["processing_stats"]["total"] == 10

    def test_metadata_written(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        CommercialLoanPortfolioGenerator(output_dir=tmp_dir, verbose=False).generate()
        d = json.loads((tmp_dir / "commercial_loan.json").read_text())
        meta = d["generation_metadata"]
        assert meta["total_loans_generated"] == 10
        assert meta["linked_commercial_assets"] == 10
        assert meta["catchment"] == "thames"

    def test_missing_commercial_raises(self, tmp_path):
        # Don't generate a commercial portfolio — loan generator must refuse.
        with pytest.raises(FileNotFoundError):
            CommercialLoanPortfolioGenerator(output_dir=tmp_path, verbose=False).generate()

    def test_convenience_function(self, commercial_portfolio_in_tmp):
        tmp_dir = commercial_portfolio_in_tmp
        result = generate_commercial_loans(output_dir=tmp_dir)
        assert len(result["data"]["commercial_loans"]) == 10
