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
Tests for MortgageLoader.

Tests mortgage-specific loading and query functionality.
"""



class TestMortgageLoaderBasics:
    """Test basic MortgageLoader functionality."""

    def test_load_mortgages(self, mortgage_loader):
        """Test loading mortgage portfolio."""
        mortgages = mortgage_loader.load_all()

        assert len(mortgages) == 3

    def test_entity_id_extraction(self, mortgage_loader):
        """Test MortgageID extraction."""
        mortgages = mortgage_loader.load_all()

        for mort in mortgages:
            mort_id = mortgage_loader.get_entity_id(mort)
            assert mort_id is not None
            assert mort_id.startswith("MORT-")

    def test_entity_summary(self, mortgage_loader):
        """Test mortgage summary generation."""
        summaries = mortgage_loader.list_all()

        assert len(summaries) == 3

        summary = summaries[0]
        assert 'mortgageId' in summary
        assert 'propertyId' in summary
        assert 'loanAmount' in summary
        assert 'lender' in summary


class TestMortgageLoaderQueries:
    """Test mortgage-specific query methods."""

    def test_find_by_id(self, mortgage_loader):
        """Test finding mortgage by ID."""
        mort = mortgage_loader.find_by_id("MORT-001")

        assert mort is not None
        assert mort['PropertyID'] == "PROP-001"
        assert mort['LoanAmount'] == 360000

    def test_find_by_property_id(self, mortgage_loader):
        """Test finding mortgage by property ID."""
        mort = mortgage_loader.find_by_property_id("PROP-001")

        assert mort is not None
        assert mort['MortgageID'] == "MORT-001"

    def test_find_by_property_id_not_found(self, mortgage_loader):
        """Test finding mortgage for property without mortgage."""
        mort = mortgage_loader.find_by_property_id("PROP-999")

        assert mort is None

    def test_find_by_lender(self, mortgage_loader):
        """Test finding mortgages by lender."""
        morts = mortgage_loader.find_by_lender("First National")

        assert len(morts) == 2  # MORT-001 and MORT-003

    def test_find_by_lender_case_insensitive(self, mortgage_loader):
        """Test lender search is case insensitive."""
        morts = mortgage_loader.find_by_lender("FIRST NATIONAL")

        assert len(morts) == 2

    def test_find_by_status_active(self, mortgage_loader):
        """Test finding active mortgages."""
        morts = mortgage_loader.find_by_status("Active")

        assert len(morts) == 2

    def test_find_by_status_delinquent(self, mortgage_loader):
        """Test finding delinquent mortgages."""
        morts = mortgage_loader.find_by_status("Delinquent")

        assert len(morts) == 1
        assert morts[0]['MortgageID'] == "MORT-003"


class TestMortgageLoaderAggregations:
    """Test aggregation methods."""

    def test_get_total_exposure(self, mortgage_loader):
        """Test total loan exposure calculation."""
        total = mortgage_loader.get_total_exposure()

        # Sum: 360000 + 1000000 + 280000 = 1640000
        assert total == 1640000

    def test_get_exposure_by_lender(self, mortgage_loader):
        """Test exposure aggregation by lender."""
        exposure = mortgage_loader.get_exposure_by_lender()

        assert "First National Bank" in exposure
        assert "Regional Credit Union" in exposure

        # First National: 360000 + 280000 = 640000
        assert exposure["First National Bank"] == 640000

        # Regional: 1000000
        assert exposure["Regional Credit Union"] == 1000000

    def test_get_delinquent_mortgages(self, mortgage_loader):
        """Test getting delinquent mortgages."""
        delinquent = mortgage_loader.get_delinquent_mortgages()

        assert len(delinquent) == 1
        assert delinquent[0]['MortgageID'] == "MORT-003"

    def test_get_property_ids_with_mortgages(self, mortgage_loader):
        """Test getting property IDs that have mortgages."""
        prop_ids = mortgage_loader.get_property_ids_with_mortgages()

        assert len(prop_ids) == 3
        assert "PROP-001" in prop_ids
        assert "PROP-002" in prop_ids
        assert "PROP-003" in prop_ids


class TestMortgagePropertyIntegration:
    """Test mortgage-property relationship queries."""

    def test_mortgage_links_to_property(self, mortgage_loader, property_loader):
        """Test that mortgage PropertyID links to valid property."""
        mortgages = mortgage_loader.load_all()

        for mort in mortgages:
            prop_id = mort.get('PropertyID')
            prop = property_loader.find_by_id(prop_id)

            assert prop is not None, f"Property {prop_id} not found for mortgage"

    def test_property_with_mortgage(self, mortgage_loader, property_loader):
        """Test finding mortgage for each property."""
        props_with_mortgages = mortgage_loader.get_property_ids_with_mortgages()

        for prop_id in props_with_mortgages:
            prop = property_loader.find_by_id(prop_id)
            assert prop is not None

            mort = mortgage_loader.find_by_property_id(prop_id)
            assert mort is not None
