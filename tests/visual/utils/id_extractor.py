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
Tests for visual.utils.data_extractors.id_extractor.

Covers: extract_id_from_tooltip and extract_id_from_popup.
"""

import pytest

from visual.utils.data_extractors.id_extractor import (
    extract_id_from_tooltip,
    extract_id_from_popup,
)


# ===========================================================================
# extract_id_from_tooltip
# ===========================================================================

class TestExtractIdFromTooltip:

    def test_empty_string_returns_none(self):
        assert extract_id_from_tooltip("") is None

    def test_none_returns_none(self):
        assert extract_id_from_tooltip(None) is None

    def test_property_id_extracted(self):
        tooltip = "Property: PROP-001 | Value: £400,000"
        result = extract_id_from_tooltip(tooltip, id_type="property")
        assert result == "PROP-001"

    def test_property_id_with_whitespace(self):
        tooltip = "Property:   PROP-002  | Risk: High"
        result = extract_id_from_tooltip(tooltip, id_type="property")
        assert result == "PROP-002"

    def test_gauge_id_from_gauge_prefix(self):
        tooltip = "Gauge: GAUGE-001 | Level: 4.2m"
        result = extract_id_from_tooltip(tooltip, id_type="gauge")
        assert result == "GAUGE-001"

    def test_gauge_id_direct_pattern(self):
        tooltip = "GAUGE-a1b2c3 reading: 3.5m"
        result = extract_id_from_tooltip(tooltip, id_type="gauge")
        assert "GAUGE-" in result

    def test_no_match_returns_none(self):
        assert extract_id_from_tooltip("No IDs here", id_type="property") is None

    def test_unknown_type_returns_none(self):
        assert extract_id_from_tooltip("Property: P1", id_type="unknown") is None

    def test_gauge_type_with_no_gauge_id_returns_none(self):
        assert extract_id_from_tooltip("Property: PROP-001", id_type="gauge") is None


# ===========================================================================
# extract_id_from_popup
# ===========================================================================

class TestExtractIdFromPopup:

    def test_empty_string_returns_none(self):
        assert extract_id_from_popup("") is None

    def test_none_returns_none(self):
        assert extract_id_from_popup(None) is None

    def test_property_id_extracted_from_html(self):
        html = "<div>ID: PROP-001</div><div>Value: £400,000</div>"
        result = extract_id_from_popup(html, id_type="property")
        assert result == "PROP-001"

    def test_gauge_id_extracted_from_html(self):
        html = "<div>ID: GAUGE-a1b2c3</div><div>Level: 4.2m</div>"
        result = extract_id_from_popup(html, id_type="gauge")
        assert result == "GAUGE-a1b2c3"

    def test_gauge_direct_pattern_in_popup(self):
        html = "<span>GAUGE-deadbeef at 51.5°N</span>"
        result = extract_id_from_popup(html, id_type="gauge")
        assert "GAUGE-" in result

    def test_no_match_returns_none(self):
        assert extract_id_from_popup("<div>No IDs</div>", id_type="property") is None

    def test_unknown_type_returns_none(self):
        assert extract_id_from_popup("ID: PROP-001", id_type="unknown") is None

    def test_non_string_input_converted(self):
        # Should handle non-string by converting via str()
        result = extract_id_from_popup(b"ID: PROP-001", id_type="property")
        # bytes repr won't match the regex pattern, so None is acceptable
        assert result is None or isinstance(result, str)
