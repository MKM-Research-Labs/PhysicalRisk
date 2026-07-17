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
