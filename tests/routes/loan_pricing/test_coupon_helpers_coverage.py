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

"""Coverage tests for the loan-pricing coupon helpers — _truthy numeric/string
branches and the _peril_leg non-numeric / off / negative paths."""

from routes._loan_pricing._coupon import _truthy, _peril_leg


class TestTruthy:
    def test_numeric_nonzero_true_and_zero_false(self):
        assert _truthy(1) is True       # line 43 (int != 0)
        assert _truthy(0.0) is False    # line 43
        assert _truthy(2.5) is True

    def test_string_tokens(self):
        assert _truthy("on") is True    # line 45
        assert _truthy("YES") is True
        assert _truthy("nope") is False

    def test_other_types_false(self):
        assert _truthy(None) is False
        assert _truthy(object()) is False


class TestPerilLeg:
    def test_off_or_missing_is_zero(self):
        assert _peril_leg(100.0, False) == 0.0
        assert _peril_leg(None, True) == 0.0

    def test_non_numeric_spread_returns_zero(self):
        assert _peril_leg("not-a-number", True) == 0.0  # lines 55-56

    def test_negative_spread_returns_zero(self):
        assert _peril_leg(-50.0, True) == 0.0

    def test_positive_spread_to_decimal(self):
        assert _peril_leg(100.0, True) == 0.01
