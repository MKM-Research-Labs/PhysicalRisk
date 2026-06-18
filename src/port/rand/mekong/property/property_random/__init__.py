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
Thames-specific property random value generators.

Contains the field generator registry and metadata generation.
Delegates to submodules for specific calculation domains:
  - property_utils: dates, names, construction years
  - property_location: postcodes, streets, bedrooms, floor levels, council tax
  - property_valuation: property value, area, sale price, rent, insurance
  - property_energy: carbon, energy, electricity, gas, solar, bills

Usage:
    from port.rand.thames import property_random

    generators = property_random.get_field_generators()
    value = generators['PropertyValue'](location_info)
"""

from .helpers import _deterministic_prop_id, _ea_zone_from_elevation
from .metadata import generate_property_metadata
from .generators import generate_field_value, get_field_generators

# Re-export functions that consumers access as module attributes
from ..property_utils import generate_postcode, generate_construction_year  # noqa: F401
from ..property_location import generate_bedrooms  # noqa: F401
from ..property_valuation import (  # noqa: F401
    calculate_property_value,
    calculate_property_area,
    calculate_insurance_premium,
)

__all__ = [
    '_deterministic_prop_id',
    '_ea_zone_from_elevation',
    'generate_property_metadata',
    'generate_field_value',
    'get_field_generators',
    'generate_postcode',
    'generate_construction_year',
    'generate_bedrooms',
    'calculate_property_value',
    'calculate_property_area',
    'calculate_insurance_premium',
]
