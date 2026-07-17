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

"""
Tests for port.src.counterparty — CounterpartyPortfolioGenerator.

Covers: generate (default count, custom count), _generate_one (structure,
rating pools per type, CSA logic), convenience function generate_counterparties.
"""

import pytest

import database
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") for every test in this module.

    The migrated counterparty writer persists through ``database``; rooting the backend at
    ``tmp_path`` isolates the write and lets assertions read back via
    ``database.get_counterparty_portfolio`` / ``list_counterparties``."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def gen(tmp_path):
    from port.src.counterparty import CounterpartyPortfolioGenerator
    return CounterpartyPortfolioGenerator(verbose=False)


# ===========================================================================
# CounterpartyPortfolioGenerator.generate
# ===========================================================================

class TestCounterpartyGenerate:

    def test_returns_dict_with_required_keys(self, gen):
        result = gen.generate(count=2)
        assert "data" in result
        assert "catchment" in result
        assert "metadata" in result

    def test_data_is_list(self, gen):
        # +1 because the generator always emits the fixed CTPY-REIT-001
        # entry alongside the random external pool of size ``count``.
        result = gen.generate(count=3)
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 4  # 1 REIT + 3 externals

    def test_default_count_uses_all_counterparties(self, gen):
        from port.src.counterparty import _ALL_COUNTERPARTIES
        result = gen.generate()
        # +1 for the fixed REIT counterparty
        assert len(result["data"]) == len(_ALL_COUNTERPARTIES) + 1

    def test_persists_portfolio(self, gen):
        result = gen.generate(count=2)
        assert database.get_counterparty_portfolio(result["catchment"]) is not None

    def test_persisted_portfolio_is_valid(self, gen):
        result = gen.generate(count=2)
        data = database.get_counterparty_portfolio(result["catchment"])
        assert "counterparties" in data
        assert "generation_metadata" in data

    def test_metadata_has_total_generated(self, gen):
        # +1 REIT prepended to the external pool of size ``count``
        result = gen.generate(count=4)
        assert result["metadata"]["total_generated"] == 5

    def test_result_reports_catchment(self, gen):
        result = gen.generate(count=1)
        assert result["catchment"] == database.active_catchment()

    def test_zero_count_returns_reit_only(self, gen):
        """count=0 still emits the fixed REIT entry."""
        result = gen.generate(count=0)
        assert len(result["data"]) == 1
        pid = result["data"][0]["CounterpartySet"]["Party"]["PartyID"]
        assert pid == "CTPY-REIT-001"


# ===========================================================================
# Structure of generated counterparty records
# ===========================================================================

class TestGeneratedStructure:

    def test_counterparty_has_counterparty_set(self, gen):
        result = gen.generate(count=1)
        ctpy = result["data"][0]
        assert "CounterpartySet" in ctpy

    def test_party_has_id(self, gen):
        result = gen.generate(count=1)
        ctpy = result["data"][0]
        party = ctpy["CounterpartySet"]["Party"]
        assert "PartyID" in party
        assert party["PartyID"].startswith("CTPY-")

    def test_party_has_name(self, gen):
        result = gen.generate(count=1)
        party = result["data"][0]["CounterpartySet"]["Party"]
        assert "PartyName" in party
        assert isinstance(party["PartyName"], str)

    def test_party_has_accounts(self, gen):
        result = gen.generate(count=1)
        party = result["data"][0]["CounterpartySet"]["Party"]
        assert "Accounts" in party
        assert len(party["Accounts"]) >= 1

    def test_party_has_contact_info(self, gen):
        result = gen.generate(count=1)
        party = result["data"][0]["CounterpartySet"]["Party"]
        assert "ContactInformation" in party
        assert "PrimaryEmail" in party["ContactInformation"]

    def test_party_has_natural_person(self, gen):
        result = gen.generate(count=1)
        party = result["data"][0]["CounterpartySet"]["Party"]
        assert "NaturalPersons" in party
        assert len(party["NaturalPersons"]) == 1

    def test_platform_has_credit_rating(self, gen):
        result = gen.generate(count=3)
        for ctpy in result["data"]:
            platform = ctpy["CounterpartySet"]["_platform"]
            assert "CreditRating" in platform
            assert platform["CreditRating"] in [
                "AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"
            ]

    def test_counterparties_list_has_two_parties(self, gen):
        result = gen.generate(count=1)
        counterparties = result["data"][0]["CounterpartySet"]["Counterparties"]
        assert len(counterparties) == 2

    def test_isda_master_agreement_is_true(self, gen):
        result = gen.generate(count=2)
        for ctpy in result["data"]:
            platform = ctpy["CounterpartySet"]["_platform"]
            assert platform["ISDAMasterAgreement"] is True

    def test_bank_type_has_csa(self, gen):
        """Banks always have CSAAgreement = True."""
        from port.src.counterparty import _BANK_NAMES
        result = gen.generate(count=len(_BANK_NAMES))
        for ctpy in result["data"][:len(_BANK_NAMES)]:
            platform = ctpy["CounterpartySet"]["_platform"]
            if platform.get("PartyType") == "Bank":
                assert platform["CSAAgreement"] is True

    def test_unique_party_ids(self, gen):
        # 1 REIT + 5 externals = 6 unique IDs
        result = gen.generate(count=5)
        ids = [c["CounterpartySet"]["Party"]["PartyID"] for c in result["data"]]
        assert len(set(ids)) == 6


# ===========================================================================
# generate_counterparties convenience function
# ===========================================================================

class TestGenerateCounterpartiesFunction:

    def test_returns_dict(self, tmp_path):
        from port.src.counterparty import generate_counterparties
        result = generate_counterparties(count=2, verbose=False)
        assert isinstance(result, dict)
        assert "data" in result

    def test_count_respected(self, tmp_path):
        from port.src.counterparty import generate_counterparties
        # +1 REIT prepended to the external pool of size ``count``
        result = generate_counterparties(count=3, verbose=False)
        assert len(result["data"]) == 4
