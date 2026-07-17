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
Property hazard curve and PRS pricing visualization.

Interactive Chart.js tabbed panel showing property-level hazard curves,
term structures, 6-component PRS pricing, and Basis Explorer with
storm journey visualisation (Gauge -> SHE -> SHD -> Property).

Sub-modules:
- phc_hazard: Hazard Curve tab (exceedance probability, GEV)
- phc_term: Term Structure tab (survival probability, hazard rates)
- phc_prs: PRS Pricing tab (controls, pricer, cashflows, commit)
- phc_basis: Basis Analysis (legacy, retained for backward compat)
- phc_basis_gauge: Basis Explorer — Gauge sub-tab
- phc_basis_she: Basis Explorer — SHE sub-tab
- phc_basis_shd: Basis Explorer — SHD sub-tab
- phc_basis_property: Basis Explorer — Property sub-tab
"""

from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static
from visual.interactivity.panel_mixin import FoliumPanelMixin
from .. import phc_hazard, phc_term, phc_prs, phc_basis
from .. import phc_basis_gauge, phc_basis_she, phc_basis_shd, phc_basis_property
from .. import phc_basis_waterfall, phc_peril_outcomes
from . import panel_create, panel_tabs, panel_data, panel_basis_strip


class PropertyHazardCurvePanel(FoliumPanelMixin):
    """Handler for interactive property hazard curve / PRS pricing dashboard."""

    def __init__(self,
                 panel_width: str = "1100px",
                 panel_height: str = "92vh"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for property hazard curve panel.

        The IIFE shell lives in ``src/static/js/propertyhc-panel.js``; panel
        dimensions and every sub-module fragment are spliced in via
        ``__TOKEN__`` placeholders.
        """
        js = (
            js_static('propertyhc-panel.js')
            .replace('__PANEL_W__', self.panel_width)
            .replace('__PANEL_H__', self.panel_height)
            .replace('__PHC_HAZARD_JS__', phc_hazard.get_js())
            .replace('__PHC_TERM_JS__', phc_term.get_js())
            .replace('__PHC_PRS_JS__', phc_prs.get_js())
            .replace('__PHC_BASIS_JS__', phc_basis.get_js())
            .replace('__PHC_BASIS_WATERFALL_JS__', phc_basis_waterfall.get_js())
            .replace('__PHC_PERIL_OUTCOMES_JS__', phc_peril_outcomes.get_js())
            .replace('__PHC_BASIS_GAUGE_JS__', phc_basis_gauge.get_js())
            .replace('__PHC_BASIS_SHE_JS__', phc_basis_she.get_js())
            .replace('__PHC_BASIS_SHD_JS__', phc_basis_shd.get_js())
            .replace('__PHC_BASIS_PROPERTY_JS__', phc_basis_property.get_js())
            .replace('__PHC_PANEL_CREATE_JS__', panel_create.get_js())
            .replace('__PHC_PANEL_TABS_JS__', panel_tabs.get_js())
            .replace('__PHC_PANEL_DATA_JS__', panel_data.get_js())
            .replace('__PHC_PANEL_BASIS_STRIP_JS__', panel_basis_strip.get_js())
        )
        return f"<script>\n{js}\n</script>"

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
