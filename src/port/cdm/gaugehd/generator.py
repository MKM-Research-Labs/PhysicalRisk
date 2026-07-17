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

"""GaugeHistoricalDaily — NRFA CSV parser and JSON generator."""

import csv
import json
import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import config

logger = logging.getLogger(__name__)

try:
    from cdm.gauge import FloodGaugeCDM
    CDM_AVAILABLE = True
except ImportError:
    CDM_AVAILABLE = False


class GaugeHistoricalDaily:
    """
    Generator for historical daily mean flow JSON files.

    Parses NRFA GDF CSV format and outputs standardized JSON
    with station metadata, statistics, and daily flow timeseries.
    """

    SCHEMA_VERSION = "1.0"

    METADATA_CATEGORIES = {
        'file': ['timestamp'],
        'database': ['id', 'name'],
        'station': [
            'id', 'name', 'gridReference', 'descriptionSummary',
            'descriptionGeneral', 'descriptionStationHydrometry',
            'descriptionFlowRecord', 'descriptionCatchment',
            'descriptionFlowRegime'
        ],
        'dataType': ['id', 'name', 'parameter', 'units', 'period', 'measurementType'],
        'data': ['first', 'last']
    }

    def __init__(self, years_of_history: int = 50):
        self.years_of_history = years_of_history
        self.cdm = FloodGaugeCDM() if CDM_AVAILABLE else None

    def parse_nrfa_csv(self, filepath: Path) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """Parse an NRFA GDF CSV file. Returns (metadata, daily_flows)."""
        metadata = {}
        daily_flows = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                if row[0] in self.METADATA_CATEGORIES:
                    category = row[0]
                    key = row[1]
                    value = row[2] if len(row) > 2 else ''
                    metadata[f"{category}_{key}"] = value
                else:
                    try:
                        date_str = row[0]
                        datetime.strptime(date_str, '%Y-%m-%d')
                        flow_value = float(row[1])
                        daily_flows.append({'date': date_str, 'flow_cumecs': flow_value})
                    except (ValueError, IndexError):
                        continue

        return metadata, daily_flows

    def calculate_statistics(self, daily_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics from daily flow data."""
        if not daily_flows:
            return {}

        flows = [f['flow_cumecs'] for f in daily_flows]
        dates = [f['date'] for f in daily_flows]

        stats = {
            'record_start': min(dates),
            'record_end': max(dates),
            'total_days': len(flows),
            'total_years': round(len(flows) / 365.25, 1),
            'mean_flow': round(statistics.mean(flows), 3),
            'median_flow': round(statistics.median(flows), 3),
            'std_dev': round(statistics.stdev(flows), 3) if len(flows) > 1 else 0,
            'min_flow': round(min(flows), 3),
            'max_flow': round(max(flows), 3),
        }

        max_idx = flows.index(max(flows))
        stats['max_flow_date'] = dates[max_idx]

        sorted_flows = sorted(flows)
        n = len(sorted_flows)

        def percentile(p):
            idx = int(n * p / 100)
            return round(sorted_flows[min(idx, n - 1)], 3)

        stats['percentiles'] = {
            'p5': percentile(5), 'p10': percentile(10), 'p25': percentile(25),
            'p50': percentile(50), 'p75': percentile(75), 'p90': percentile(90),
            'p95': percentile(95), 'p99': percentile(99),
        }

        stats['q95_flow'] = stats['percentiles']['p5']
        stats['q5_flow'] = stats['percentiles']['p95']

        monthly_flows: Dict[str, List[float]] = {}
        for flow in daily_flows:
            month = flow['date'][5:7]
            monthly_flows.setdefault(month, []).append(flow['flow_cumecs'])
        stats['monthly_means'] = {
            m: round(statistics.mean(v), 3)
            for m, v in sorted(monthly_flows.items())
        }

        annual_flows: Dict[str, Dict[str, Any]] = {}
        for flow in daily_flows:
            year = flow['date'][:4]
            if year not in annual_flows:
                annual_flows[year] = {'max': 0, 'max_date': ''}
            if flow['flow_cumecs'] > annual_flows[year]['max']:
                annual_flows[year]['max'] = flow['flow_cumecs']
                annual_flows[year]['max_date'] = flow['date']

        annual_maxima = [v['max'] for v in annual_flows.values()]
        stats['annual_maxima'] = {
            'mean': round(statistics.mean(annual_maxima), 3) if annual_maxima else 0,
            'std_dev': round(statistics.stdev(annual_maxima), 3) if len(annual_maxima) > 1 else 0,
            'years_count': len(annual_maxima),
            'events': [
                {'year': y, 'max_flow': v['max'], 'date': v['max_date']}
                for y, v in sorted(annual_flows.items(), key=lambda x: x[1]['max'], reverse=True)[:10]
            ]
        }

        extreme_threshold = stats['percentiles']['p99']
        extreme_events = [
            {'date': f['date'], 'flow_cumecs': f['flow_cumecs']}
            for f in daily_flows if f['flow_cumecs'] >= extreme_threshold
        ]
        stats['extreme_events'] = {
            'threshold_p99': extreme_threshold,
            'count': len(extreme_events),
            'top_10': sorted(extreme_events, key=lambda x: x['flow_cumecs'], reverse=True)[:10]
        }

        return stats

    def filter_by_years(self, daily_flows: List[Dict[str, Any]],
                        years: Optional[int] = None) -> List[Dict[str, Any]]:
        """Filter flows to most recent N years."""
        if years is None or not daily_flows:
            return daily_flows
        dates = [datetime.strptime(f['date'], '%Y-%m-%d') for f in daily_flows]
        max_date = max(dates)
        cutoff_date = max_date.replace(year=max_date.year - years)
        return [f for f in daily_flows
                if datetime.strptime(f['date'], '%Y-%m-%d') >= cutoff_date]

    def generate(self, input_path: Path, output_path: Optional[Path] = None,
                 years: Optional[int] = None, gauge_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON file from NRFA CSV."""
        metadata, all_flows = self.parse_nrfa_csv(input_path)
        station_id = gauge_id or metadata.get('station_id', input_path.stem.replace('_gdf', ''))
        years_to_use = years if years is not None else self.years_of_history
        filtered_flows = self.filter_by_years(all_flows, years_to_use)
        stats = self.calculate_statistics(filtered_flows)

        from port.src.gauge.gaugehd.common import build_station_metadata
        station_metadata = build_station_metadata(station_id, metadata)

        output_data = {
            'schema_version': self.SCHEMA_VERSION,
            'data_type': 'GaugeHistoricalDaily',
            'generated_at': datetime.now().isoformat(),
            'generator': 'gaugehd',
            'years_included': years_to_use,
            'station_metadata': station_metadata,
            'statistics': stats,
            'daily_flows': filtered_flows
        }

        if output_path is None:
            output_dir = config.input_dir
            output_path = output_dir / f"gaugehd_{station_id}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info("Generated: %s", output_path)
        logger.info("Station: %s (%s)", station_metadata['station_name'], station_id)
        logger.info("Records: %d days (%s years)", len(filtered_flows), stats.get('total_years', 0))
        logger.info("Mean Flow: %s m3/s", stats.get('mean_flow', 'N/A'))
        logger.info("Max Flow: %s m3/s on %s", stats.get('max_flow', 'N/A'), stats.get('max_flow_date', 'N/A'))

        return output_data

    def get_nrfa_metadata_for_cdm(self, stats: Dict[str, Any],
                                   station_metadata: Dict[str, str],
                                   output_filename: str) -> Dict[str, Any]:
        """Extract NRFA metadata fields for updating gauge CDM."""
        return {
            'NRFAStationID': station_metadata.get('station_id'),
            'GridReference': station_metadata.get('grid_reference'),
            'CatchmentArea': None,
            'RecordStartDate': stats.get('record_start'),
            'RecordEndDate': stats.get('record_end'),
            'MeanFlow': stats.get('mean_flow'),
            'MedianFlow': stats.get('median_flow'),
            'Q95Flow': stats.get('q95_flow'),
            'Q5Flow': stats.get('q5_flow'),
            'MaxRecordedFlow': stats.get('max_flow'),
            'MaxRecordedFlowDate': stats.get('max_flow_date'),
            'HistoricalDataFile': output_filename,
            'DatabaseSource': station_metadata.get('database_name'),
            'FlowUnits': station_metadata.get('units', 'm3/s'),
            'DataQualityNotes': station_metadata.get('description_flow_record', '')[:500]
        }
