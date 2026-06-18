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

"""Commercial portfolio generation.

Sub-modules
-----------
main.generator  — CommercialPortfolioGenerator (commercial.json)
ts              — CommercialTimeSeriesGenerator (commercialts/d/e/)
hc              — CommercialHazardCurveGenerator (commercialhc/shd/she.json)
"""

from .hc import CommercialHazardCurveGenerator  # noqa: F401
from .main.generator import CommercialPortfolioGenerator, generate_commercials  # noqa: F401
from .ts import CommercialTimeSeriesGenerator  # noqa: F401

__all__ = [
    "CommercialPortfolioGenerator",
    "CommercialTimeSeriesGenerator",
    "CommercialHazardCurveGenerator",
    "generate_commercials",
]
