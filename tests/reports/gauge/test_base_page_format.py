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
Tests for GaugeBasePage format helper methods (page_00_base.py):
  - _format_value
  - _format_measurement
  - _format_coordinate
  - _format_frequency
  - _format_field_name
"""


def _make_base_page():
    """Return a concrete GaugeBasePage instance."""
    from reports.gauge.gauge_page_00_base import GaugeBasePage

    class _ConcreteBase(GaugeBasePage):
        def generate_elements(self, gauge_data, timeseries_data=None):
            return []

    return _ConcreteBase()


# ===========================================================================
# GaugeBasePage._format_value
# ===========================================================================

class TestFormatValue:

    def test_none_returns_not_specified(self):
        page = _make_base_page()
        assert page._format_value(None) == 'Not specified'

    def test_true_returns_yes(self):
        page = _make_base_page()
        assert page._format_value(True) == 'Yes'

    def test_false_returns_no(self):
        page = _make_base_page()
        assert page._format_value(False) == 'No'

    def test_integer_returns_str(self):
        """int branch (line 270): str(value)."""
        page = _make_base_page()
        result = page._format_value(42)
        assert result == '42'

    def test_float_whole_number_strips_decimal(self):
        """float.is_integer() -> str(int(value))."""
        page = _make_base_page()
        result = page._format_value(3.0)
        assert result == '3'

    def test_float_with_decimals_formatted(self):
        """float with fractional part -> 2 decimal places."""
        page = _make_base_page()
        result = page._format_value(3.14)
        assert result == '3.14'

    def test_empty_string_returns_not_specified(self):
        """Blank/whitespace-only string (line 272) -> 'Not specified'."""
        page = _make_base_page()
        assert page._format_value('') == 'Not specified'
        assert page._format_value('   ') == 'Not specified'

    def test_normal_string_returned(self):
        page = _make_base_page()
        assert page._format_value('hello') == 'hello'


# ===========================================================================
# GaugeBasePage._format_measurement
# ===========================================================================

class TestFormatMeasurement:

    def test_numeric_value_with_default_unit(self):
        """line 280: f'{value:.3f} {unit}'."""
        page = _make_base_page()
        result = page._format_measurement(3.5)
        assert result == '3.500 m'

    def test_numeric_value_with_custom_unit(self):
        page = _make_base_page()
        result = page._format_measurement(1.234, unit='km')
        assert result == '1.234 km'

    def test_integer_value(self):
        page = _make_base_page()
        result = page._format_measurement(5)
        assert result == '5.000 m'

    def test_non_numeric_delegates_to_format_value(self):
        page = _make_base_page()
        result = page._format_measurement(None)
        assert result == 'Not specified'


# ===========================================================================
# GaugeBasePage._format_coordinate
# ===========================================================================

class TestFormatCoordinate:

    def test_float_coordinate_six_decimals(self):
        """line 286: f'{value:.6f}'."""
        page = _make_base_page()
        result = page._format_coordinate(51.5)
        assert result == '51.500000'

    def test_negative_coordinate(self):
        page = _make_base_page()
        result = page._format_coordinate(-0.1)
        assert result == '-0.100000'

    def test_none_delegates_to_format_value(self):
        page = _make_base_page()
        assert page._format_coordinate(None) == 'Not specified'


# ===========================================================================
# GaugeBasePage._format_frequency
# ===========================================================================

class TestFormatFrequency:

    def test_positive_returns_times(self):
        page = _make_base_page()
        assert page._format_frequency(3) == '3 times'

    def test_zero_returns_never(self):
        """line 294: 'Never'."""
        page = _make_base_page()
        assert page._format_frequency(0) == 'Never'

    def test_non_numeric_delegates(self):
        page = _make_base_page()
        assert page._format_frequency(None) == 'Not specified'


# ===========================================================================
# GaugeBasePage._format_field_name
# ===========================================================================

class TestFormatFieldName:

    def test_camel_case_split(self):
        page = _make_base_page()
        result = page._format_field_name('gaugeId')
        assert 'Gauge' in result

    def test_abbreviation_replacements(self):
        page = _make_base_page()
        result = page._format_field_name('gpsCoordinate')
        assert 'GPS' in result
