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

"""Coverage tests for GroundMotionResult.median_pga_g — the empty-samples
None case plus the odd/even median branches."""

from models.seismic.datastructures._groundmotion import (
    GroundMotionResult,
    GroundMotionSample,
)


def _result(pgas):
    samples = [
        GroundMotionSample(draw_index=i, pga_g=v, median_pga_g=v, epsilon=0.0)
        for i, v in enumerate(pgas)
    ]
    return GroundMotionResult(
        asset_id="A1", regime="active_shallow", vs30_mps=400.0,
        site_class="C", amplification_factor=1.0, sigma_total=0.6,
        samples=samples,
    )


class TestMedianPgaG:
    def test_none_when_no_samples(self):
        assert _result([]).median_pga_g is None  # lines 56-57

    def test_odd_count_returns_middle_value(self):
        # sorted -> [0.1, 0.2, 0.3]; mid index 1 -> 0.2
        assert _result([0.3, 0.1, 0.2]).median_pga_g == 0.2  # lines 58-61 (odd)

    def test_even_count_averages_two_middle_values(self):
        # sorted -> [0.1, 0.2, 0.3, 0.4]; 0.5 * (0.2 + 0.3) = 0.25
        assert _result([0.4, 0.1, 0.3, 0.2]).median_pga_g == 0.25  # lines 58-61 (even)
