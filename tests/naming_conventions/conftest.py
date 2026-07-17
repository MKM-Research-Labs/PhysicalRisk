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

"""Shared regex patterns, constants and helpers for naming convention tests."""

import re
from pathlib import Path

# =============================================================================
# Agreed regex patterns (documented protocol)
# =============================================================================

GAUGE_ID_RE  = re.compile(r'^GAUGE-[0-9a-f]{8}$')
PROP_ID_RE   = re.compile(r'^PROP-[0-9a-f]{8}$')
MORT_ID_RE   = re.compile(r'^MORT-[0-9a-f]{8}$')
STORM_ID_RE  = re.compile(r'^STORM-[0-9a-f]{8}$')
PRS_ID_RE    = re.compile(r'^PRS-[0-9a-fA-F]{8}$')  # book uses .upper()

# Files that display property labels — must use config.format
# (src/visual/layer/mortgage_layer/popup.py was removed when the legacy
#  mortgage_risk layer was retired — see commit eed780a2.)
_PROPERTY_DISPLAY_FILES_PY = [
    'src/visual/layer/property_layer/layer.py',
    'src/visual/layer/property_layer/popup.py',
    'src/visual/popups/property_popup/builder.py',
    'src/reports/property/property_page_01_title_overview.py',
    'src/reports/property/claim/page1_cover.py',
    'src/reports/risk/risk_page_06_property_details.py',
]

# Panel JS migrated out of the .py shells into src/static/js
# (see "Extract … inline JS to static/js" commits).
_PROPERTY_DISPLAY_FILES_JS = [
    'src/static/js/propertyhc-panel.js',
    'src/static/js/propertysa.js',
    'src/visual/interactivity/property/propertypdf.py',
    'src/static/js/nav-menus.js',
    'src/static/js/trading/aggregate/map_view.js',
    'src/static/js/trading/client/table.js',
]

# Files that build storm dropdowns — must use pipe-separated format
_STORM_DROPDOWN_FILES = [
    'src/static/js/sp-table.js',
    'src/static/js/storm/fa_render.js',
    'src/static/js/gauge/gaugehc/ghc_stress_setup.js',
    'src/static/js/gauge/gaugesa/gsa_timeline.js',
    'src/static/js/property/psa_timeline.js',
    'src/static/js/trading/port_stress/setup.js',
    'src/static/js/trading/stress/setup_data.js',
]


def _read_source(rel_path: str) -> str:
    root = Path(__file__).resolve().parent.parent.parent
    return (root / rel_path).read_text()
