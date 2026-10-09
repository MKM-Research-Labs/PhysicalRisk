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

"""CDM fields the XVA model reads: netting set, CSA terms, settlement lag.

Covers the PRS trade fields (Header.NettingSetID, Payouts.SettlementDays), the
counterparty CreditSupport block and its validation, and the synthetic block
the counterparty generator attaches (docs/xva/project_plan.md, WP0).
"""

from datetime import datetime

import pytest

from config.port import NETTING_SET_PREFIX, PRS_SETTLEMENT_DAYS, SYNTHETIC_CSA_TERMS
from port.cdm.ctpy import CounterpartyCDM
from port.cdm.ctpy._credit_support import credit_support_errors
from port.cdm.prs import PhysicalRiskSwapCDM
from port.src.counterparty._credit_support import netting_set_id, with_credit_support


def _ctpy(platform=None, party_id="CTPY-1"):
    return {"CounterpartySet": {
        "Party": {"PartyID": party_id, "PartyName": "Test Re"},
        "Counterparties": [{"CounterpartyRole": "Party1", "PartyRef": "MKM"},
                           {"CounterpartyRole": "Party2", "PartyRef": party_id}],
        "_platform": platform or {},
    }}


def _netting_set(**overrides):
    ns = {"NettingSetID": "NS-1", "MasterAgreement": "ISDA2002", "CloseOutNetting": True,
          "CsaType": "VM", "Threshold": 0.0, "MinimumTransferAmount": 250_000.0,
          "MarginPeriodOfRiskDays": 10}
    ns.update(overrides)
    return ns


class TestPrsTradeFields:

    def test_schema_lists_netting_set_and_settlement_days(self):
        fields = PhysicalRiskSwapCDM().list_all_fields()
        assert "PhysicalSwap.Header.NettingSetID" in fields
        assert "PhysicalSwap.Payouts.SettlementDays" in fields

    def test_mapping_carries_both_fields(self):
        flat = PhysicalRiskSwapCDM().create_mapping({"PhysicalSwap": {
            "Header": {"SwapID": "PRS-1", "NettingSetID": "NS-CTPY-1"},
            "Payouts": {"SettlementDays": 5}}})
        assert flat["netting_set_id"] == "NS-CTPY-1"
        assert flat["settlement_days"] == 5

    def test_mapping_omits_them_on_older_trades(self):
        flat = PhysicalRiskSwapCDM().create_mapping(
            {"PhysicalSwap": {"Header": {"SwapID": "PRS-1"}}})
        assert "netting_set_id" not in flat and "settlement_days" not in flat

    def test_book_record_references_the_counterparty_netting_set(self):
        from port.src.book.book_common._records import _build_cdm_record
        record = _build_cdm_record(
            swap_id="PRS-1", gauge_id="G1", gauge_name="Gauge", catchment_id="thames",
            counterparty_id="CTPY-1", counterparty_name="Test Re", is_payer=True,
            notional=5e6, tenor=1, trigger="severe", trade_spread_bps=50,
            fair_spread_bps=48, npv=0, premium_leg_pv=0, protection_leg_pv=0,
            risky_annuity=0.9, trade_date=datetime(2026, 10, 9))
        swap = record["PhysicalSwap"]
        assert swap["Header"]["NettingSetID"] == netting_set_id("CTPY-1")
        assert swap["Payouts"]["SettlementDays"] == PRS_SETTLEMENT_DAYS


class TestCreditSupportValidation:

    def test_absent_block_is_valid(self):
        assert credit_support_errors({}) == []
        assert CounterpartyCDM().validate(_ctpy()) == {}

    def test_well_formed_block_is_valid(self):
        assert credit_support_errors(
            {"CreditSupport": {"NettingSets": [_netting_set()]}}) == []

    @pytest.mark.parametrize("bad, message", [
        ({"NettingSetID": ""}, "Missing NettingSetID"),
        ({"CsaType": "Tri-party"}, "Invalid CsaType"),
        ({"MasterAgreement": "GMRA"}, "Invalid MasterAgreement"),
        ({"CloseOutNetting": "yes"}, "CloseOutNetting must be true or false"),
        ({"Threshold": -1.0}, "Threshold must be a non-negative number"),
        ({"MarginPeriodOfRiskDays": True}, "MarginPeriodOfRiskDays must be"),
        ({"InitialMarginReceived": "0"}, "InitialMarginReceived must be"),
    ])
    def test_each_defect_is_reported(self, bad, message):
        errors = credit_support_errors(
            {"CreditSupport": {"NettingSets": [_netting_set(**bad)]}})
        assert any(message in e for e in errors), errors

    def test_duplicate_ids_are_reported(self):
        errors = credit_support_errors(
            {"CreditSupport": {"NettingSets": [_netting_set(), _netting_set()]}})
        assert errors == ["NettingSets[1]: Duplicate NettingSetID 'NS-1'"]

    def test_cdm_validate_surfaces_the_section(self):
        record = _ctpy()
        record["CounterpartySet"]["CreditSupport"] = {
            "NettingSets": [_netting_set(CsaType="Bad")]}
        assert "CreditSupport" in CounterpartyCDM().validate(record)

    def test_mapping_counts_netting_sets(self):
        record = _ctpy()
        assert CounterpartyCDM().create_mapping(record)["netting_set_count"] == 0
        record["CounterpartySet"]["CreditSupport"] = {"NettingSets": [_netting_set()]}
        assert CounterpartyCDM().create_mapping(record)["netting_set_count"] == 1


class TestSyntheticCreditSupport:

    def test_netting_set_id_is_prefixed_party_id(self):
        assert netting_set_id("CTPY-1") == f"{NETTING_SET_PREFIX}CTPY-1"

    def test_financial_with_csa_gets_financial_terms(self):
        record = with_credit_support(_ctpy({
            "PartyType": "Reinsurer", "CSAAgreement": True,
            "ISDAMasterAgreement": True, "NettingAgreement": True}))
        ns = record["CounterpartySet"]["CreditSupport"]["NettingSets"][0]
        assert ns["NettingSetID"] == netting_set_id("CTPY-1")
        assert ns["CsaType"] == "VM" and ns["CloseOutNetting"] is True
        assert ns["Threshold"] == SYNTHETIC_CSA_TERMS["financial"]["Threshold"]

    def test_corporate_with_csa_gets_corporate_threshold(self):
        record = with_credit_support(_ctpy({
            "PartyType": "Utility", "CSAAgreement": True,
            "ISDAMasterAgreement": True, "NettingAgreement": False}))
        ns = record["CounterpartySet"]["CreditSupport"]["NettingSets"][0]
        assert ns["Threshold"] == SYNTHETIC_CSA_TERMS["corporate"]["Threshold"]
        assert ns["CloseOutNetting"] is False

    def test_no_csa_means_no_margin_terms(self):
        record = with_credit_support(_ctpy({"PartyType": "Utility", "CSAAgreement": False}))
        ns = record["CounterpartySet"]["CreditSupport"]["NettingSets"][0]
        assert ns["CsaType"] == "None" and ns["MasterAgreement"] == "None"
        assert "Threshold" not in ns and "MarginPeriodOfRiskDays" not in ns

    def test_synthetic_block_passes_validation(self):
        for platform in ({"PartyType": "Bank", "CSAAgreement": True,
                          "ISDAMasterAgreement": True, "NettingAgreement": True},
                         {"PartyType": "Utility", "CSAAgreement": False}):
            assert CounterpartyCDM().validate(with_credit_support(_ctpy(platform))) == {}
