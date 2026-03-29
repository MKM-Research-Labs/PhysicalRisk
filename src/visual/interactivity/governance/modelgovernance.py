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

from . import (
    mg_audit,
    mg_audit_reports,
    mg_bibliography,
    mg_documents,
    mg_edit_modal,
    mg_helpers,
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
        """Generate JavaScript for model governance panel."""
        return f"""
        <script>
        (function() {{
            var MG_W = '{self.panel_width}';
            var MG_H = '{self.panel_height}';
            var mgPanel = null;
            var mgData = null;
            var mgDetailData = null;
            var mgActiveTab = 'inventory';
            var mgSelectedModel = null;
            var mgSortCol = null;
            var mgSortAsc = true;
            var mgFilters = {{}};
            var mgExpanded = false;

            function getBaseUrl() {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                return cfg.url || '';
            }}

            // ==============================================================
            // Sub-module code
            // ==============================================================
{mg_helpers.get_js()}
{mg_edit_modal.get_js()}
{mg_panel_ui.get_js()}
{mg_inventory.get_js()}
{mg_detail_header.get_js()}
{mg_detail_tabs.get_js()}
{mg_chain.get_js()}
{mg_bcbs239.get_js()}
{mg_validation.get_js()}
{mg_raci.get_js()}
{mg_mrc.get_js()}
{mg_mrc_meeting.get_js()}
{mg_audit.get_js()}
{mg_documents.get_js()}
{mg_bibliography.get_js()}
{mg_audit_reports.get_js()}
{mg_lineage.get_js()}
{mg_field_lineage.get_js()}

            // ================================================================
            // Tab switching
            // ================================================================
            function switchMgTab(tab) {{
                console.log('[Governance] Switching to tab:', tab);
                mgActiveTab = tab;
                mgSelectedModel = null;
                document.getElementById('mg-back-btn').style.display = 'none';
                // Restore default scroll for non-BCBS tabs
                var contentEl = document.getElementById('mg-content');
                if (contentEl) contentEl.style.overflowY = (tab === 'bcbs239' || tab === 'raci') ? 'hidden' : 'auto';
                ['inventory', 'chain', 'params', 'bcbs239', 'raci', 'mrc', 'audit', 'documents', 'bibliography', 'audit-reports', 'lineage', 'field-lineage'].forEach(function(t) {{
                    var btn = document.getElementById('mg-tab-' + t);
                    if (btn) {{
                        btn.style.background = t === tab ? '#1976d2' : 'white';
                        btn.style.color = t === tab ? 'white' : '#333';
                    }}
                }});
                document.getElementById('mg-title').textContent = 'Regulatory Compliance';

                if (tab === 'inventory') renderInventory();
                else if (tab === 'chain') renderModelChain();
                else if (tab === 'bcbs239') renderBCBS239();
                else if (tab === 'raci') renderRACITab();
                else if (tab === 'mrc') renderMRC();
                else if (tab === 'audit') renderAuditTrail();
                else if (tab === 'documents') renderDocuments();
                else if (tab === 'bibliography') renderBibliography();
                else if (tab === 'audit-reports') renderAuditReports();
                else if (tab === 'lineage') renderDataLineage();
                else if (tab === 'field-lineage') renderFieldLineage();
            }}

            // ================================================================
            // Show / hide / navigation
            // ================================================================
            function showInventory() {{
                mgSelectedModel = null;
                document.getElementById('mg-back-btn').style.display = 'none';
                switchMgTab('inventory');
            }}

            function showMgPanel() {{
                console.log('[Governance] Opening panel');
                createPanel();
                mgPanel.style.display = 'flex';
                mgSelectedModel = null;

                var content = document.getElementById('mg-content');
                content.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading model inventory...</div>';

                var baseUrl = getBaseUrl();
                console.log('[Governance] Fetching model inventory from', baseUrl + '/api/v1/governance/models');
                fetch(baseUrl + '/api/v1/governance/models', {{mode: 'cors'}})
                    .then(function(r) {{ return r.json(); }})
                    .then(function(data) {{
                        if (data.status !== 'success') {{
                            content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + (data.message || 'Unknown') + '</div>';
                            return;
                        }}
                        console.log('[Governance] Loaded', data.total_models, 'models');
                        mgData = data;
                        switchMgTab('inventory');
                    }})
                    .catch(function(err) {{
                        content.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load model inventory. Is the server running?</div>';
                        console.error('[Governance] Load error:', err);
                    }});
            }}

            function hideMgPanel() {{
                if (mgPanel) mgPanel.style.display = 'none';
                console.log('[Governance] Panel closed');
            }}

            // ================================================================
            // Map control button (standalone, top-right)
            // ================================================================
            function addMapControl() {{
                function findMap() {{
                    var mapKey = Object.keys(window).find(function(k) {{ return k.startsWith('map_'); }});
                    if (mapKey) return window[mapKey];
                    return null;
                }}

                function tryAdd() {{
                    var map = findMap();
                    if (!map) {{
                        setTimeout(tryAdd, 500);
                        return;
                    }}

                    var GovernanceControl = L.Control.extend({{
                        options: {{ position: 'topright' }},
                        onAdd: function() {{
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = 'Regulatory Compliance';
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:white;';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {{
                                L.DomEvent.preventDefault(e);
                                showMgPanel();
                            }});
                            return container;
                        }}
                    }});

                    new GovernanceControl().addTo(map);
                }}

                setTimeout(tryAdd, 1000);
            }}

            // Global API
            window.showModelGovernance = showMgPanel;
            window.MG = {{
                show: showMgPanel,
                hide: hideMgPanel,
                showDetail: showModelDetail,
                switchDetailTab: switchDetailTab,
                switchDocsSection: switchDocsSection,
                openEdit: openEditModal,
                toggleSort: mgToggleSort,
                setFilter: mgSetFilter,
                setDateFilter: mgSetDateFilter,
                clearFilters: mgClearFilters,
                switchMrcTab: switchMrcSubTab,
                showMeeting: showMrcMeeting,
                switchMeetingTab: switchMeetingTab,
                showNewMeetingForm: showNewMeetingForm,
                createMeeting: createMeeting,
                uploadMeetingDoc: uploadMeetingDoc,
                addNewMeetingDoc: addNewMeetingDoc,
                removeNewMeetingDoc: removeNewMeetingDoc,
                showAgendaForm: showAgendaForm,
                saveAgendaItem: saveAgendaItem,
                deleteAgendaItem: deleteAgendaItem,
                showMinuteForm: showMinuteForm,
                saveMinuteItem: saveMinuteItem,
                deleteMinuteItem: deleteMinuteItem,
                showParticipantForm: showParticipantForm,
                saveParticipant: saveParticipant,
                deleteParticipant: deleteParticipant,
                showDecisionForm: showDecisionForm,
                saveDecision: saveDecision,
                deleteDecision: deleteDecision,
                showActionForm: showActionForm,
                saveAction: saveAction,
                deleteAction: deleteAction,
                downloadMeetingPdf: downloadMeetingPdf,
                toggleBcbs239Principle: toggleBcbs239Principle,
                showBcbs239EditForm: showBcbs239EditForm,
                saveBcbs239Principle: saveBcbs239Principle,
                downloadBcbs239Pdf: downloadBcbs239Pdf,
                toggleVqQuestion: toggleVqQuestion,
                showVqEditForm: showVqEditForm,
                saveVqQuestion: saveVqQuestion,
                showRiskOverrideForm: showRiskOverrideForm,
                saveRiskOverride: saveRiskOverride,
                clearRiskOverride: clearRiskOverride,
                refreshRiskRating: refreshRiskRating,
                showRaciEditRole: showRaciEditRole,
                saveRaciRole: saveRaciRole,
                toggleRaciActivity: toggleRaciActivity,
                showRaciEditActivity: showRaciEditActivity,
                saveRaciActivity: saveRaciActivity,
                showRaciEditEscalation: showRaciEditEscalation,
                saveRaciEscalation: saveRaciEscalation,
                sortBib: window.MG && window.MG.sortBib,
                showBibForm: window.MG && window.MG.showBibForm,
                submitBibRef: window.MG && window.MG.submitBibRef,
                editBibRef: window.MG && window.MG.editBibRef,
                deleteBibRef: window.MG && window.MG.deleteBibRef,
                exportBibtex: window.MG && window.MG.exportBibtex,
                uploadDocument: window.MG && window.MG.uploadDocument,
                downloadDocument: window.MG && window.MG.downloadDocument,
                deleteDocument: window.MG && window.MG.deleteDocument,
            }};

            // Add map control button on load
            addMapControl();

            console.log('Model Governance panel ready');
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add model governance panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
        }
