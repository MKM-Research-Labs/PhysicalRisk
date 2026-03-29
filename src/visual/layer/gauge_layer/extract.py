# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Gauge data extraction from raw CDM gauge records."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def extract_gauges(gauge_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract gauge information from raw gauge data.

    Args:
        gauge_data: Raw gauge data dictionary

    Returns:
        List of processed gauge information
    """
    gauges = []

    # Try different possible key formats for compatibility
    raw_gauges = gauge_data.get('items', gauge_data.get('floodGauges', gauge_data.get('flood_gauges', [])))

    for gauge in raw_gauges:
        try:
            # Extract gauge information
            gauge_info = gauge.get('FloodGauge', {})
            header = gauge_info.get('Header', {})
            sensor_details = gauge_info.get('SensorDetails', {})
            gauge_information = sensor_details.get('GaugeInformation', {})

            # Get coordinates
            lat = gauge_information.get('GaugeLatitude')
            lon = gauge_information.get('GaugeLongitude')

            if lat is None or lon is None:
                continue

            # Extract key information
            gauge_id = header.get('GaugeID', 'Unknown')
            gauge_name = header.get('GaugeName', '')
            gauge_type = gauge_information.get('GaugeType', 'Unknown')
            operational_status = gauge_information.get('OperationalStatus', 'Unknown')
            gauge_owner = gauge_information.get('GaugeOwner', 'Unknown')
            data_source = gauge_information.get('DataSourceType', 'Unknown')
            installation_date = gauge_information.get('InstallationDate', 'Unknown')
            certification_status = gauge_information.get('CertificationStatus', 'Unknown')

            # Extract measurement information
            measurements = sensor_details.get('Measurements', {})
            measurement_frequency = measurements.get('MeasurementFrequency', 'Unknown')
            measurement_method = measurements.get('MeasurementMethod', 'Unknown')
            data_transmission = measurements.get('DataTransmission', 'Unknown')

            # Extract flood stage information
            flood_stage = gauge_info.get('FloodStage', {}).get('UK', {})
            flood_alert = flood_stage.get('FloodAlert', 'N/A')
            flood_warning = flood_stage.get('FloodWarning', 'N/A')
            severe_warning = flood_stage.get('SevereFloodWarning', 'N/A')

            # Extract sensor statistics
            sensor_stats = gauge_info.get('SensorStats', {})
            historical_high = sensor_stats.get('HistoricalHighLevel', 'N/A')
            historical_high_date = sensor_stats.get('HistoricalHighDate', 'N/A')
            last_level3_date = sensor_stats.get('LastDateLevelExceedLevel3', 'N/A')
            frequency_exceed_level3 = sensor_stats.get('FrequencyExceedLevel3', 'N/A')

            # Extract ground elevation
            ground_elevation = gauge_information.get('GroundLevelMeters', 'N/A')

            processed_gauge = {
                'gauge_id': gauge_id,
                'gauge_name': gauge_name,
                'lat': float(lat),
                'lon': float(lon),
                'gauge_type': gauge_type,
                'operational_status': operational_status,
                'gauge_owner': gauge_owner,
                'data_source': data_source,
                'installation_date': installation_date,
                'certification_status': certification_status,
                'ground_elevation': ground_elevation,
                'measurement_frequency': measurement_frequency,
                'measurement_method': measurement_method,
                'data_transmission': data_transmission,
                'flood_alert': flood_alert,
                'flood_warning': flood_warning,
                'severe_warning': severe_warning,
                'historical_high': historical_high,
                'historical_high_date': historical_high_date,
                'last_level3_date': last_level3_date,
                'frequency_exceed_level3': frequency_exceed_level3
            }

            gauges.append(processed_gauge)

        except Exception as e:
            logger.warning(f"Error extracting gauge data: {e}")
            continue

    return gauges
