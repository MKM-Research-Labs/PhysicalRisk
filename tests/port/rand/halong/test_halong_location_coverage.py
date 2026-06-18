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

"""Coverage expansion tests for property_location.py — Block B6.

Targets missing lines:
  - 60-63: generate_bathrooms for houses with 3 bedrooms and 4+ bedrooms
  - 159: generate_council_tax_band returns 'A' for value < 120000
  - 161: generate_council_tax_band returns 'B' for value in [120000, 156000)
"""

import random

import pytest

from port.rand.halong.property.property_location import (
    generate_bathrooms,
    generate_council_tax_band,
)


# ---------------------------------------------------------------------------
# Lines 60-63: generate_bathrooms — house with 3 and 4+ bedrooms
# ---------------------------------------------------------------------------

class TestGenerateBathroomsHousePaths:

    def test_house_3_bedrooms_returns_1_or_2(self):
        """Line 60-61: house with 3 bedrooms returns 1 or 2 bathrooms."""
        random.seed(42)
        results = set()
        for _ in range(100):
            val = generate_bathrooms({"property_type": "House", "bedrooms": 3})
            results.add(val)
        assert results.issubset({1, 2})
        assert len(results) == 2  # both values should appear in 100 trials

    def test_house_4_bedrooms_returns_2_or_3(self):
        """Line 62-63: house with 4+ bedrooms returns 2 or 3 bathrooms."""
        random.seed(42)
        results = set()
        for _ in range(100):
            val = generate_bathrooms({"property_type": "House", "bedrooms": 4})
            results.add(val)
        assert results.issubset({2, 3})
        assert len(results) == 2

    def test_house_5_bedrooms_returns_2_or_3(self):
        """5 bedrooms also takes the 4+ path (line 62-63)."""
        random.seed(0)
        val = generate_bathrooms({"property_type": "House", "bedrooms": 5})
        assert val in (2, 3)


# ---------------------------------------------------------------------------
# Line 56: generate_bathrooms — Flat path
# ---------------------------------------------------------------------------

class TestGenerateBathroomsFlatPaths:

    def test_flat_2_bedrooms_returns_1(self):
        """Line 56: flat with <=2 bedrooms always returns 1 bathroom."""
        for _ in range(20):
            val = generate_bathrooms({"property_type": "Flat", "bedrooms": 2})
            assert val == 1

    def test_flat_default_type_is_flat(self):
        """Missing property_type defaults to 'Flat' (line 52) → line 56."""
        val = generate_bathrooms({"bedrooms": 1})
        assert val == 1

    def test_flat_3_bedrooms_returns_1_or_2(self):
        """Line 56: flat with >2 bedrooms returns 1 or 2 bathrooms."""
        random.seed(42)
        results = set()
        for _ in range(100):
            val = generate_bathrooms({"property_type": "Flat", "bedrooms": 3})
            results.add(val)
        assert results.issubset({1, 2})
        assert len(results) == 2  # both values should appear in 100 trials


# ---------------------------------------------------------------------------
# Lines 159, 161: generate_council_tax_band — bands A and B
# ---------------------------------------------------------------------------

class TestCouncilTaxBandLowValues:

    def test_band_a_for_very_low_value(self):
        """Line 159: property value < 120000 returns band 'A'."""
        band = generate_council_tax_band({"property_value": 100000})
        assert band == "A"

    def test_band_a_boundary(self):
        """Exactly at 119999 should be band 'A'."""
        band = generate_council_tax_band({"property_value": 119999})
        assert band == "A"

    def test_band_b_lower_boundary(self):
        """Line 161: property value = 120000 returns band 'B'."""
        band = generate_council_tax_band({"property_value": 120000})
        assert band == "B"

    def test_band_b_mid_range(self):
        """Property value 140000 returns band 'B'."""
        band = generate_council_tax_band({"property_value": 140000})
        assert band == "B"

    def test_band_b_upper_boundary(self):
        """Exactly at 155999 should still be band 'B'."""
        band = generate_council_tax_band({"property_value": 155999})
        assert band == "B"


# ---------------------------------------------------------------------------
# Lines 163, 165, 167, 169, 173: bands C, D, E, F, H
# ---------------------------------------------------------------------------

class TestCouncilTaxBandHigherValues:

    @pytest.mark.parametrize("value,expected", [
        (180000, "C"),   # line 163: [156000, 204000)
        (230000, "D"),   # line 165: [204000, 264000)
        (300000, "E"),   # line 167: [264000, 360000)
        (420000, "F"),   # line 169: [360000, 480000)
        (700000, "G"),   # line 171: [480000, 960000)
        (1000000, "H"),  # line 173: >= 960000
    ])
    def test_bands_c_through_h(self, value, expected):
        assert generate_council_tax_band({"property_value": value}) == expected

    def test_default_value_band_g(self):
        """Missing property_value defaults to 500000 (line 156) → band 'G'."""
        assert generate_council_tax_band({}) == "G"
