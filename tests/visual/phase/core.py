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

"""Tests for core visual infrastructure: DataLoader, MapBuilder, utilities."""


class TestCoreImports:
    """Test that core modules can be imported."""

    def test_import_data_loader(self):
        from visual.core import DataLoader
        assert DataLoader is not None

    def test_import_map_builder(self):
        from visual.core import MapBuilder
        assert MapBuilder is not None

    def test_import_tc_event_visualization(self):
        from visual.core import TCEventVisualization
        assert TCEventVisualization is not None

    def test_import_utils(self):
        from visual.utils import ColorSchemes, DataFormatter, RiskAssessor
        assert ColorSchemes is not None
        assert DataFormatter is not None
        assert RiskAssessor is not None


class TestCoreUtilities:
    """Test utility module functions (ColorSchemes, DataFormatter, RiskAssessor)."""

    def test_currency_formatting(self):
        from visual.utils import DataFormatter
        result = DataFormatter.format_currency(123456.789)
        assert isinstance(result, str)
        assert "123" in result

    def test_flood_risk_color_high(self):
        from visual.utils import ColorSchemes
        color = ColorSchemes.get_flood_risk_color("High")
        assert color is not None
        assert isinstance(color, str)

    def test_flood_risk_color_low(self):
        from visual.utils import ColorSchemes
        color = ColorSchemes.get_flood_risk_color("Low")
        assert color is not None
        assert isinstance(color, str)

    def test_flood_risk_color_varies_by_level(self):
        from visual.utils import ColorSchemes
        high = ColorSchemes.get_flood_risk_color("High")
        low = ColorSchemes.get_flood_risk_color("Low")
        assert high != low

    def test_risk_assessor_depth(self):
        from visual.utils import RiskAssessor
        level = RiskAssessor.assess_flood_risk_level(1.5)
        assert isinstance(level, str)
        assert len(level) > 0

    def test_risk_assessor_zero_depth(self):
        from visual.utils import RiskAssessor
        level = RiskAssessor.assess_flood_risk_level(0.0)
        assert isinstance(level, str)

    def test_risk_assessor_higher_depth_is_higher_risk(self):
        from visual.utils import RiskAssessor
        low_level = RiskAssessor.assess_flood_risk_level(0.05)
        high_level = RiskAssessor.assess_flood_risk_level(2.5)
        # Both should be strings; high depth should not equal low depth
        assert low_level != high_level


class TestMapBuilderInstantiation:
    """Test MapBuilder can be instantiated."""

    def test_map_builder_creation(self):
        from visual.core import MapBuilder
        builder = MapBuilder()
        assert builder is not None

    def test_map_builder_create_map(self):
        from visual.core import MapBuilder
        builder = MapBuilder()
        base_map = builder.create_map(center=(51.5, -0.1), zoom=10)
        assert base_map is not None


class TestDataLoaderInstantiation:
    """Test DataLoader can be instantiated."""

    def test_data_loader_creation(self, tmp_path):
        from visual.core import DataLoader
        loader = DataLoader(tmp_path)
        assert loader is not None

    def test_data_loader_has_load_all_data(self, tmp_path):
        from visual.core import DataLoader
        loader = DataLoader(tmp_path)
        assert hasattr(loader, 'load_all_data')
