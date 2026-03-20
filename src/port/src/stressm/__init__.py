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

"""Multi-storm stress pipeline package."""

from .pipeline import (
    generate_stressm,
    GAUGE_SUMMARY_FILENAME, SCHEMA_VERSION_SPATIAL,
)
from .gaugets_writer import populate_gaugets, write_classifier_summary, build_summary
from .classifier import train_gauge_stressm_classifier, _print_classifier_result
from .gauge_parser import (
    _extract_gauges, _parse_gauge, _load_gaugehd_baselines, _seasonal_base_level,
)
from .reporting import _print_gauge_progression

__all__ = [
    'generate_stressm',
    'populate_gaugets',
    'write_classifier_summary',
    'build_summary',
    'train_gauge_stressm_classifier',
    'GAUGE_SUMMARY_FILENAME',
    'SCHEMA_VERSION_SPATIAL',
    '_extract_gauges',
    '_parse_gauge',
    '_print_classifier_result',
    '_print_gauge_progression',
]
