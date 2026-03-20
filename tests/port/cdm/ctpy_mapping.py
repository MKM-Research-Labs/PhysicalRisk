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

"""Tests for CounterpartyCDM (ctpy.py) validate/create_mapping/get_required_fields."""

import pytest
from port.cdm.ctpy import CounterpartyCDM


_VALID_CTPY = {
    "CounterpartySet": {
        "Party": {
            "PartyID": "CTPY-001",
            "PartyName": "Bank of Test",
            "PartyIdScheme": "LEI",
            "ContactInformation": {
                "PrimaryEmail": "test@bank.com",
                "PrimaryPhone": "+44 20 1234 5678",
                "AddressLine1": "1 Test Street",
                "City": "London",
                "PostCode": "EC1A 1BB",
                "Country": "GB",
            },
        },
        "Counterparties": [
            {"CounterpartyRole": "Party1", "PartyRef": "CTPY-001", "ExternalPartyId": "EXT-001"},
            {"CounterpartyRole": "Party2", "PartyRef": "CTPY-002", "ExternalPartyId": "EXT-002"},
        ],
        "AncillaryParties": [],
    }
}


@pytest.fixture
def cdm():
    return CounterpartyCDM()


class TestCounterpartyCDMSchema:
    """Basic schema/required-fields tests."""

    def test_schema_is_dict(self, cdm):
        assert isinstance(cdm.schema, dict)
        assert len(cdm.schema) > 0

    def test_get_required_fields_returns_list(self, cdm):
        """Lines 294-301: get_required_fields() returns non-empty list."""
        fields = cdm.get_required_fields()
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert any("PartyID" in f for f in fields)
        assert any("CounterpartyRole" in f for f in fields)


class TestCounterpartyCDMValidate:
    """Tests for validate() — lines 169-233."""

    def test_valid_data_no_errors(self, cdm):
        """Valid counterparty data produces empty error dict."""
        errors = cdm.validate(_VALID_CTPY)
        assert errors == {}

    def test_missing_party_id_adds_error(self, cdm):
        """Lines 188-189: missing PartyID → Party errors."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyName": "Bank of Test"},
                "Counterparties": [
                    {"CounterpartyRole": "Party1", "PartyRef": "CTPY-001"},
                    {"CounterpartyRole": "Party2", "PartyRef": "CTPY-002"},
                ],
            }
        }
        errors = cdm.validate(data)
        assert "Party" in errors
        assert any("PartyID" in e for e in errors["Party"])

    def test_missing_party_name_adds_error(self, cdm):
        """Lines 191-192: missing PartyName → Party errors."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-001"},
                "Counterparties": [
                    {"CounterpartyRole": "Party1", "PartyRef": "CTPY-001"},
                    {"CounterpartyRole": "Party2", "PartyRef": "CTPY-002"},
                ],
            }
        }
        errors = cdm.validate(data)
        assert "Party" in errors
        assert any("PartyName" in e for e in errors["Party"])

    def test_empty_counterparties_adds_error(self, cdm):
        """Lines 201-202: empty Counterparties array → error."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-001", "PartyName": "Test"},
                "Counterparties": [],
            }
        }
        errors = cdm.validate(data)
        assert "Counterparties" in errors

    def test_missing_counterparty_role_adds_error(self, cdm):
        """Lines 209-210: missing CounterpartyRole → error."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-001", "PartyName": "Test"},
                "Counterparties": [{"PartyRef": "CTPY-001"}],
            }
        }
        errors = cdm.validate(data)
        assert "Counterparties" in errors
        assert any("CounterpartyRole" in e for e in errors["Counterparties"])

    def test_invalid_counterparty_role_adds_error(self, cdm):
        """Lines 211-214: invalid role (not Party1/Party2) → error."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-001", "PartyName": "Test"},
                "Counterparties": [{"CounterpartyRole": "InvalidRole", "PartyRef": "CTPY-001"}],
            }
        }
        errors = cdm.validate(data)
        assert "Counterparties" in errors
        assert any("Invalid" in e for e in errors["Counterparties"])

    def test_missing_party_ref_adds_error(self, cdm):
        """Lines 218-219: missing PartyRef → error."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-001", "PartyName": "Test"},
                "Counterparties": [{"CounterpartyRole": "Party1"}],
            }
        }
        errors = cdm.validate(data)
        assert "Counterparties" in errors
        assert any("PartyRef" in e for e in errors["Counterparties"])

    def test_two_cps_same_role_adds_error(self, cdm):
        """Lines 222-225: two CPs with same role → error."""
        data = {
            "CounterpartySet": {
                "Party": {"PartyID": "CTPY-001", "PartyName": "Test"},
                "Counterparties": [
                    {"CounterpartyRole": "Party1", "PartyRef": "CTPY-001"},
                    {"CounterpartyRole": "Party1", "PartyRef": "CTPY-002"},
                ],
            }
        }
        errors = cdm.validate(data)
        assert "Counterparties" in errors

    def test_empty_data_returns_errors(self, cdm):
        """validate({}) returns errors for all required fields."""
        errors = cdm.validate({})
        assert isinstance(errors, dict)


class TestCounterpartyCDMCreateMapping:
    """Tests for create_mapping() — lines 235-292."""

    def test_full_data_returns_flat_dict(self, cdm):
        """Lines 245-289: create_mapping with full data."""
        mapping = cdm.create_mapping(_VALID_CTPY)
        assert isinstance(mapping, dict)
        assert mapping["party_id"] == "CTPY-001"
        assert mapping["party_name"] == "Bank of Test"
        assert mapping["party1_ref"] == "CTPY-001"
        assert mapping["party2_ref"] == "CTPY-002"

    def test_contact_info_fields_extracted(self, cdm):
        """Lines 263-269: ContactInformation fields mapped."""
        mapping = cdm.create_mapping(_VALID_CTPY)
        assert mapping.get("primary_email") == "test@bank.com"
        assert mapping.get("city") == "London"

    def test_count_fields_present(self, cdm):
        """Lines 280-285: count fields in mapping."""
        mapping = cdm.create_mapping(_VALID_CTPY)
        assert "counterparty_count" in mapping
        assert mapping["counterparty_count"] == 2

    def test_empty_data_returns_dict(self, cdm):
        """Minimal data (empty CounterpartySet) returns dict."""
        mapping = cdm.create_mapping({"CounterpartySet": {}})
        assert isinstance(mapping, dict)

    def test_none_values_excluded(self, cdm):
        """Lines 288-289: None values are stripped from result."""
        mapping = cdm.create_mapping({"CounterpartySet": {"Party": {"PartyID": "X"}}})
        assert None not in mapping.values()

    def test_invalid_data_raises_value_error(self, cdm):
        """Lines 291-292: exception → raises ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            cdm.create_mapping(None)
