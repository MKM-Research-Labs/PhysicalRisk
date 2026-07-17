# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
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
