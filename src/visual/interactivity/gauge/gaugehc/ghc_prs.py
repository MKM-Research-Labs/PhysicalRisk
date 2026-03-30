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
Gauge hazard curve — PRS Pricing tab.

Tab 3: Controls, analytical pricer (semi-annual cashflows),
PRS pricing table + bar chart, and trade commit.

Sub-modules:
- ghc_prs_rates: Yield curve, maturity dates, survival interpolation
- ghc_prs_controls: Input form + maturity popup
- ghc_prs_pricer: Cashflow engine + chart rendering
- ghc_prs_commit: Trade commit API call
"""

from . import ghc_prs_rates, ghc_prs_controls, ghc_prs_pricer, ghc_prs_commit


def get_js() -> str:
    """Return JS fragment for PRS pricing tab."""
    return (ghc_prs_rates.get_js() +
            ghc_prs_controls.get_js() +
            ghc_prs_pricer.get_js() +
            ghc_prs_commit.get_js())
