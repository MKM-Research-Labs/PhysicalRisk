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

"""Schema-driven field value generation for property randomisation."""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from ._registry import get_field_generators


def generate_field_value(field_name: str, field_def: Dict, index: int, metadata: Dict[str, Any]) -> Any:
    """
    Generate a value for a specific field.

    Args:
        field_name: Name of the field
        field_def: Field definition from schema
        index: Property index
        metadata: Property metadata dictionary

    Returns:
        Generated value for the field
    """
    generators = get_field_generators()

    if field_name in generators:
        location_info = {
            'property_type': metadata.get('property_type'),
            'property_area': metadata.get('property_area'),
            'property_value': metadata.get('property_value'),
            'construction_year': metadata.get('construction_year'),
            'elevation': metadata.get('elevation'),
            'vertical_offset': metadata.get('vertical_offset', 0.5),
            'area_name': metadata.get('area_name'),
            'value_factor': metadata.get('value_factor', 1.0),
            'streets_data': metadata.get('streets_data', {})
        }

        try:
            return generators[field_name](location_info)
        except Exception:
            pass

    # Fallback to type-based generation
    field_type = field_def.get('type', 'string')

    if field_type in ('string', 'text'):
        options = field_def.get('options')
        if options:
            return random.choice(options)
        return ''
    elif field_type == 'number':
        return round(random.uniform(0, 1000), 2)
    elif field_type == 'integer':
        return random.randint(0, 100)
    elif field_type == 'boolean':
        return random.choice([True, False])
    elif field_type == 'date':
        days_ago = random.randint(0, 3650)
        return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

    return None
