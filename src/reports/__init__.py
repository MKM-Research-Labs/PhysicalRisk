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

#
# This software is provided under license by MKM Research Labs.
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

"""
MKM Research Labs Reports Package

Comprehensive reporting system for gauge, property, and risk analysis.

Structure:
---------
reports/
├── gauge/          - Flood gauge reports
├── property/       - Property analysis reports (future)
├── risk/           - Risk assessment reports (future)
└── utils/          - Shared utilities

Usage:
------
from reports.gauge import generate_gauge_report

report_path = generate_gauge_report(
    gauge_data={'FloodGauge': {...}},
    output_dir='output/gauge/',
    report_type='basic'
)
"""

# Gauge reports
from .gauge import (
    GaugeReportGenerator,
    generate_gauge_report,
    generate_report_for_gauge,
    get_available_gauges,
    validate_gauge_exists,
)

# Shared utilities
from .utils import open_pdf_file

# Property reports (placeholder for future)
# from .property import PropertyReportGenerator, generate_property_report

# Risk reports (placeholder for future)
# from .risk import RiskReportGenerator, generate_risk_report

__all__ = [
    # Gauge
    'GaugeReportGenerator',
    'generate_gauge_report',
    'generate_report_for_gauge',
    'get_available_gauges',
    'validate_gauge_exists',

    # Utils
    'open_pdf_file',

    # Property (uncomment when ready)
    # 'PropertyReportGenerator',
    # 'generate_property_report',

    # Risk (uncomment when ready)
    # 'RiskReportGenerator',
    # 'generate_risk_report',
]

__version__ = '1.0.0'
__author__ = 'MKM Research Labs'
