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
Property report generation — convenience functions and data helpers.

PropertyReportGenerator class lives in .generator.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from reports.utils.open_pdf import open_pdf_file

from .generator import PropertyReportGenerator  # noqa: F401

logger = logging.getLogger(__name__)


def generate_property_report(property_data: Dict[str, Any],
                        rloan_data: Optional[Dict[str, Any]] = None,
                        output_dir: Optional[Union[str, Path]] = None,
                        report_type: str = "full",
                        auto_open: bool = True) -> Path:
    """
    Simple convenience function to generate a property report.

    Args:
        property_data: Property information
        rloan_data: Mortgage information (optional)
        output_dir: Output directory
        report_type: Type of report ('full', 'property-only', 'mortgage-focused', 'risk-focused')
        auto_open: Whether to automatically open the PDF after generation

    Returns:
        Path to generated PDF
    """
    generator = PropertyReportGenerator(output_dir)

    if report_type == 'property-only':
        report_path = generator.generate_property_only_report(property_data)
    elif report_type == 'mortgage-focused' and rloan_data:
        report_path = generator.generate_mortgage_focused_report(property_data, rloan_data)
    elif report_type == 'risk-focused':
        report_path = generator.generate_risk_focused_report(property_data, rloan_data)
    else:
        report_path = generator.generate_report(property_data, rloan_data)

    if auto_open:
        logger.debug(f"Calling open_pdf_file({report_path})")
        try:
            open_pdf_file(report_path)
            logger.info(f"PDF opened automatically: {report_path}")
        except Exception as e:
            logger.warning(f"Could not auto-open PDF: {e}")
            logger.info(f"Manual open: {report_path}")
    else:
        logger.debug("auto_open is False, skipping PDF open")

    return report_path


def _find_property_by_id(data, property_id):
    """Find specific property in data structure."""
    if isinstance(data, dict):
        if 'properties' in data:
            properties = data['properties']
        elif 'portfolio' in data:
            properties = data['portfolio']
        else:
            properties = [data]
    elif isinstance(data, list):
        properties = data
    else:
        raise ValueError("Invalid property data structure")

    for prop in properties:
        prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
        if prop_id == property_id:
            return prop

    raise ValueError(f"Property {property_id} not found")


def _find_mortgage_by_property_id(data, property_id):
    """Find mortgage for specific property."""
    if isinstance(data, dict):
        mortgages = data.get('loans', [data])
    elif isinstance(data, list):
        mortgages = data
    else:
        return data

    for mortgage in mortgages:
        if mortgage.get('PropertyID') == property_id:
            return mortgage

    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate property reports using modular page system.')

    parser.add_argument('--property-file', required=True, help='Property JSON file path')
    parser.add_argument('--mortgage-file', help='Mortgage JSON file path')
    parser.add_argument('--output-dir', default='reports', help='Output directory')
    parser.add_argument('--property-id', help='Specific property ID to process')
    parser.add_argument('--pages', nargs='+', help='Specific pages to include')
    parser.add_argument('--report-type',
                       choices=['full', 'property-only', 'mortgage-focused', 'risk-focused'],
                       default='full', help='Type of report to generate')
    parser.add_argument('--list-pages', action='store_true', help='List available pages')
    parser.add_argument('--list-categories', action='store_true', help='List page categories')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.list_pages:
        generator = PropertyReportGenerator()
        logger.info("Available pages:")
        for page in generator.list_available_pages():
            logger.info(f"  - {page}")
        sys.exit(0)

    if args.list_categories:
        generator = PropertyReportGenerator()
        logger.info("Page categories:")
        for category, pages in generator.get_page_categories().items():
            logger.info(f"\n{category}:")
            for page in pages:
                logger.info(f"  - {page}")
        sys.exit(0)

    try:
        with open(args.property_file) as f:
            property_data = json.load(f)

        rloan_data = None
        if args.mortgage_file:
            with open(args.mortgage_file) as f:
                rloan_data = json.load(f)

        if args.property_id:
            property_data = _find_property_by_id(property_data, args.property_id)
            if rloan_data:
                rloan_data = _find_mortgage_by_property_id(rloan_data, args.property_id)

        generator = PropertyReportGenerator(args.output_dir)

        if args.report_type == 'property-only':
            report_path = generator.generate_property_only_report(property_data)
        elif args.report_type == 'mortgage-focused' and rloan_data:
            report_path = generator.generate_mortgage_focused_report(property_data, rloan_data)
        elif args.report_type == 'risk-focused':
            report_path = generator.generate_risk_focused_report(property_data, rloan_data)
        else:
            report_path = generator.generate_report(property_data, rloan_data, args.pages)

        logger.info("Report generated successfully!")
        logger.info(f"File: {report_path}")
        logger.info(f"Type: {args.report_type}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
