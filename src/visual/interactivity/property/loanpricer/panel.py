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
Loan Pricer popup panel for property and commercial markers.

Provides an editable set of loan inputs (balance, value, rate, term, flood
risk, …) and prices them live against the server-side LoanPricer via the
``/loan-pricer`` route. Residential (PROP-) and commercial (CPROP-) assets
share one panel; the asset-id prefix selects the endpoint.

The (large) client-side JS/HTML body lives in ``template.py``; this module
holds only the Python handler that parameterises and injects it.
"""

from typing import Any, Dict

import folium

from .template import LOAN_PRICER_JS_TEMPLATE


class LoanPricerPanel:
    """Handler for the interactive Loan Pricer popup."""

    def __init__(self,
                 panel_width: str = "720px",
                 panel_height: str = "680px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for the loan pricer panel."""
        return LOAN_PRICER_JS_TEMPLATE.format(
            panel_width=self.panel_width,
            panel_height=self.panel_height,
        )

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add loan pricer panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
