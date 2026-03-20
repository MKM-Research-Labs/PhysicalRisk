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
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from config.port import GAUGE_TYPE_WEIGHTS

# Note: Catchment-specific data (AREAS, etc.) should be passed via metadata
# from the generator which has access to catchment params via config.load_params_module()


# =============================================================================
# CONSTANTS - Thames specific gauge choices
# =============================================================================

GAUGE_TYPES = [
    "Staff gauge", "Wire-weight gauge", "Shaft encoder",
    "Bubbler system", "Pressure transducer", "Radar gauge",
    "Ultrasonic gauge"
]
# GAUGE_TYPE_WEIGHTS imported from config/port.py

GAUGE_OWNERS = [
    "Environment Agency", "Thames Water", "Local Authority",
    "Met Office", "Research Institution"
]

UK_DECISION_BODIES = [
    "Environment Agency", "Department for Environment, Food and Rural Affairs",
    "Natural Resources Wales", "Scottish Environment Protection Agency"
]

DATA_CURATORS = [
    "Environment Agency", "Met Office", "CEDA Archive",
    "British Hydrological Society", "Centre for Ecology & Hydrology"
]

MANUFACTURERS = [
    "OTT HydroMet", "Campbell Scientific", "Vaisala", "Sutron",
    "YSI", "In-Situ Inc.", "Stevens Water", "SEBA Hydrometrie"
]


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
# TEXT VALUE GENERATORS
# =============================================================================

def generate_text_value(field_name: str, field_def: Dict, index: int, metadata: Dict) -> str:
    """
    Generate a text value based on field name and schema.

    Args:
        field_name: Name of the field
        field_def: Schema definition for the field
        index: Gauge index
        metadata: Gauge metadata dictionary

    Returns:
        Generated text value
    """
    if field_name == 'GaugeID':
        return metadata['gauge_id']
    elif field_name == 'GaugeOwner':
        return random.choice(GAUGE_OWNERS)
    elif field_name == 'ManufacturerName':
        return random.choice(MANUFACTURERS)
    elif field_name == 'DecisionBody':
        return random.choice(UK_DECISION_BODIES)
    elif field_name == 'DataCurator':
        return random.choice(DATA_CURATORS)
    elif field_name == 'GaugeName':
        # Use the short name from catchment definition (e.g. "Chelsea Bridge")
        location = metadata.get('location', {})
        short_name = location.get('name', '')
        catchment_name = metadata.get('catchment_name', 'River')
        if short_name:
            return f"{catchment_name} {short_name}"
        area_name = location.get('area', 'Unknown Area')
        return f"{catchment_name} {area_name} Gauge {index+1}"

    return f"Text-{field_name}-{index}"


# =============================================================================
# DECIMAL VALUE GENERATORS
# =============================================================================

def generate_decimal_value(field_name: str, field_def: Dict, index: int, metadata: Dict) -> float:
    """
    Generate a decimal value based on field name and schema.

    Args:
        field_name: Name of the field
        field_def: Schema definition for the field
        index: Gauge index
        metadata: Gauge metadata dictionary

    Returns:
        Generated decimal value
    """
    if field_name == 'HistoricalHighLevel':
        return metadata['historical_high_level']
    elif field_name == 'FloodAlert':
        return metadata['flood_alert']
    elif field_name == 'FloodWarning':
        return metadata['flood_warning']
    elif field_name == 'SevereFloodWarning':
        return metadata['severe_flood_warning']
    elif field_name == 'GaugeLatitude':
        return metadata['location']['lat']
    elif field_name == 'GaugeLongitude':
        return metadata['location']['lon']
    elif field_name == 'elevation':
        return metadata['location']['elevation']
    elif field_name == 'GroundLevelMeters':
        return metadata['location']['elevation']

    return round(random.uniform(0, 10), 2)


# =============================================================================
# INTEGER VALUE GENERATORS
# =============================================================================

def generate_integer_value(field_name: str, field_def: Dict, index: int, metadata: Dict) -> int:
    """
    Generate an integer value based on field name and schema.

    Args:
        field_name: Name of the field
        field_def: Schema definition for the field
        index: Gauge index
        metadata: Gauge metadata dictionary

    Returns:
        Generated integer value
    """
    if field_name == 'FrequencyExceedLevel3':
        # Generate frequency exceeded Level 3 in past 5 years
        return random.choices(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            weights=[0.3, 0.2, 0.15, 0.1, 0.07, 0.05, 0.05, 0.03, 0.02, 0.02, 0.01]
        )[0]

    return random.randint(1, 10)


# =============================================================================
# DATE VALUE GENERATORS
# =============================================================================

def generate_date_value(field_name: str, field_def: Dict, index: int, metadata: Dict) -> str:
    """
    Generate a date value based on field name and schema.

    Args:
        field_name: Name of the field
        field_def: Schema definition for the field
        index: Gauge index
        metadata: Gauge metadata dictionary

    Returns:
        Generated date string in YYYY-MM-DD format
    """
    if field_name == 'HistoricalHighDate':
        return metadata['historical_high_date']
    elif field_name == 'InstallationDate':
        return metadata['install_date']
    elif field_name == 'LastInspectionDate':
        # Generate last inspection date (within last 2 years)
        inspection_days = random.randint(0, 365*2)
        return (datetime.now() - timedelta(days=inspection_days)).strftime("%Y-%m-%d")
    elif field_name == 'LastDateLevelExceedLevel3':
        # Generate last date level exceeded Level 3 (within last 5 years)
        level3_days = random.randint(0, 365*5)
        return (datetime.now() - timedelta(days=level3_days)).strftime("%Y-%m-%d")

    # Default random date within past 5 years
    days_ago = random.randint(0, 365 * 5)
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


# =============================================================================
# MENU VALUE GENERATORS
# =============================================================================

def generate_menu_value(field_name: str, field_def: Dict, index: int, metadata: Dict) -> str:
    """
    Generate a menu value based on field name and schema.

    Args:
        field_name: Name of the field
        field_def: Schema definition for the field
        index: Gauge index
        metadata: Gauge metadata dictionary

    Returns:
        Generated menu value
    """
    options = field_def.get('options', []) if isinstance(field_def, dict) else []

    if field_name == 'DataSourceType':
        return "SensorGauge"  # Most common for Thames river gauges
    elif field_name == 'TidalInfluence':
        # Thames tidal limit is Teddington Lock (~longitude -0.32)
        # East of that is tidal, west is non-tidal
        lon = metadata.get('location', {}).get('lon', -0.5)
        if lon > -0.25:
            return "Tidal"
        elif lon > -0.35:
            return "Partially tidal"
        else:
            return "Non-tidal"
    elif field_name == 'GaugeType':
        return random.choices(GAUGE_TYPES, weights=GAUGE_TYPE_WEIGHTS)[0]
    elif field_name == 'MaintenanceSchedule':
        return random.choice(["Monthly", "Quarterly", "Bi-annual", "Annual"])
    elif field_name == 'OperationalStatus':
        return random.choices(
            ["Fully operational", "Maintenance required", "Temporarily offline", "Decommissioned"],
            weights=[0.8, 0.15, 0.04, 0.01]
        )[0]
    elif field_name == 'CertificationStatus':
        return random.choices(
            ["Fully certified", "Provisional", "Under review", "Non-certified"],
            weights=[0.85, 0.1, 0.03, 0.02]
        )[0]
    elif field_name == 'MeasurementFrequency':
        return random.choice(["5 minutes", "15 minutes", "30 minutes", "Hourly"])
    elif field_name == 'MeasurementMethod':
        return "Automatic"  # Most common
    elif field_name == 'DataTransmission':
        return "Automatic"  # Most common
    elif field_name == 'DataAccessMethod':
        return random.choices(
            ["PublicAPI", "WebInterface", "Email/Other"],
            weights=[0.4, 0.5, 0.1]
        )[0]

    # Default: random from options if available
    if options:
        return options[index % len(options)]
    return ""


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
