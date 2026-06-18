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

"""Coverage tests for the value-formatter error branches: non-numeric
percentage and coordinate inputs."""

from visual.utils.formatters._value import _ValueFormattersMixin as F


class TestValueFormatterErrorBranches:
    def test_format_percentage_non_numeric_returns_str(self):
        # float("abc") raises ValueError -> returns str(value) (lines 96-97).
        assert F.format_percentage("abc") == "abc"

    def test_format_coordinates_non_numeric_returns_na(self):
        # "x" >= 0 raises TypeError -> returns "N/A" (lines 119-120).
        assert F.format_coordinates("x", "y") == "N/A"
