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
