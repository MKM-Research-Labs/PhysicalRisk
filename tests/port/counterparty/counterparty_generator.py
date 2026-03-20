# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

import json

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def gen(tmp_path):
    from port.src.counterparty import CounterpartyPortfolioGenerator
    return CounterpartyPortfolioGenerator(output_dir=tmp_path, verbose=False)


# ===========================================================================
# CounterpartyPortfolioGenerator.generate
# ===========================================================================

class TestCounterpartyGenerate:

    def test_returns_dict_with_required_keys(self, gen):
        result = gen.generate(count=2)
        assert "data" in result
        assert "file_path" in result
        assert "metadata" in result

    def test_data_is_list(self, gen):
        result = gen.generate(count=3)
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 3

    def test_default_count_uses_all_counterparties(self, gen):
        from port.src.counterparty import _ALL_COUNTERPARTIES
        result = gen.generate()
        assert len(result["data"]) == len(_ALL_COUNTERPARTIES)

    def test_creates_output_file(self, gen, tmp_path):
        gen.generate(count=2)
        output_file = tmp_path / "counterparty.json"
        assert output_file.exists()

    def test_output_file_is_valid_json(self, gen, tmp_path):
        gen.generate(count=2)
        data = json.loads((tmp_path / "counterparty.json").read_text())
        assert "counterparties" in data
        assert "generation_metadata" in data

    def test_metadata_has_total_generated(self, gen):
        result = gen.generate(count=4)
        assert result["metadata"]["total_generated"] == 4

    def test_file_path_is_pathlib_path(self, gen):
        from pathlib import Path
        result = gen.generate(count=1)
        assert isinstance(result["file_path"], Path)

    def test_zero_count_returns_empty(self, gen):
        result = gen.generate(count=0)
        assert result["data"] == []


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
        result = gen.generate(count=5)
        ids = [c["CounterpartySet"]["Party"]["PartyID"] for c in result["data"]]
        assert len(set(ids)) == 5


# ===========================================================================
# generate_counterparties convenience function
# ===========================================================================

class TestGenerateCounterpartiesFunction:

    def test_returns_dict(self, tmp_path):
        from port.src.counterparty import generate_counterparties
        result = generate_counterparties(output_dir=tmp_path, count=2, verbose=False)
        assert isinstance(result, dict)
        assert "data" in result

    def test_count_respected(self, tmp_path):
        from port.src.counterparty import generate_counterparties
        result = generate_counterparties(output_dir=tmp_path, count=3, verbose=False)
        assert len(result["data"]) == 3
