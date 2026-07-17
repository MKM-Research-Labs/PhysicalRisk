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

"""
Gauge report generation — convenience functions and data helpers.

GaugeReportGenerator class lives in .generator.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .generator import GaugeReportGenerator  # noqa: F401

logger = logging.getLogger(__name__)


def generate_gauge_report(gauge_data: Dict[str, Any],
                         timeseries_data: Optional[Dict[str, Any]] = None,
                         output_dir: Optional[Union[str, Path]] = None,
                         report_type: str = "basic",
                         auto_open: bool = True) -> Path:
    """
    Simple convenience function to generate a gauge report.

    Args:
        gauge_data: Gauge information
        timeseries_data: Timeseries data (optional)
        output_dir: Output directory
        report_type: Type of report ('basic', 'monitoring', 'analysis', 'full')
        auto_open: Whether to automatically open the PDF after generation

    Returns:
        Path to generated PDF
    """
    generator = GaugeReportGenerator(output_dir)

    # Generate the report
    if report_type == 'basic':
        report_path = generator.generate_basic_report(gauge_data, timeseries_data)
    elif report_type == 'monitoring' and timeseries_data:
        report_path = generator.generate_monitoring_report(gauge_data, timeseries_data)
    elif report_type == 'analysis':
        report_path = generator.generate_analysis_report(gauge_data, timeseries_data)
    else:
        report_path = generator.generate_report(gauge_data, timeseries_data)

    # Auto-open the PDF if requested
    if auto_open:
        try:
            from .report_generator import open_pdf_file
            open_pdf_file(report_path)
            logger.info(f"Gauge PDF opened automatically: {report_path}")
        except Exception as e:
            logger.warning(f"Could not auto-open gauge PDF: {e}")
            logger.info(f"Manual open: {report_path}")

    return report_path


def _find_gauge_by_id(data, gauge_id):
    """Find specific gauge in data structure."""
    if isinstance(data, dict):
        if 'flood_gauges' in data:
            gauges = data['flood_gauges']
        elif 'FloodGauge' in data:
            # Single gauge object
            return data
        else:
            raise ValueError("Invalid gauge data structure - no 'flood_gauges' or 'FloodGauge' found")
    elif isinstance(data, list):
        gauges = data
    else:
        raise ValueError("Invalid gauge data structure - must be dict or list")

    for gauge in gauges:
        try:
            gauge_header_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
            if gauge_header_id == gauge_id:
                return gauge
        except (AttributeError, TypeError):
            continue

    raise ValueError(f"Gauge {gauge_id} not found in data")


if __name__ == "__main__":
    import sys

    from reports.shared.base_generator import build_report_cli, handle_info_requests

    def _add_gauge_args(parser):
        parser.add_argument('--gauge-file', required=True, help='Gauge JSON file path')
        parser.add_argument('--timeseries-file', help='Timeseries JSON file path')
        parser.add_argument('--gauge-id', help='Specific gauge ID to process')

    args = build_report_cli(
        description='Generate gauge reports using modular page system.',
        report_type_choices=['basic', 'monitoring', 'analysis', 'full'],
        default_report_type='basic',
        extra_args_fn=_add_gauge_args,
    )

    logging.basicConfig(level=logging.INFO)
    handle_info_requests(args, GaugeReportGenerator())

    try:
        # Load data
        with open(args.gauge_file) as f:
            gauge_data = json.load(f)

        timeseries_data = None
        if args.timeseries_file:
            with open(args.timeseries_file) as f:
                timeseries_data = json.load(f)

        # Handle specific gauge ID
        if args.gauge_id:
            gauge_data = _find_gauge_by_id(gauge_data, args.gauge_id)

        # Generate report
        generator = GaugeReportGenerator(args.output_dir)

        if args.report_type == 'basic':
            report_path = generator.generate_basic_report(gauge_data)
        elif args.report_type == 'monitoring' and timeseries_data:
            report_path = generator.generate_monitoring_report(gauge_data, timeseries_data)
        elif args.report_type == 'analysis':
            report_path = generator.generate_analysis_report(gauge_data, timeseries_data)
        else:
            report_path = generator.generate_report(gauge_data, timeseries_data, args.pages)

        logger.info("Gauge report generated successfully!")
        logger.info(f"File: {report_path}")
        logger.info(f"Type: {args.report_type}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
