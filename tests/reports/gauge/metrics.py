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

"""Tests for gauge statistical metrics."""

from tests.reports.gauge._helpers import (
    calculate_level_range,
    calculate_max_level,
    calculate_max_rate_of_rise,
    calculate_mean_level,
    calculate_min_level,
)


class TestGaugeMetrics:
    """Test gauge statistical metrics."""

    def test_mean_level(self, normal_readings):
        """Calculate mean water level."""
        mean = calculate_mean_level(normal_readings)
        assert 2.5 < mean < 3.5

    def test_max_level(self, flood_event_readings):
        """Calculate maximum level."""
        max_level = calculate_max_level(flood_event_readings)
        assert max_level > 6.0

    def test_min_level(self, normal_readings):
        """Calculate minimum level."""
        min_level = calculate_min_level(normal_readings)
        assert min_level > 0

    def test_level_range(self, flood_event_readings):
        """Calculate level range."""
        level_range = calculate_level_range(flood_event_readings)
        assert level_range > 2.0

    def test_rate_of_rise(self, flood_event_readings):
        """Calculate maximum rate of rise."""
        rate = calculate_max_rate_of_rise(flood_event_readings)
        assert rate > 0
