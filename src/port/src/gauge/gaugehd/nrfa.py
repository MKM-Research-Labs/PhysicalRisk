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

"""
NRFA (National River Flow Archive) CSV parsing.

Parses NRFA GDF CSV format when real gauge data is available,
converts to the standard GaugeHistoricalDaily JSON format.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import config
from .statistics import calculate_flow_statistics

logger = logging.getLogger(__name__)

# NRFA metadata keys expected in CSV header
METADATA_CATEGORIES = {
    'file': ['timestamp'],
    'database': ['id', 'name'],
    'station': [
        'id', 'name', 'gridReference', 'descriptionSummary',
        'descriptionGeneral', 'descriptionStationHydrometry',
        'descriptionFlowRecord', 'descriptionCatchment',
        'descriptionFlowRegime',
    ],
    'dataType': ['id', 'name', 'parameter', 'units', 'period', 'measurementType'],
    'data': ['first', 'last'],
}


def parse_nrfa_csv(filepath: Path) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """
    Parse an NRFA GDF CSV file.

    Args:
        filepath: Path to the CSV file

    Returns:
        Tuple of (metadata dict, list of daily flow dicts)
    """
    metadata = {}
    daily_flows = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 2:
                continue

            if row[0] in METADATA_CATEGORIES:
                category = row[0]
                key = row[1]
                value = row[2] if len(row) > 2 else ''
                metadata[f"{category}_{key}"] = value
            else:
                try:
                    date_str = row[0]
                    datetime.strptime(date_str, '%Y-%m-%d')
                    flow_value = float(row[1])
                    daily_flows.append({
                        'date': date_str,
                        'flow_cumecs': flow_value,
                    })
                except (ValueError, IndexError):
                    continue

    return metadata, daily_flows


def filter_by_years(
    daily_flows: List[Dict[str, Any]],
    years: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filter flows to most recent N years.

    Args:
        daily_flows: All daily flow observations
        years: Number of years to keep (None = all)

    Returns:
        Filtered list of flows
    """
    if years is None or not daily_flows:
        return daily_flows

    dates = [datetime.strptime(f['date'], '%Y-%m-%d') for f in daily_flows]
    max_date = max(dates)
    cutoff_date = max_date.replace(year=max_date.year - years)

    return [
        f for f in daily_flows
        if datetime.strptime(f['date'], '%Y-%m-%d') >= cutoff_date
    ]


def generate_from_nrfa(
    input_path: Path,
    output_path: Optional[Path] = None,
    years: Optional[int] = None,
    gauge_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate JSON file from NRFA CSV.

    Args:
        input_path: Path to NRFA CSV file
        output_path: Path for output JSON (auto-generated if None)
        years: Number of years to include (None = 50)
        gauge_id: Override gauge ID (extracted from metadata if None)

    Returns:
        The generated data dictionary
    """
    metadata, all_flows = parse_nrfa_csv(input_path)

    station_id = gauge_id or metadata.get('station_id', input_path.stem.replace('_gdf', ''))

    years_to_use = years if years is not None else 50
    filtered_flows = filter_by_years(all_flows, years_to_use)

    stats = calculate_flow_statistics(filtered_flows)

    from port.src.gauge.gaugehd.common import build_station_metadata
    station_metadata = build_station_metadata(station_id, metadata)

    output_data = {
        'schema_version': '1.0',
        'data_type': 'GaugeHistoricalDaily',
        'generated_at': datetime.now().isoformat(),
        'generator': 'gaugehd.py',
        'generation_mode': 'nrfa',
        'years_included': years_to_use,
        'station_metadata': station_metadata,
        'statistics': stats,
        'daily_flows': filtered_flows,
    }

    if output_path is None:
        output_dir = config.get_gaugehd_dir()
        output_path = output_dir / f"gauge_{station_id}_hd.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info("Generated: %s", output_path.name)
    logger.info("Station: %s (%s)", station_metadata['station_name'], station_id)
    logger.info("Records: %d days (%s years)", len(filtered_flows), stats.get('total_years', 0))
    logger.info("Period: %s to %s", stats.get('record_start', 'N/A'), stats.get('record_end', 'N/A'))
    logger.info("Mean Flow: %s m3/s", stats.get('mean_flow', 'N/A'))
    logger.info("Max Flow: %s m3/s on %s", stats.get('max_flow', 'N/A'), stats.get('max_flow_date', 'N/A'))

    return output_data
