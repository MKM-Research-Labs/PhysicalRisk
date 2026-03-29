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

"""Gauge and flood risk data extraction utilities."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_gauge_info(gauge: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract gauge information from gauge data.

    Args:
        gauge: Raw gauge data dictionary

    Returns:
        Structured gauge data or None if extraction fails
    """
    try:
        # Handle nested structure
        gauge_data = gauge.get('FloodGauge', gauge)

        # Extract header information
        header = gauge_data.get('Header', {})
        gauge_id = header.get('GaugeID', 'Unknown')

        # Extract sensor details
        sensor_details = gauge_data.get('SensorDetails', {})
        gauge_info = sensor_details.get('GaugeInformation', {})
        measurements = sensor_details.get('Measurements', {})

        # Extract coordinates
        lat = gauge_info.get('GaugeLatitude')
        lon = gauge_info.get('GaugeLongitude')

        if lat is None or lon is None:
            logger.warning("Invalid coordinates for gauge %s", gauge_id)
            return None

        # Extract operational information
        gauge_owner = gauge_info.get('GaugeOwner', 'Unknown')
        gauge_type = gauge_info.get('GaugeType', 'Unknown')
        operational_status = gauge_info.get('OperationalStatus', 'Unknown')
        data_source = gauge_info.get('DataSourceType', 'Unknown')
        installation_date = gauge_info.get('InstallationDate', 'Unknown')
        certification_status = gauge_info.get('CertificationStatus', 'Unknown')

        # Extract measurement information
        measurement_frequency = measurements.get('MeasurementFrequency', 'Unknown')
        measurement_method = measurements.get('MeasurementMethod', 'Unknown')
        data_transmission = measurements.get('DataTransmission', 'Unknown')

        # Extract statistical data
        sensor_stats = gauge_data.get('SensorStats', {})

        # Extract flood stage information
        flood_stage = gauge_data.get('FloodStage', {}).get('UK', {})

        extracted_info = {
            'gauge_id': gauge_id,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'gauge_owner': gauge_owner,
            'gauge_type': gauge_type,
            'operational_status': operational_status,
            'data_source': data_source,
            'installation_date': installation_date,
            'certification_status': certification_status,
            'measurement_frequency': measurement_frequency,
            'measurement_method': measurement_method,
            'data_transmission': data_transmission,
            'sensor_stats': sensor_stats,
            'flood_stage': flood_stage,
            # Keep original nested structure for detailed popups
            'original_data': gauge_data
        }

        return extracted_info

    except Exception as e:
        logger.error("Error extracting gauge info: %s", e)
        return None


def extract_flood_risk_data(flood_risk_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract flood risk information from flood risk report.

    Args:
        flood_risk_report: Complete flood risk report

    Returns:
        Dictionary with gauge, property, and mortgage risk data
    """
    result = {
        'gauge_flood_info': {},
        'property_flood_info': {},
        'mortgage_risk_info': {'by_mortgage_id': {}, 'by_property_id': {}}
    }

    try:
        # Extract gauge flood information
        gauge_data = flood_risk_report.get("gauge_data", {})
        for gauge_id, gauge_info in gauge_data.items():
            result['gauge_flood_info'][gauge_id] = {
                "gauge_name": gauge_info.get("gauge_name"),
                "elevation": gauge_info.get("elevation"),
                "max_level": gauge_info.get("max_level"),
                "alert_level": gauge_info.get("alert_level"),
                "warning_level": gauge_info.get("warning_level"),
                "severe_level": gauge_info.get("severe_level"),
                "max_gauge_reading": gauge_info.get("max_gauge_reading")
            }

        # Extract property flood information
        property_risk = flood_risk_report.get("property_risk", {})
        for prop_id, prop_data in property_risk.items():
            result['property_flood_info'][prop_id] = {
                "property_id": prop_data.get("property_id"),
                "property_elevation": prop_data.get("property_elevation"),
                "nearest_gauge": prop_data.get("nearest_gauge"),
                "nearest_gauge_id": prop_data.get("nearest_gauge_id"),
                "distance_to_gauge": prop_data.get("distance_to_gauge"),
                "gauge_elevation": prop_data.get("gauge_elevation"),
                "water_level": prop_data.get("water_level"),
                "severe_level": prop_data.get("severe_level"),
                "gauge_flood_depth": prop_data.get("gauge_flood_depth"),
                "elevation_diff": prop_data.get("elevation_diff"),
                "flood_depth": prop_data.get("flood_depth"),
                "risk_value": prop_data.get("risk_value"),
                "risk_level": prop_data.get("risk_level"),
                "property_value": prop_data.get("property_value"),
                "value_at_risk": prop_data.get("value_at_risk")
            }

        # Extract mortgage risk information
        mortgage_risk_data = flood_risk_report.get("mortgage_risk", {})
        for mortgage_id, risk_info in mortgage_risk_data.items():
            # Add to mortgage ID lookup
            result['mortgage_risk_info']['by_mortgage_id'][mortgage_id] = risk_info

            # Add to property ID lookup if property ID exists
            property_id = risk_info.get("PropertyID")
            if property_id:
                result['mortgage_risk_info']['by_property_id'][property_id] = risk_info

        logger.info("Extracted flood risk data: %d gauges, %d properties, %d mortgages",
                    len(result['gauge_flood_info']),
                    len(result['property_flood_info']),
                    len(result['mortgage_risk_info']['by_mortgage_id']))

    except Exception as e:
        logger.error("Error extracting flood risk data: %s", e)

    return result
