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
