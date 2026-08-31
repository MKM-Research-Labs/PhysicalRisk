// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

function renderMrcParticipants(m) {
    var items = m.participants || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + items.length + ' participant' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showParticipantForm()" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">+ Add Participant</button>';
    html += '</div>';

    html += '<div id="mrc-participant-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);padding:var(--space-wide);text-align:center;">No participants yet. Click "+ Add Participant" to add one.</div>';
        return html;
    }

    html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['Name', 'Role', 'Organisation', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    items.forEach(function(p) {
        var sc = p.status === 'Attended' ? 'var(--green)' : p.status === 'Invited' ? 'var(--accent)' : p.status === 'Apologies' ? 'var(--amber)' : 'var(--muted)';
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;">' + p.name + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (p.role || '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (p.organisation || '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(p.status, sc) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">';
        html += '<button onclick="window.MG.showParticipantForm(\'' + p.id + '\')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--accent);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--accent);margin-right:var(--space-2);">Edit</button>';
        html += '<button onclick="window.MG.deleteParticipant(\'' + p.id + '\')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--red);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--red);">Del</button>';
        html += '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showParticipantForm(editId) {
    var area = document.getElementById('mrc-participant-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editId) {
        existing = (m.participants || []).find(function(p) { return p.id === editId; });
    }

    var html = '<div style="padding:var(--space-6);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' + (existing ? 'Edit Participant ' + editId : 'New Participant') + '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Name</label>';
    html += '<input type="text" id="mrc-pf-name" value="' + (existing ? existing.name : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Role</label>';
    html += '<input type="text" id="mrc-pf-role" value="' + (existing ? (existing.role || '') : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);margin-top:var(--space-4);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Organisation</label>';
    html += '<input type="text" id="mrc-pf-org" value="' + (existing ? (existing.organisation || '') : 'MKM Research Labs') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Status</label>';
    html += '<select id="mrc-pf-status" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    ['Invited', 'Attended', 'Apologies', 'Declined'].forEach(function(s) {
        html += '<option value="' + s + '"' + (existing && existing.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div></div>';
    html += '<div style="display:flex;gap:var(--space-4);margin-top:var(--space-4);">';
    html += '<button onclick="window.MG.saveParticipant(\'' + (editId || '') + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-participant-form-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveParticipant(editId) {
    var m = window._mrcMeeting;
    var name = document.getElementById('mrc-pf-name').value.trim();
    if (!name) { alert('Name is required'); return; }
    var body = {
        name: name,
        role: document.getElementById('mrc-pf-role').value.trim(),
        organisation: document.getElementById('mrc-pf-org').value.trim(),
        status: document.getElementById('mrc-pf-status').value,
    };
    if (editId) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/participants/' + editId + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/participants', body, m.id);
    }
}

function deleteParticipant(participantId) {
    if (!confirm('Remove participant ' + participantId + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/participants/' + participantId + '/delete', {}, m.id);
}

// ================================================================
// Models in scope (read-only)
// ================================================================
function renderMrcModelsInScope(m) {
    var ids = m.models_in_scope || [];
    if (ids.length === 0) return '<div style="color:var(--muted);font-size:var(--size-sm);">No models in scope.</div>';

    var allModels = (mgData && mgData.models) ? mgData.models : [];
    var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['Model ID', 'Name', 'Tier', 'RAG', 'Status'].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    ids.forEach(function(mid) {
        var info = allModels.find(function(x) { return x.model_id === mid; });
        html += '<tr style="cursor:pointer;" onmouseenter="this.style.background=\'var(--sunken)\'" onmouseleave="this.style.background=\'\'" onclick="window.MG.showDetail(\'' + mid + '\')">';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;color:var(--accent);">' + mid + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (info ? info.short_name : mid) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (info ? tierBadge(info.tier) : '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (info ? ragBadge(info.rag_rating) : '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (info ? reviewBadge(info.review_status) : '\u2014') + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

// ================================================================
// Decisions — with Add / Edit / Delete
// ================================================================
function renderMrcDecisions(m) {
    var items = m.decisions || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + items.length + ' decision' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showDecisionForm()" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">+ Add Decision</button>';
    html += '</div>';

    html += '<div id="mrc-decision-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);padding:var(--space-wide);text-align:center;">No decisions recorded yet.</div>';
        return html;
    }

    html += '<div style="display:flex;flex-direction:column;gap:var(--space-4);">';
    items.forEach(function(d) {
        html += '<div style="padding:var(--space-5) var(--space-7);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--control);border-left:3px solid var(--accent);">';
        html += '<div style="display:flex;align-items:center;justify-content:space-between;">';
        html += '<div style="display:flex;align-items:center;gap:var(--space-4);">';
        html += '<span style="font-size:var(--size-xxs);font-weight:700;color:var(--accent);background:var(--accent-soft);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-sm);">' + d.id + '</span>';
        html += '<span style="font-size:var(--size-xxs);color:var(--muted);">' + d.date + '</span>';
        html += '</div>';
        html += '<div>';
        html += '<button onclick="window.MG.showDecisionForm(\'' + d.id + '\')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--accent);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--accent);margin-right:var(--space-2);">Edit</button>';
        html += '<button onclick="window.MG.deleteDecision(\'' + d.id + '\')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--red);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--red);">Del</button>';
        html += '</div></div>';
        html += '<div style="font-size:var(--size-sm);color:var(--text);margin-top:var(--space-3);">' + d.description + '</div>';
        html += '</div>';
    });
    html += '</div>';
    return html;
}

function showDecisionForm(editId) {
    var area = document.getElementById('mrc-decision-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editId) {
        existing = (m.decisions || []).find(function(d) { return d.id === editId; });
    }

    var html = '<div style="padding:var(--space-6);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' + (existing ? 'Edit Decision ' + editId : 'New Decision') + '</div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Description</label>';
    html += '<textarea id="mrc-df-desc" rows="3" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;">' + (existing ? existing.description : '') + '</textarea></div>';
    html += '<div style="display:flex;gap:var(--space-4);margin-top:var(--space-4);align-items:flex-end;">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Date</label>';
    html += '<input type="date" id="mrc-df-date" value="' + (existing ? existing.date : m.date) + '" style="font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);"></div>';
    html += '<button onclick="window.MG.saveDecision(\'' + (editId || '') + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-decision-form-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveDecision(editId) {
    var m = window._mrcMeeting;
    var desc = document.getElementById('mrc-df-desc').value.trim();
    if (!desc) { alert('Description is required'); return; }
    var body = {
        description: desc,
        date: document.getElementById('mrc-df-date').value,
    };
    if (editId) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/decisions/' + editId + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/decisions', body, m.id);
    }
}

function deleteDecision(decisionId) {
    if (!confirm('Delete decision ' + decisionId + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/decisions/' + decisionId + '/delete', {}, m.id);
}

// ================================================================
// Actions — with Add / Edit / Delete
// ================================================================
function renderMrcActions(m) {
    var items = m.actions || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + items.length + ' action' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showActionForm()" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">+ Add Action</button>';
    html += '</div>';

    html += '<div id="mrc-action-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);padding:var(--space-wide);text-align:center;">No actions recorded yet.</div>';
        return html;
    }

    html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['ID', 'Action', 'Owner', 'Target Date', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    items.forEach(function(a) {
        var sc = a.status === 'Open' ? 'var(--amber)' : a.status === 'Closed' ? 'var(--green)' : 'var(--accent)';
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;color:var(--accent);">' + a.id + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + a.description + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + a.owner + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + a.target_date + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(a.status, sc) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">';
        html += '<button onclick="window.MG.showActionForm(\'' + a.id + '\')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--accent);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--accent);margin-right:var(--space-2);">Edit</button>';
        html += '<button onclick="window.MG.deleteAction(\'' + a.id + '\')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--red);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--red);">Del</button>';
        html += '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showActionForm(editId) {
    var area = document.getElementById('mrc-action-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editId) {
        existing = (m.actions || []).find(function(a) { return a.id === editId; });
    }

    var html = '<div style="padding:var(--space-6);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' + (existing ? 'Edit Action ' + editId : 'New Action') + '</div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Description</label>';
    html += '<textarea id="mrc-actf-desc" rows="2" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;">' + (existing ? existing.description : '') + '</textarea></div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-4);margin-top:var(--space-4);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Owner</label>';
    html += '<input type="text" id="mrc-actf-owner" value="' + (existing ? existing.owner : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Target Date</label>';
    html += '<input type="date" id="mrc-actf-date" value="' + (existing ? existing.target_date : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Status</label>';
    html += '<select id="mrc-actf-status" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    ['Open', 'In Progress', 'Closed'].forEach(function(s) {
        html += '<option value="' + s + '"' + (existing && existing.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div></div>';
    html += '<div style="display:flex;gap:var(--space-4);margin-top:var(--space-4);">';
    html += '<button onclick="window.MG.saveAction(\'' + (editId || '') + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-action-form-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveAction(editId) {
    var m = window._mrcMeeting;
    var desc = document.getElementById('mrc-actf-desc').value.trim();
    if (!desc) { alert('Description is required'); return; }
    var body = {
        description: desc,
        owner: document.getElementById('mrc-actf-owner').value.trim(),
        target_date: document.getElementById('mrc-actf-date').value,
        status: document.getElementById('mrc-actf-status').value,
    };
    if (editId) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/actions/' + editId + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/actions', body, m.id);
    }
}

function deleteAction(actionId) {
    if (!confirm('Delete action ' + actionId + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/actions/' + actionId + '/delete', {}, m.id);
}

