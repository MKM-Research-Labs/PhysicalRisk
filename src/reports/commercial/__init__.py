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

"""Commercial asset PDF report.

Mirrors the property report shape but:
  - reads CommercialAsset.* (CDM root differs from PropertyHeader.* used
    by the residential CDM);
  - replaces residential-only sections (PropertyAttributes, Contents)
    with commercial-only sections (CommercialAttributes,
    AccessibilityFeatures, Tenancy);
  - reads the commercial_loan.json sibling rather than mortgage.json;
  - shares all other section renderers via ``reports.asset``.
"""

from .commercial_report import generate_commercial_report, generate_cloan_report
from .generator import CommercialReportGenerator

__all__ = [
    "CommercialReportGenerator",
    "generate_commercial_report",
    "generate_cloan_report",
]
