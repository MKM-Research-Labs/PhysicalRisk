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

"""Integration tests for single property flood analysis workflow."""

from tests.reports.property._helpers import (
    find_nearest_gauge,
    load_gauge_data,
    load_property_data,
    run_single_property_test,
)


class TestSinglePropertyAnalysis:
    """Integration tests for single property flood analysis."""

    def test_load_property_data(self, thames_input_dir):
        properties = load_property_data(thames_input_dir)
        assert properties is not None
        assert len(properties) == 3
        assert "property_id" in properties.columns
        assert "latitude" in properties.columns
        assert "elevation" in properties.columns

    def test_load_gauge_data(self, thames_input_dir):
        gauge_meta, gauge_readings = load_gauge_data(thames_input_dir)
        assert gauge_meta is not None
        assert len(gauge_meta) == 3
        assert gauge_readings is not None
        assert "THAMES_TEDDINGTON" in gauge_readings

    def test_find_nearest_gauge(self, sample_gauges):
        gauge_id, distance = find_nearest_gauge(51.4310, -0.3215, sample_gauges)
        assert gauge_id == "THAMES_TEDDINGTON"
        assert distance < 1.0

    def test_full_analysis_low_risk_property(self, thames_input_dir):
        results = run_single_property_test(thames_input_dir, property_index=2)
        assert results["success"] is True
        assert results["property"]["property_id"] == "THAMES_TEST_003"
        assert results["flood_analysis"]["risk_level"] == "MINIMAL"
        assert results["flood_analysis"]["flood_depth_m"] == 0.0

    def test_full_analysis_high_risk_property(self, thames_input_dir):
        results = run_single_property_test(thames_input_dir, property_index=1)
        assert results["success"] is True
        assert results["property"]["property_id"] == "THAMES_TEST_002"
        assert results["flood_analysis"]["flood_depth_m"] >= 0.0
