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

"""Popup integration tests using synthetic data (part 1).

Tests popup builder instantiation and individual section builders.
All tests use synthetic in-memory data -- no file I/O required.
"""

import pytest


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPopupBuilderInstantiation:
    """Popup builders must be importable and instantiable."""

    def test_property_popup_builder(self):
        from visual.popups import PropertyPopupBuilder
        builder = PropertyPopupBuilder()
        assert builder is not None

    def test_gauge_popup_builder(self):
        from visual.popups import GaugePopupBuilder
        builder = GaugePopupBuilder()
        assert builder is not None

    def test_base_popup_builder(self):
        from visual.popups import PopupBuilder
        builder = PopupBuilder()
        assert builder is not None


class TestPropertySectionBuilders:
    """Individual section builders must produce correct HTML."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_property, sample_address, sample_mortgage, sample_flood_info):
        from visual.popups import PropertyPopupBuilder
        self.builder = PropertyPopupBuilder()
        self.prop = sample_property
        self.address = sample_address
        self.mortgage = sample_mortgage
        self.flood_info = sample_flood_info

    def test_property_section_has_type(self):
        section = self.builder.create_property_section(
            self.prop, 'PROP-INTG-001', self.address,
            '51.5074\u00b0N, -0.1278\u00b0E', 1985, 'Medium (1925-1975)', 500000, False
        )
        assert 'Residential' in section or 'Terraced House' in section

    def test_property_section_has_address(self):
        section = self.builder.create_property_section(
            self.prop, 'PROP-INTG-001', self.address,
            '51.5074\u00b0N, -0.1278\u00b0E', 1985, 'Medium (1925-1975)', 500000, False
        )
        assert 'Test Street' in section
        assert 'London' in section

    def test_property_section_has_value(self):
        section = self.builder.create_property_section(
            self.prop, 'PROP-INTG-001', self.address,
            '51.5074\u00b0N, -0.1278\u00b0E', 1985, 'Medium (1925-1975)', 500000, False
        )
        assert '500,000' in section

    def test_flood_info_section(self):
        section = self.builder.create_flood_info_section(self.flood_info)
        assert 'Test Thames Gauge' in section
        assert 'Medium' in section

    def test_rloan_section(self):
        section = self.builder.create_rloan_section(self.mortgage, 500000, 'Medium')
        assert 'MTG-INTG-001' in section
        assert 'Test Bank Ltd' in section
        assert 'MORTGAGE DETAILS' in section


class TestGaugeSectionBuilders:
    """Gauge popup section builders must produce correct HTML."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_gauge_info):
        from visual.popups import GaugePopupBuilder
        self.builder = GaugePopupBuilder()
        self.gauge_info = sample_gauge_info

    def test_equipment_details_section(self):
        section = self.builder.create_equipment_details_section(self.gauge_info)
        assert 'Environment Agency' in section
        assert 'Equipment Details' in section

    def test_equipment_section_has_status(self):
        section = self.builder.create_equipment_details_section(self.gauge_info)
        assert 'Fully operational' in section

    def test_flood_thresholds_section(self):
        section = self.builder.create_flood_thresholds_section(self.gauge_info)
        assert '2.5' in section or 'Alert' in section
        assert 'Flood Thresholds' in section
