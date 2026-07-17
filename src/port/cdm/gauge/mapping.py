# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Flood Gauge CDM mapping — flat dict extraction from nested CDM structure."""

from typing import List


def create_gauge_mapping(gauge: dict) -> dict:
    """
    Create a flat dictionary from nested CDM structure.

    Args:
        gauge: Nested gauge data in CDM format

    Returns:
        Flat dictionary with snake_case keys
    """
    try:
        fg = gauge.get('FloodGauge', {})
        header = fg.get('Header', {})
        stats = fg.get('SensorStats', {})
        details = fg.get('SensorDetails', {})
        gauge_info = details.get('GaugeInformation', {})
        measurements = details.get('Measurements', {})
        flood_stage = fg.get('FloodStage', {}).get('UK', {})
        nrfa = fg.get('NRFAMetadata', {})

        gauge_data = {
            # Header
            'gauge_id': header.get('GaugeID'),
            'catchment_id': header.get('CatchmentID'),
            'gauge_name': header.get('GaugeName'),

            # SensorStats
            'historical_high_level': stats.get('HistoricalHighLevel'),
            'historical_high_date': stats.get('HistoricalHighDate'),
            'last_date_level_exceed_level3': stats.get('LastDateLevelExceedLevel3'),
            'frequency_exceed_level3': stats.get('FrequencyExceedLevel3'),

            # GaugeInformation
            'data_source_type': gauge_info.get('DataSourceType'),
            'gauge_owner': gauge_info.get('GaugeOwner'),
            'gauge_type': gauge_info.get('GaugeType'),
            'manufacturer_name': gauge_info.get('ManufacturerName'),
            'installation_date': gauge_info.get('InstallationDate'),
            'last_inspection_date': gauge_info.get('LastInspectionDate'),
            'maintenance_schedule': gauge_info.get('MaintenanceSchedule'),
            'operational_status': gauge_info.get('OperationalStatus'),
            'certification_status': gauge_info.get('CertificationStatus'),
            'gauge_latitude': gauge_info.get('GaugeLatitude'),
            'gauge_longitude': gauge_info.get('GaugeLongitude'),
            'ground_level_meters': gauge_info.get('GroundLevelMeters'),
            'elevation': gauge_info.get('elevation') or gauge_info.get('GroundLevelMeters'),

            # Measurements
            'measurement_frequency': measurements.get('MeasurementFrequency'),
            'measurement_method': measurements.get('MeasurementMethod'),
            'data_transmission': measurements.get('DataTransmission'),
            'data_curator': measurements.get('DataCurator'),
            'data_access_method': measurements.get('DataAccessMethod'),

            # FloodStage UK
            'decision_body': flood_stage.get('DecisionBody'),
            'flood_alert': flood_stage.get('FloodAlert'),
            'flood_warning': flood_stage.get('FloodWarning'),
            'severe_flood_warning': flood_stage.get('SevereFloodWarning'),
            'flash_minor': flood_stage.get('FlashMinor'),
            'flash_major': flood_stage.get('FlashMajor'),
            'tsunami_minor': flood_stage.get('TsunamiMinor'),
            'tsunami_major': flood_stage.get('TsunamiMajor'),

            # NRFAMetadata
            'nrfa_station_id': nrfa.get('NRFAStationID'),
            'grid_reference': nrfa.get('GridReference'),
            'catchment_area': nrfa.get('CatchmentArea'),
            'record_start_date': nrfa.get('RecordStartDate'),
            'record_end_date': nrfa.get('RecordEndDate'),
            'mean_flow': nrfa.get('MeanFlow'),
            'median_flow': nrfa.get('MedianFlow'),
            'q95_flow': nrfa.get('Q95Flow'),
            'q5_flow': nrfa.get('Q5Flow'),
            'max_recorded_flow': nrfa.get('MaxRecordedFlow'),
            'max_recorded_flow_date': nrfa.get('MaxRecordedFlowDate'),
            'historical_data_file': nrfa.get('HistoricalDataFile'),
            'database_source': nrfa.get('DatabaseSource'),
            'flow_units': nrfa.get('FlowUnits'),
            'data_quality_notes': nrfa.get('DataQualityNotes')
        }

        return {k: v for k, v in gauge_data.items() if v is not None}

    except Exception as e:
        raise ValueError(f"Error creating gauge mapping: {str(e)}")


def get_required_fields() -> List[str]:
    """Return list of required fields."""
    return ['FloodGauge.Header.GaugeID', 'FloodGauge.Header.CatchmentID']


def get_nrfa_fields() -> List[str]:
    """Return list of NRFA metadata fields."""
    return [
        'nrfa_station_id', 'grid_reference', 'catchment_area',
        'record_start_date', 'record_end_date', 'mean_flow',
        'median_flow', 'q95_flow', 'q5_flow', 'max_recorded_flow',
        'max_recorded_flow_date', 'historical_data_file',
        'database_source', 'flow_units', 'data_quality_notes'
    ]
