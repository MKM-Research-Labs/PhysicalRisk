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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Thames-specific gauge random value generators.

Contains all the random value generation logic for Thames catchment flood gauges,
including field generators by type (text, decimal, integer, date, menu).

Usage:
    from port.random.thames import gauge_random

    # Generate metadata for a gauge at given location
    metadata = gauge_random.generate_gauge_metadata(index, location)

    # Generate specific field values
    value = gauge_random.generate_text_value('GaugeOwner', field_def, index, metadata)
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from .gauge_field_generators import (  # noqa: F401
    GAUGE_TYPES,
    GAUGE_OWNERS,
    UK_DECISION_BODIES,
    DATA_CURATORS,
    MANUFACTURERS,
    generate_text_value,
    generate_decimal_value,
    generate_integer_value,
    generate_date_value,
    generate_menu_value,
)

# Note: Catchment-specific data (AREAS, etc.) should be passed via metadata
# from the generator which has access to catchment params via config.load_params_module()


# =============================================================================
# METADATA GENERATION
# =============================================================================

def generate_gauge_metadata(index: int, location: Dict[str, Any], catchment_name: str = "River") -> Dict[str, Any]:
    """
    Generate metadata for a gauge that will be used by field generators.

    Args:
        index: Gauge index
        location: Location dictionary with lat, lon, elevation, name
        catchment_name: Name of the catchment (e.g., "Thames", "Seine", "Rhine")

    Returns:
        Metadata dictionary containing gauge-specific information
    """
    # Generate deterministic ID from location coordinates.
    # This ensures gauge IDs are STABLE across regenerations —
    # the same location always produces the same ID.
    # Prevents downstream breakage (trades, hazard curves, blotter).
    import hashlib
    loc_key = f"{location['lat']:.6f}:{location['lon']:.6f}:{location.get('name', '')}"
    gauge_id = f"GAUGE-{hashlib.sha256(loc_key.encode()).hexdigest()[:8]}"

    # Generate consistent historical high level
    historical_high_level = 5.0 + random.uniform(0, 3.0)

    # Calculate alert levels as percentages of historical high
    flood_alert = historical_high_level * 0.6
    flood_warning = historical_high_level * 0.8
    severe_flood_warning = historical_high_level * 0.95

    # Generate install date (between 2 and 15 years ago)
    years_ago = random.randint(2, 15)
    install_date = (datetime.now() - timedelta(days=365*years_ago)).strftime("%Y-%m-%d")

    # Generate historical high date (after install date)
    high_date_days = random.randint(30, years_ago * 365 - 30)
    historical_high_date = (datetime.now() - timedelta(days=high_date_days)).strftime("%Y-%m-%d")

    return {
        "gauge_id": gauge_id,
        "historical_high_level": round(historical_high_level, 2),
        "historical_high_date": historical_high_date,
        "flood_alert": round(flood_alert, 2),
        "flood_warning": round(flood_warning, 2),
        "severe_flood_warning": round(severe_flood_warning, 2),
        "install_date": install_date,
        "location": location,
        "catchment_name": catchment_name,  # Add catchment name to metadata
        "index": index
    }


# =============================================================================
# FLOOD RISK ASSESSMENT
# =============================================================================

def generate_flood_risk_assessment(location: Dict[str, Any], distance_threshold: int = 300) -> Dict[str, Any]:
    """
    Generate random flood status based on proximity to Thames.

    Args:
        location: Location dictionary
        distance_threshold: Distance in meters considered close to Thames

    Returns:
        Dictionary with flood status information
    """
    # Properties closer to Thames have higher flood risks
    distance_to_thames = location.get('distance_to_thames', 0)
    is_close_to_thames = distance_to_thames < distance_threshold

    if is_close_to_thames:
        risk_score = random.randint(7, 10)
        risk_category = random.choice(["High", "Very High"])
    else:
        risk_score = random.randint(2, 6)
        risk_category = random.choice(["Low", "Medium"])

    return {
        "FloodRiskScore": risk_score,
        "FloodRiskCategory": risk_category,
        "LastAssessmentDate": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
    }


# =============================================================================
# UNIFIED FIELD GENERATOR
# =============================================================================

def generate_field_value(field_name: str, field_def: Dict, index: int, metadata: Dict) -> Any:
    """
    Generate a value for any field based on its type in the schema.

    Args:
        field_name: Name of the field
        field_def: Schema definition for the field
        index: Gauge index
        metadata: Gauge metadata dictionary

    Returns:
        Generated value appropriate for the field type
    """
    if not isinstance(field_def, dict):
        return field_def if isinstance(field_def, str) else ""

    field_type = field_def.get('type', 'text')

    if field_type == 'text':
        return generate_text_value(field_name, field_def, index, metadata)
    elif field_type == 'decimal':
        return generate_decimal_value(field_name, field_def, index, metadata)
    elif field_type == 'integer':
        return generate_integer_value(field_name, field_def, index, metadata)
    elif field_type == 'date':
        return generate_date_value(field_name, field_def, index, metadata)
    elif field_type == 'menu':
        return generate_menu_value(field_name, field_def, index, metadata)
    else:
        return ""
