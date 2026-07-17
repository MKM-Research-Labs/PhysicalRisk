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
Gauge Report Generation Package.

Sub-modules:
- gauge_generator: GaugeReportGenerator class
- gauge_integrator: generate_gauge_report(), generate_report_for_gauge(),
                    validate_gauge_exists(), get_available_gauges()
"""

from .gauge_generator import GaugeReportGenerator  # noqa: F401
from .gauge_integrator import (  # noqa: F401
    generate_gauge_report,
    generate_report_for_gauge,
    get_available_gauges,
    validate_gauge_exists,
)

__all__ = [
    'generate_gauge_report',
    'GaugeReportGenerator',
    'validate_gauge_exists',
    'get_available_gauges',
    'generate_report_for_gauge',
]

__version__ = '1.0.0'
__author__ = 'MKM Research Labs'
