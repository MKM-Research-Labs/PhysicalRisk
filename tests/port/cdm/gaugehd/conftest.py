# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
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

"""Shared helpers for GaugeHistoricalDaily tests."""

import datetime
from pathlib import Path


def write_nrfa_csv(path: Path, station_id: str = "39001",
                   station_name: str = "Thames at Kingston",
                   n_years: int = 3) -> Path:
    """Write a minimal NRFA GDF CSV file."""
    lines = [
        "file,timestamp,2024-01-01",
        "database,id,7",
        "database,name,NRFA",
        f"station,id,{station_id}",
        f"station,name,{station_name}",
        "station,gridReference,TQ177695",
        "station,descriptionSummary,Thames gauge station",
        "station,descriptionGeneral,",
        "station,descriptionStationHydrometry,",
        "station,descriptionFlowRecord,Good quality",
        "station,descriptionCatchment,",
        "station,descriptionFlowRegime,",
        "dataType,id,gdf",
        "dataType,name,Gauged Daily Flow",
        "dataType,parameter,Flow",
        "dataType,units,m3/s",
        "dataType,period,daily",
        "dataType,measurementType,mean",
        "data,first,2020-01-01",
        "data,last,2022-12-31",
    ]
    start = datetime.date(2020, 1, 1)
    for i in range(365 * n_years):
        d = start + datetime.timedelta(days=i)
        flow = 50.0 + (i % 30)
        lines.append(f"{d.isoformat()},{flow:.2f}")

    csv_path = path / f"{station_id}_gdf.csv"
    csv_path.write_text("\n".join(lines))
    return csv_path
