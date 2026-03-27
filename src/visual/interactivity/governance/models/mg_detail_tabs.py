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

"""Model Governance detail tabs — all 9 sub-tab renderers."""


def get_js():
    """Return JS fragment for detail tab renderers."""
    return """
// ================================================================
// Detail tab renderers
// ================================================================
function renderOverviewTab(m) {
    var html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">';

    // Left: key details
    html += '<div>';
    html += sectionHeader('Model Details');
    html += infoRow('Description', m.description);
    html += infoRow('Methodology', m.methodology);
    html += infoRow('Tier Rationale', m.tier_rationale);
    html += infoRow('Source Module', '<code style="font-size:11px;background:#f0f0f0;padding:2px 6px;border-radius:3px;">' + m.source_module + '</code>');
    html += infoRow('Materiality', m.materiality);
    html += infoRow('Complexity', m.complexity);
    html += '</div>';

    // Right: governance status
    html += '<div>';
    html += sectionHeader('Governance Status');
    html += infoRow('RAG Rating', ragBadge(m.rag_rating) + editBtn('rag_rating', m.model_id));
    html += infoRow('Model Owner', '<b>' + (m.owner || '\u2014') + '</b>' + (m.model_owner_role ? ' (' + m.model_owner_role + ')' : '') + editBtn('owner', m.model_id));
    html += infoRow('Lifecycle Stage', statusDot(lifecycleColors[m.lifecycle_stage] || '#999') + m.lifecycle_stage + editBtn('lifecycle_stage', m.model_id));
    html += infoRow('Validation Status', m.validation_status + editBtn('validation_status', m.model_id));
    html += infoRow('Last Review', (m.last_review_date || '<span style="color:#f57c00;">Not yet reviewed</span>') + editBtn('last_review_date', m.model_id));
    html += infoRow('MRC Signoff', (m.mrc_signoff_date || '<span style="color:#f57c00;">Pending</span>') + editBtn('mrc_signoff_date', m.model_id));
    html += infoRow('Next Review', (m.next_review_date || 'Not scheduled') + editBtn('next_review_date', m.model_id));
    html += infoRow('Recertification', (m.recertification_date || 'Not scheduled') + editBtn('recertification_date', m.model_id));
    html += infoRow('Review Frequency', (m.review_frequency || '\u2014') + editBtn('review_frequency', m.model_id));
    html += infoRow('Peer Reviewer', (m.peer_reviewer || '<span style="color:#f57c00;">TBD</span>') + editBtn('peer_reviewer', m.model_id));

    html += sectionHeader('Testing');
    var tc = m.test_coverage || {};
    html += infoRow('Unit Tests', tc.unit_tests ? '\u2705 Yes' : '\u274c No');
    html += infoRow('Integration Tests', tc.integration_tests ? '\u2705 Yes' : '\u274c No');
    html += infoRow('Benchmark Tests', tc.benchmark_tests ? '\u2705 Yes (' + (tc.benchmark_reference || '') + ')' : '\u274c No');
    html += infoRow('Test File', tc.test_file ? '<code style="font-size:10px;background:#f0f0f0;padding:2px 4px;border-radius:2px;">' + tc.test_file + '</code>' : '\u2014');

    if (m.alternatives_considered && m.alternatives_considered.length > 0) {
        html += sectionHeader('Alternatives Considered');
        html += '<div style="font-size:11px;color:#555;">';
        m.alternatives_considered.forEach(function(a) {
            html += '<div style="padding:2px 0;">\u2022 ' + a + '</div>';
        });
        html += '<div style="margin-top:6px;font-size:11px;color:#333;font-style:italic;">' + (m.methodology_rationale || '') + '</div>';
        html += '</div>';
    }

    // Dependencies
    html += sectionHeader('Dependencies');
    html += infoRow('Upstream', (m.upstream_models && m.upstream_models.length > 0) ? m.upstream_models.join(', ') : 'None (input model)');
    html += infoRow('Downstream', (m.downstream_models && m.downstream_models.length > 0) ? m.downstream_models.join(', ') : 'None (terminal model)');

    // Known failure modes
    if (m.known_failure_modes && m.known_failure_modes.length > 0) {
        html += sectionHeader('Known Failure Modes');
        html += '<div style="font-size:11px;color:#555;">';
        m.known_failure_modes.forEach(function(f) {
            html += '<div style="padding:2px 0;color:#d32f2f;">\u26a0 ' + f + '</div>';
        });
        html += '</div>';
    }

    html += '</div></div>';
    return html;
}

function renderRemediationTab(m) {
    var steps = m.remediation_steps || [];
    if (steps.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No remediation steps recorded</div>';

    var openCount = steps.filter(function(r) { return r.status === 'Open'; }).length;
    var closedCount = steps.filter(function(r) { return r.status === 'Closed'; }).length;

    var html = '<div style="padding:12px;">';

    // Summary bar
    html += '<div style="display:flex;gap:16px;margin-bottom:12px;">';
    html += '<div style="padding:8px 14px;border-radius:6px;background:#fff3e0;border-left:3px solid #f57c00;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Open</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#e65100;margin-left:8px;">' + openCount + '</span></div>';
    html += '<div style="padding:8px 14px;border-radius:6px;background:#e8f5e9;border-left:3px solid #388e3c;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Closed</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#388e3c;margin-left:8px;">' + closedCount + '</span></div>';
    html += '<div style="padding:8px 14px;border-radius:6px;background:#f5f5f5;border-left:3px solid #666;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Total</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#333;margin-left:8px;">' + steps.length + '</span></div>';
    html += '</div>';

    // Table
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Description', 'Owner', 'Priority', 'Due Date', 'Status'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    var priorityColors = {'High': '#d32f2f', 'Medium': '#f57c00', 'Low': '#1976d2'};
    var statusColors = {'Open': '#e65100', 'In Progress': '#1976d2', 'Closed': '#388e3c'};

    steps.forEach(function(r) {
        var isOverdue = r.status === 'Open' && r.due_date && new Date(r.due_date) < new Date();
        var rowStyle = isOverdue ? 'background:#fff8e1;' : '';
        html += '<tr style="' + rowStyle + '">';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + r.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + r.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + r.owner + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(r.priority, priorityColors[r.priority] || '#999') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + (r.due_date || '\u2014') + (isOverdue ? ' <span style="color:#d32f2f;font-size:9px;font-weight:600;">OVERDUE</span>' : '') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(r.status, statusColors[r.status] || '#999') + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    return html;
}

function renderVersionHistoryTab(m) {
    var versions = m.version_history || [];
    if (versions.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No version history recorded</div>';

    var html = '<div style="padding:12px;">';

    // Current version banner
    html += '<div style="padding:10px 14px;background:#e3f2fd;border-radius:6px;border-left:3px solid #1976d2;margin-bottom:16px;">';
    html += '<span style="font-size:10px;color:#888;text-transform:uppercase;">Current Version</span>';
    html += '<span style="font-size:16px;font-weight:700;color:#1976d2;margin-left:10px;">v' + m.version + '</span>';
    html += '<span style="font-size:11px;color:#666;margin-left:10px;">' + m.lifecycle_stage + '</span>';
    html += '</div>';

    // Timeline
    html += '<div style="position:relative;padding-left:24px;">';

    // Vertical line
    html += '<div style="position:absolute;left:8px;top:8px;bottom:8px;width:2px;background:#e0e0e0;"></div>';

    versions.slice().reverse().forEach(function(v, i) {
        var isCurrent = v.version === m.version;
        var dotColor = isCurrent ? '#1976d2' : '#9e9e9e';
        var dotSize = isCurrent ? '12px' : '8px';

        html += '<div style="position:relative;padding:10px 0 16px 16px;">';

        // Timeline dot
        html += '<div style="position:absolute;left:-' + (isCurrent ? '18px' : '16px') + ';top:14px;width:' + dotSize + ';height:' + dotSize + ';border-radius:50%;background:' + dotColor + ';border:2px solid white;box-shadow:0 0 0 1px ' + dotColor + ';"></div>';

        // Version card
        html += '<div style="padding:12px 16px;border:1px solid ' + (isCurrent ? '#bbdefb' : '#e0e0e0') + ';border-radius:6px;background:' + (isCurrent ? '#f5f9ff' : 'white') + ';">';

        // Header row
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">';
        html += '<div>';
        html += '<span style="font-size:14px;font-weight:700;color:' + (isCurrent ? '#1976d2' : '#333') + ';">v' + v.version + '</span>';
        if (isCurrent) html += ' ' + badge('Current', '#1976d2');
        html += '</div>';
        html += '<span style="font-size:11px;color:#888;">' + v.date + '</span>';
        html += '</div>';

        // Description
        html += '<div style="font-size:12px;color:#555;margin-bottom:6px;">' + v.description + '</div>';

        // Footer
        html += '<div style="display:flex;gap:16px;font-size:10px;color:#888;">';
        html += '<span>Author: <b>' + v.author + '</b></span>';
        if (v.document) {
            html += '<span>Ref: <span style="color:#1976d2;">' + v.document + '</span></span>';
        }
        html += '</div>';

        html += '</div></div>';
    });

    html += '</div></div>';
    return html;
}

function renderLimitationsTab(m) {
    var lims = m.limitations || [];
    if (lims.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No limitations documented</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Description', 'Impact', 'Monitoring Trigger', 'Compensating Control'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    lims.forEach(function(l) {
        var impactColor = l.impact === 'High' ? '#d32f2f' : l.impact === 'Medium' ? '#f57c00' : '#388e3c';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + l.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + l.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(l.impact, impactColor) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + (l.monitoring_trigger || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#333;">' + (l.compensating_control || '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderAssumptionsTab(m) {
    var assumptions = m.assumptions || [];
    if (assumptions.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No assumptions documented</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['ID', 'Assumption', 'Impact', 'Monitoring', 'Mitigation'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    assumptions.forEach(function(a) {
        var impactColor = a.impact === 'High' ? '#d32f2f' : a.impact === 'Medium' ? '#f57c00' : '#388e3c';
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;white-space:nowrap;">' + a.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + a.description + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(a.impact, impactColor) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#666;">' + (a.monitoring || '\u2014') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-size:10px;color:#333;">' + (a.mitigation || '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderChangesTab(m) {
    var changes = m.change_history || [];
    if (changes.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No change history</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Version', 'Date', 'Author', 'Type', 'Description'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    changes.forEach(function(c) {
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;font-weight:600;">' + c.version + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;">' + c.date + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + c.author + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(c.type, '#1976d2') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + c.description + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderAuditTab(entries) {
    if (!entries || entries.length === 0) return '<div style="padding:20px;text-align:center;color:#888;">No audit entries for this model</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:#fafafa;">';
    ['Timestamp', 'Event', 'User', 'Action', 'Source'].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd;font-size:10px;color:#555;">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    entries.slice().reverse().forEach(function(e) {
        html += '<tr>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;font-size:10px;">' + e.timestamp + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + badge(e.event_type, '#1976d2') + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + e.user + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + e.action + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid #f0f0f0;">' + e.source + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderDocsTab(m) {
    var docUrl = '/api/v1/governance/models/' + m.model_id + '/documentation/pdf';
    var testUrl = '/api/v1/governance/models/' + m.model_id + '/test-results/pdf';
    var analysisUrl = '/api/v1/governance/models/' + m.model_id + '/analysis/pdf';

    var html = '<div style="display:flex;flex-direction:column;height:100%;">';

    // Sub-tab bar
    html += '<div id="mg-docs-subtabs" style="display:flex;gap:0;border-bottom:2px solid #e0e0e0;margin-bottom:12px;">';
    var sections = [
        {id: 'core-docs', label: 'Core Documentation'},
        {id: 'test-results', label: 'Test Results'},
        {id: 'analysis', label: 'Analysis'},
    ];
    sections.forEach(function(s, i) {
        var active = i === 0;
        html += '<button id="mg-docs-btn-' + s.id + '" onclick="window.MG.switchDocsSection(\\'' + s.id + '\\')" ';
        html += 'style="padding:8px 16px;font-size:11px;font-weight:' + (active ? '600' : '400') + ';';
        html += 'border:none;cursor:pointer;background:transparent;';
        html += 'color:' + (active ? '#1976d2' : '#666') + ';';
        html += 'border-bottom:2px solid ' + (active ? '#1976d2' : 'transparent') + ';';
        html += 'margin-bottom:-2px;">' + s.label + '</button>';
    });
    html += '</div>';

    // Section containers
    // -- Core Documentation
    html += '<div id="mg-docs-sec-core-docs" style="flex:1;display:flex;flex-direction:column;">';
    html += _docsPdfSection(docUrl, 'mg-doc-pdf-container', 'Model documentation for ' + m.model_id + ' &mdash; ' + m.name);
    html += '</div>';

    // -- Test Results (hidden initially)
    html += '<div id="mg-docs-sec-test-results" style="flex:1;display:none;flex-direction:column;">';
    html += _docsPdfSection(testUrl, 'mg-test-pdf-container', 'Automated test results for model ' + m.model_id);
    html += '</div>';

    // -- Analysis (hidden initially)
    html += '<div id="mg-docs-sec-analysis" style="flex:1;display:none;flex-direction:column;">';
    html += _docsPdfSection(analysisUrl, 'mg-analysis-pdf-container', 'Model analysis for ' + m.model_id + ' &mdash; sensitivity, stress testing');
    html += '</div>';

    html += '</div>';

    // Check PDF availability for each section
    var checks = [
        {url: docUrl, containerId: 'mg-doc-pdf-container', label: 'No Documentation Available', hint: 'Model documentation PDF has not been generated for ' + m.model_id + '.'},
        {url: testUrl, containerId: 'mg-test-pdf-container', label: 'No Test Results Available', hint: 'Run: <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;">python app.py check tests --pdf</code>'},
        {url: analysisUrl, containerId: 'mg-analysis-pdf-container', label: 'No Analysis Available', hint: 'Run: <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;">python -m docs.models.sensitivities.generate_all_analysis</code>'},
    ];
    checks.forEach(function(c) {
        fetch(c.url, {method: 'HEAD'}).then(function(resp) {
            if (!resp.ok) {
                var el = document.getElementById(c.containerId);
                if (el) {
                    el.innerHTML = '<div style="padding:40px;text-align:center;">' +
                        '<div style="font-size:32px;margin-bottom:12px;">&#x26A0;</div>' +
                        '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">' + c.label + '</div>' +
                        '<div style="font-size:11px;color:#888;">' + c.hint + '</div></div>';
                }
            }
        });
    });

    return html;
}

function _docsPdfSection(pdfUrl, containerId, description) {
    var html = '';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;margin-bottom:8px;">';
    html += '<div style="font-size:12px;color:#666;">' + description + '</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:11px;font-weight:500;">&#x2913; Download PDF</a>';
    html += '</div>';
    html += '<div id="' + containerId + '" style="flex:1;min-height:500px;border:1px solid #e0e0e0;border-radius:6px;overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="500" style="border:none;">';
    html += '<div style="padding:40px;text-align:center;">';
    html += '<div style="font-size:32px;margin-bottom:12px;">&#x1F4C4;</div>';
    html += '<div style="font-size:13px;font-weight:600;color:#333;margin-bottom:8px;">PDF Document</div>';
    html += '<div style="font-size:11px;color:#888;margin-bottom:16px;">Your browser cannot display the PDF inline.</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-block;padding:8px 20px;background:#1976d2;color:white;border-radius:4px;text-decoration:none;font-size:12px;">Open PDF</a>';
    html += '</div></object></div>';
    return html;
}

function switchDocsSection(sectionId) {
    var sectionIds = ['core-docs', 'test-results', 'analysis'];
    sectionIds.forEach(function(s) {
        var sec = document.getElementById('mg-docs-sec-' + s);
        var btn = document.getElementById('mg-docs-btn-' + s);
        if (sec) sec.style.display = s === sectionId ? 'flex' : 'none';
        if (btn) {
            btn.style.borderBottomColor = s === sectionId ? '#1976d2' : 'transparent';
            btn.style.color = s === sectionId ? '#1976d2' : '#666';
            btn.style.fontWeight = s === sectionId ? '600' : '400';
        }
    });
}

// ================================================================
// HTML helpers
// ================================================================
function sectionHeader(text) {
    return '<div style="font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-top:16px;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #eee;">' + text + '</div>';
}

function infoRow(label, value) {
    return '<div style="display:flex;padding:3px 0;font-size:11px;">' +
        '<span style="min-width:130px;color:#888;flex-shrink:0;">' + label + '</span>' +
        '<span style="color:#333;">' + value + '</span></div>';
}

"""
