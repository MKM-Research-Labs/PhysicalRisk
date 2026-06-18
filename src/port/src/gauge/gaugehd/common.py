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
