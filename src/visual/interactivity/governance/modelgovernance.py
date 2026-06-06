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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""
Regulatory Compliance Dashboard panel.

Interactive panel with its own Leaflet control button (top-right) showing:
- Model inventory with tier badges and status indicators
- Detail view per model with tabs (overview, limitations, assumptions, audit trail)
- Workflow indicators for review dates and validation status
- Model chain dependency diagram (string of pearls)
- MRC meetings with agenda, minutes, decisions, and actions
- Audit trail viewer

Loads data from:
- /api/v1/governance/models (model inventory summary)
- /api/v1/governance/models/<id> (model detail)
- /api/v1/governance/audit-trail (audit log)
- /api/v1/governance/mrc/meetings (MRC meetings)

Sub-modules:
- mg_helpers: colour maps, badge functions, editable fields, HTML helpers
- mg_edit_modal: edit confirmation modal
- mg_panel_ui: panel creation and expand/restore
- mg_inventory: model inventory table
- mg_detail_header: model detail header
- mg_detail_tabs: model detail tabs
- mg_chain: model chain diagram
- mg_bcbs239: BCBS 239 compliance
- mg_validation: validation questionnaire
- mg_raci: RACI matrix
- mg_mrc: MRC meetings list
- mg_mrc_meeting: MRC meeting detail
- mg_documents: document upload/download management
- mg_bibliography: academic reference management
- mg_audit: audit trail
"""

from typing import Any, Dict

import folium

from visual.interactivity._jsbundle import js_static
from . import (
    mg_audit,
    mg_audit_reports,
    mg_bibliography,
    mg_documents,
    mg_edit_modal,
    mg_helpers,
    mg_main_setup,
    mg_panel_ui,
)
from .models import (
    mg_bcbs239,
    mg_chain,
    mg_detail_header,
    mg_detail_tabs,
    mg_field_lineage,
    mg_inventory,
    mg_lineage,
    mg_validation,
)
from .mrc import mg_mrc, mg_mrc_meeting
from .raci import mg_raci


class ModelGovernancePanel:
    """Handler for model risk governance dashboard panel."""

    def __init__(self,
                 panel_width: str = "1060px",
                 panel_height: str = "700px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for model governance panel.

        The IIFE shell lives in ``src/static/js/modelgovernance-panel.js``;
        panel dimensions and every sub-module fragment are spliced in via
        ``__TOKEN__`` placeholders.
        """
        js = (
            js_static('modelgovernance-panel.js')
            .replace('__PANEL_W__', self.panel_width)
            .replace('__PANEL_H__', self.panel_height)
            .replace('__MG_HELPERS_JS__', mg_helpers.get_js())
            .replace('__MG_EDIT_MODAL_JS__', mg_edit_modal.get_js())
            .replace('__MG_PANEL_UI_JS__', mg_panel_ui.get_js())
            .replace('__MG_INVENTORY_JS__', mg_inventory.get_js())
            .replace('__MG_DETAIL_HEADER_JS__', mg_detail_header.get_js())
            .replace('__MG_DETAIL_TABS_JS__', mg_detail_tabs.get_js())
            .replace('__MG_CHAIN_JS__', mg_chain.get_js())
            .replace('__MG_BCBS239_JS__', mg_bcbs239.get_js())
            .replace('__MG_VALIDATION_JS__', mg_validation.get_js())
            .replace('__MG_RACI_JS__', mg_raci.get_js())
            .replace('__MG_MRC_JS__', mg_mrc.get_js())
            .replace('__MG_MRC_MEETING_JS__', mg_mrc_meeting.get_js())
            .replace('__MG_AUDIT_JS__', mg_audit.get_js())
            .replace('__MG_DOCUMENTS_JS__', mg_documents.get_js())
            .replace('__MG_BIBLIOGRAPHY_JS__', mg_bibliography.get_js())
            .replace('__MG_AUDIT_REPORTS_JS__', mg_audit_reports.get_js())
            .replace('__MG_LINEAGE_JS__', mg_lineage.get_js())
            .replace('__MG_FIELD_LINEAGE_JS__', mg_field_lineage.get_js())
            .replace('__MG_MAIN_SETUP_JS__', mg_main_setup.get_js())
        )
        return f"<script>\n{js}\n</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add model governance panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
        }
