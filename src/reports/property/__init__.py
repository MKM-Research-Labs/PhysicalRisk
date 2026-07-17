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
Property Report Generation Package

This package provides comprehensive property report generation capabilities,
orchestrating multiple page modules to create detailed property analysis reports.

Main Components:
- PropertyReportGenerator: Main class for generating property reports
- generate_property_report: Convenience function for simple report generation
- Individual page modules for each section of the report

Usage:
    from reports.property import generate_property_report, PropertyReportGenerator

    # Simple usage with convenience function
    report_path = generate_property_report(
        property_data=property_data,
        rloan_data=rloan_data,
        report_type="full"
    )

    # Advanced usage with generator class
    generator = PropertyReportGenerator(output_dir="./reports")
    report_path = generator.generate_report(property_data, rloan_data)
"""

from .generator import PropertyReportGenerator  # noqa: F401
from .property_generator import generate_property_report  # noqa: F401

__all__ = [
    'PropertyReportGenerator',
    'generate_property_report'
]

__version__ = '1.0.0'
