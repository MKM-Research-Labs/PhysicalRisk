"""Shared helpers for gaugehd generators."""


def build_station_metadata(station_id: str, metadata: dict) -> dict:
    """Build station metadata dict from raw NRFA metadata."""
    return {
        'station_id': station_id,
        'station_name': metadata.get('station_name', ''),
        'grid_reference': metadata.get('station_gridReference', ''),
        'description_summary': metadata.get('station_descriptionSummary', ''),
        'description_general': metadata.get('station_descriptionGeneral', ''),
        'description_hydrometry': metadata.get('station_descriptionStationHydrometry', ''),
        'description_flow_record': metadata.get('station_descriptionFlowRecord', ''),
        'description_catchment': metadata.get('station_descriptionCatchment', ''),
        'description_flow_regime': metadata.get('station_descriptionFlowRegime', ''),
        'data_type_id': metadata.get('dataType_id', ''),
        'data_type_name': metadata.get('dataType_name', ''),
        'parameter': metadata.get('dataType_parameter', ''),
        'units': metadata.get('dataType_units', ''),
        'period': metadata.get('dataType_period', ''),
        'measurement_type': metadata.get('dataType_measurementType', ''),
        'full_record_first': metadata.get('data_first', ''),
        'full_record_last': metadata.get('data_last', ''),
        'database_id': metadata.get('database_id', ''),
        'database_name': metadata.get('database_name', ''),
    }
