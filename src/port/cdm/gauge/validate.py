# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flood Gauge CDM validation logic."""

from typing import Dict, List


def validate_gauge(gauge_data: dict) -> Dict[str, List[str]]:
    """
    Validate flood gauge data against the CDM schema.

    Args:
        gauge_data: Flood gauge data to validate

    Returns:
        Dictionary of validation errors by section
    """
    errors = {}

    try:
        # Validate Header section
        header_errors = []
        header = gauge_data.get("FloodGauge", {}).get("Header", {})

        if not header.get("GaugeID"):
            header_errors.append("Missing required field: GaugeID")

        if not header.get("CatchmentID"):
            header_errors.append("Missing recommended field: CatchmentID")

        if header_errors:
            errors["Header"] = header_errors

        # Validate SensorDetails section
        sensor_errors = []
        gauge_info = (gauge_data.get("FloodGauge", {})
                      .get("SensorDetails", {})
                      .get("GaugeInformation", {}))

        menu_validations = {
            "DataSourceType": ["SensorGauge", "Satellite", "WeatherStation"],
            "GaugeType": [
                "Staff gauge", "Wire-weight gauge", "Shaft encoder",
                "Bubbler system", "Pressure transducer", "Radar gauge",
                "Ultrasonic gauge"
            ],
            "MaintenanceSchedule": ["Monthly", "Quarterly", "Bi-annual", "Annual"],
            "OperationalStatus": [
                "Fully operational", "Maintenance required",
                "Temporarily offline", "Decommissioned"
            ],
            "CertificationStatus": [
                "Fully certified", "Provisional",
                "Under review", "Non-certified"
            ]
        }

        for field, valid_options in menu_validations.items():
            if field in gauge_info and gauge_info[field] not in valid_options:
                sensor_errors.append(f"Invalid value for {field}: {gauge_info[field]}")

        if sensor_errors:
            errors["SensorDetails"] = sensor_errors

        return errors

    except Exception as e:
        return {"validation_error": [str(e)]}
