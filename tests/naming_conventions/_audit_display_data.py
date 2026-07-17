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

"""Shared constants for audit_display_formats_part*.py.

Pulled out of the audit_display_formats module so each part can stay
around 200 lines while TestAuditCoverage (in part1) still has access
to every _COMPLIANT and _HARDCODED list across all four sections.
"""

# =========================================================================
#  Storm display
# =========================================================================

# Files that correctly use storm_option_js (via __STORM_OPT__ sentinel
# or direct import).
_STORM_COMPLIANT = [
    'src/visual/interactivity/storm/sp_table.py',
    'src/visual/interactivity/storm/fa_render.py',
    'src/visual/interactivity/gauge/gaugehc/ghc_stress_setup.py',
    'src/visual/interactivity/gauge/gaugesa/gsa_timeline.py',
    'src/visual/interactivity/property/psa_timeline.py',
    'src/visual/interactivity/trading/port_stress/setup.py',
    'src/visual/interactivity/trading/stress/setup_data.py',
]

# Files that hardcode storm labels instead of using storm_option_js.
_STORM_HARDCODED = [
    'src/visual/interactivity/gauge/gaugehc/ghc_historical.py',
]


# =========================================================================
#  Gauge display
# =========================================================================

# Files that correctly use gauge_title_js / gauge_title_py (via
# __GAUGE_TITLE__ sentinel or direct import).
_GAUGE_COMPLIANT = [
    'src/visual/interactivity/gauge/gaugesa/panel.py',
    'src/visual/interactivity/gauge/gaugehc/panel_data.py',
    'src/reports/gauge/gauge_page_01_title_overview.py',
    'src/reports/gauge/gauge_page_02_sensor_details.py',
    'src/reports/gauge/gauge_page_03_location.py',
    'src/reports/gauge/gauge_page_04_measurements.py',
    'src/reports/gauge/gauge_page_05_flood_stages.py',
    'src/reports/gauge/gauge_page_06_risk_assessment.py',
]

# Files that hardcode gauge display strings.
_GAUGE_HARDCODED = [
    'src/visual/interactivity/gauge/gaugeha.py',
    'src/visual/interactivity/context_menus.py',
    'src/visual/layer/gauge_layer/marker.py',
    'src/visual/popups/gauge_popup.py',
    'src/visual/interactivity/trading/stress/setup_data.py',
    'src/visual/interactivity/trading/blotter/filters.py',
    'src/visual/interactivity/trading/blotter/actions.py',
    'src/visual/interactivity/trading/port_stress/pfloods.py',
    'src/visual/interactivity/trading/port_stress/portfolio_pnl.py',
    'src/visual/interactivity/trading/fs01/grid.py',
    'src/visual/interactivity/trading/eod/render.py',
    'src/visual/interactivity/trading/td_main_map.py',
    'src/visual/interactivity/trading/aggregate/map_view.py',
    'src/visual/interactivity/property/phc_hazard.py',
    'src/visual/interactivity/property/propertyhc/panel_basis_strip.py',
    'src/visual/interactivity/governance/models/mg_lineage.py',
    'src/visual/interactivity/trading/market/render.py',
    'src/reports/gauge/gauge_integrator.py',
    'src/reports/port/sections.py',
    'src/reports/port/sections_portfolio.py',
]


# =========================================================================
#  Property display
# =========================================================================

# JS files using window.propertyDisplayName (canonical JS helper).
# Panel JS was migrated out of the .py shells into src/static/js
# (see "Extract … inline JS to static/js" commits). The compliant
# propertyDisplayName() usage now lives in the static asset files.
_PROPERTY_COMPLIANT_JS = [
    'src/static/js/propertyhc-panel.js',
    'src/static/js/property/propertyhc/panel_data.js',
    'src/static/js/propertydetails.js',
    'src/static/js/propertysa.js',
    'src/visual/interactivity/property/propertypdf.py',
    'src/static/js/nav-menus.js',
    'src/static/js/trading/aggregate/map_view.js',
    'src/static/js/trading/client/table.js',
]

# Python files using property_title_py from config.format.
# (mortgage_layer/popup.py removed when the legacy mortgage_risk layer
#  was retired — see commit eed780a2.)
_PROPERTY_COMPLIANT_PY = [
    'src/visual/layer/property_layer/layer.py',
    'src/visual/layer/property_layer/popup.py',
    'src/visual/popups/property_popup/builder.py',
    'src/reports/property/property_page_01_title_overview.py',
    'src/reports/property/claim/page1_cover.py',
    'src/reports/risk/risk_page_06_property_details.py',
]

# Files that hardcode property display strings.
_PROPERTY_HARDCODED = [
    'src/visual/interactivity/storm/sp_sim.py',
    'src/visual/interactivity/storm/fa_render.py',
    'src/visual/interactivity/storm/sp_table.py',
    'src/reports/property/property_page_15_data_summary/_core.py',
    'src/reports/property/claim/page5_determination.py',
    'src/reports/rloan/rloan_page_01_title.py',
    'src/reports/port/sections_portfolio.py',
    'src/reports/risk/risk_page_04_risk_analysis.py',
]


# =========================================================================
#  Counterparty / trade display
# =========================================================================

# No centralised format function exists yet in config/format.py.
# All counterparty and swap ID display is currently hardcoded.
# This section tracks every file that renders these labels so that when
# a counterparty_title_js / swap_id_js function is added, migration
# progress is visible.

_COUNTERPARTY_HARDCODED = [
    'src/visual/interactivity/property/phc_prs.py',
    'src/visual/interactivity/gauge/gaugehc/ghc_prs_controls.py',
    'src/visual/interactivity/trading/blotter/table.py',
    'src/visual/interactivity/trading/blotter/actions.py',
    'src/visual/interactivity/trading/client/table.py',
    'src/visual/interactivity/trading/stress/table.py',
    'src/reports/gauge/gauge_page_12_trading.py',
    'src/reports/trading/eod_page_02_positions.py',
    'src/reports/trading/eod_page_03_pnl_detail.py',
]


