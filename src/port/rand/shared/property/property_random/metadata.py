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

"""Property metadata generation."""

import random
from typing import Any, Dict

from .helpers import _deterministic_prop_id
from ..property_utils import generate_construction_year
from ..property_valuation import calculate_property_area, calculate_property_value


def generate_property_metadata(index: int, location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate property metadata including ID, type, and other core attributes.

    Args:
        index: Property index in the portfolio
        location: Location dictionary with lat, lon, elevation, name, etc.

    Returns:
        Dictionary containing property metadata
    """
    property_type = random.choice([
        'Flat', 'Mid-terrace', 'End-terrace',
        'Semi-detached', 'Detached', 'Bungalow'
    ])

    construction_year = generate_construction_year()
    property_area = calculate_property_area({'property_type': property_type})

    property_value = calculate_property_value({
        'property_type': property_type,
        'property_area': property_area,
        'construction_year': construction_year,
        'elevation': location['elevation'],
        'value_factor': location.get('value_factor', 1.0)
    })

    return {
        'property_id': _deterministic_prop_id(location, index),
        'property_type': property_type,
        'construction_year': construction_year,
        'property_area': property_area,
        'property_value': property_value,
        'elevation': location['elevation'],
        'vertical_offset': location.get('vertical_offset', 0.5),
        'area_name': location.get('name', 'Unknown'),
        'value_factor': location.get('value_factor', 1.0),
        'streets_data': location.get('streets_data', {})
    }
