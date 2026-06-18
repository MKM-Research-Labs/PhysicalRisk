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

"""Coverage tests for the risk-assessment Vs30 -> NEHRP site-class mapping."""

import pytest

from reports.property.property_page_05_risk_assessment._helpers import (
    _RiskHelpersMixin,
)


@pytest.mark.parametrize("vs30,expected", [
    (900, "Rock (Site Class A/B)"),
    (760, "Rock (Site Class A/B)"),
    (500, "Stiff soil (Site Class C)"),
    (360, "Stiff soil (Site Class C)"),
    (250, "Soft soil (Site Class D)"),
    (180, "Soft soil (Site Class D)"),
    (100, "Very soft soil (Site Class E)"),
    (0, "Very soft soil (Site Class E)"),
])
def test_vs30_site_class(vs30, expected):
    assert _RiskHelpersMixin()._vs30_site_class(vs30) == expected  # lines 56-63
