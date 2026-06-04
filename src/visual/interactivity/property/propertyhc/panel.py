# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

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

from visual.interactivity.panel_mixin import FoliumPanelMixin
from .. import phc_hazard, phc_term, phc_prs, phc_basis
from .. import phc_basis_gauge, phc_basis_she, phc_basis_shd, phc_basis_property
from .. import phc_basis_waterfall, phc_peril_outcomes
from . import panel_create, panel_tabs, panel_data, panel_basis_strip


class PropertyHazardCurvePanel(FoliumPanelMixin):
    """Handler for interactive property hazard curve / PRS pricing dashboard."""

    def __init__(self,
                 panel_width: str = "1100px",
                 panel_height: str = "750px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for property hazard curve panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var currentChart = null;
            var phcPanel = null;
            var phcData = null;
            var counterpartyData = [];

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
{phc_hazard.get_js()}
{phc_term.get_js()}
{phc_prs.get_js()}
{phc_basis.get_js()}
{phc_basis_waterfall.get_js()}
{phc_peril_outcomes.get_js()}
{phc_basis_gauge.get_js()}
{phc_basis_she.get_js()}
{phc_basis_shd.get_js()}
{phc_basis_property.get_js()}

            // ==============================================================
            // Panel creation
            // ==============================================================
{panel_create.get_js()}

            // ==============================================================
            // Tab switching
            // ==============================================================
{panel_tabs.get_js()}

            // ==============================================================
            // Show / Hide
            // ==============================================================
            function showPanel(propertyId) {{
                console.log('[PropertyHazard] Opening panel for', propertyId);
                var panel = createPanel();
                panel.dataset.propertyId = propertyId;
                var isCommercial = (typeof propertyId === 'string'
                                     && propertyId.indexOf('CPROP-') === 0);
                var titleLabel = isCommercial
                    ? 'Commercial PRS Pricer: '
                    : 'PRS Pricer: ';
                document.getElementById('phc-panel-title').textContent =
                    titleLabel + window.propertyDisplayName(propertyId);
                document.getElementById('phc-status').textContent = 'Loading...';
                panel.style.display = 'flex';

                activeTab = 0;
                switchTab(0);
                loadData(propertyId);
            }}

            function hidePanel() {{
                if (phcPanel) phcPanel.style.display = 'none';
                if (currentChart) {{ currentChart.destroy(); currentChart = null; }}
                if (basisGaugeChart) {{ basisGaugeChart.destroy(); basisGaugeChart = null; }}
                if (basisSHEChart) {{ basisSHEChart.destroy(); basisSHEChart = null; }}
                if (basisSHDChart) {{ basisSHDChart.destroy(); basisSHDChart = null; }}
                if (basisPropertyChart) {{ basisPropertyChart.destroy(); basisPropertyChart = null; }}
                if (_basisWaterfallChart) {{ _basisWaterfallChart.destroy(); _basisWaterfallChart = null; }}
                if (_perilOutcomesChart) {{ _perilOutcomesChart.destroy(); _perilOutcomesChart = null; }}
                var subBar = document.getElementById('phc-basis-subtab-bar');
                if (subBar) subBar.remove();
                basisSelectedStorm = null;
                basisActiveSubTab = 0;
                phcData = null;
                console.log('[PropertyHazard] Panel closed');
            }}

            // ==============================================================
            // Data loading
            // ==============================================================
{panel_data.get_js()}

            // ==============================================================
            // Basis summary strip — storm journey at a glance
            // ==============================================================
{panel_basis_strip.get_js()}

            // ==============================================================
            // Event listeners
            // ==============================================================
            document.addEventListener('propertyHazardRequested', function(e) {{
                if (e.detail && e.detail.propertyId) showPanel(e.detail.propertyId);
            }});

            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape' && phcPanel && phcPanel.style.display !== 'none') {{
                    hidePanel();
                }}
            }});

            window.PropertyHazardCurvePanel = {{
                show: showPanel,
                hide: hidePanel
            }};

            console.log('Property hazard curve panel ready');
        }})();
        </script>
        """

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
