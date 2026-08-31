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

function showRaciEditRole(roleId) {
    var area = document.getElementById('raci-role-edit-area');
    if (!area) return;
    var role = (raciData.roles || []).find(function(r) { return r.role_id === roleId; });
    if (!role) return;

    var html = '<div style="padding:var(--space-8);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-top:var(--space-4);">';
    html += '<div style="font-size:var(--size-sm);font-weight:600;color:var(--text);margin-bottom:var(--space-5);">Edit Role: ' + role.label + ' (' + role.raci_code + ')</div>';

    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);margin-bottom:var(--space-5);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Assigned To</label>';
    html += '<input type="text" id="raci-role-assigned" value="' + (role.assigned_to || '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Backup</label>';
    html += '<input type="text" id="raci-role-backup" value="' + (role.backup || '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '</div>';

    html += '<div style="display:flex;gap:var(--space-4);">';
    html += '<button onclick="window.MG.saveRaciRole(\'' + roleId + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'raci-role-edit-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRaciRole(roleId) {
    console.log('[RACI] Saving role', roleId);
    var body = {
        assigned_to: document.getElementById('raci-role-assigned').value,
        backup: document.getElementById('raci-role-backup').value || null,
        user: 'Dashboard User',
    };

    fetch(getBaseUrl() + '/api/v1/governance/raci/roles/' + roleId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[RACI] Role', roleId, 'saved successfully');
            raciData = data.raci;
            renderRACIDashboard();
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function toggleRaciActivity(activityId) {
    if (raciExpandedActivity === activityId) {
        raciExpandedActivity = null;
    } else {
        raciExpandedActivity = activityId;
    }
    renderRACIDashboard();
}

function showRaciEditActivity(activityId) {
    var area = document.getElementById('raci-activity-edit-area');
    if (!area) return;
    var act = (raciData.activities || []).find(function(a) { return a.activity_id === activityId; });
    if (!act) return;

    var roles = raciData.roles || [];

    var html = '<div style="padding:var(--space-8);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-top:var(--space-4);">';
    html += '<div style="font-size:var(--size-sm);font-weight:600;color:var(--text);margin-bottom:var(--space-5);">Edit Activity: ' + act.activity + '</div>';

    html += '<div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:var(--space-4);margin-bottom:var(--space-5);">';
    ['R', 'A', 'C', 'I'].forEach(function(code) {
        var codeLabel = code === 'R' ? 'Responsible' : code === 'A' ? 'Accountable' : code === 'C' ? 'Consulted' : 'Informed';
        html += '<div><label style="font-size:var(--size-xxs);color:' + raciCodeColor(code) + ';font-weight:600;display:block;margin-bottom:var(--space-1);">' + code + ' \u2014 ' + codeLabel + '</label>';
        html += '<select id="raci-act-' + code + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
        html += '<option value="">None</option>';
        roles.forEach(function(r) {
            html += '<option value="' + r.role_id + '"' + (act[code] === r.role_id ? ' selected' : '') + '>' + r.label + '</option>';
        });
        html += '</select></div>';
    });
    html += '</div>';

    html += '<div style="margin-bottom:var(--space-4);"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Tier Emphasis</label>';
    html += '<input type="text" id="raci-act-tier" value="' + (act.tier_emphasis || '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';

    html += '<div style="margin-bottom:var(--space-5);"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Notes</label>';
    html += '<textarea id="raci-act-notes" rows="2" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;line-height:1.5;">' + (act.notes || '') + '</textarea></div>';

    html += '<div style="display:flex;gap:var(--space-4);">';
    html += '<button onclick="window.MG.saveRaciActivity(\'' + activityId + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'raci-activity-edit-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRaciActivity(activityId) {
    console.log('[RACI] Saving activity', activityId);
    var body = {
        R: document.getElementById('raci-act-R').value || null,
        A: document.getElementById('raci-act-A').value || null,
        C: document.getElementById('raci-act-C').value || null,
        I: document.getElementById('raci-act-I').value || null,
        tier_emphasis: document.getElementById('raci-act-tier').value || null,
        notes: document.getElementById('raci-act-notes').value,
        user: 'Dashboard User',
    };

    fetch(getBaseUrl() + '/api/v1/governance/raci/activities/' + activityId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[RACI] Activity', activityId, 'saved successfully');
            raciData = data.raci;
            renderRACIDashboard();
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function showRaciEditEscalation(triggerId) {
    var area = document.getElementById('raci-escalation-edit-area');
    if (!area) return;
    var trig = (raciData.escalation_triggers || []).find(function(t) { return t.trigger_id === triggerId; });
    if (!trig) return;

    var th = trig.tier_threshold || {};

    var html = '<div style="padding:var(--space-8);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-top:var(--space-4);">';
    html += '<div style="font-size:var(--size-sm);font-weight:600;color:var(--text);margin-bottom:var(--space-5);">Edit Escalation: ' + trig.trigger + '</div>';

    html += '<div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:var(--space-4);margin-bottom:var(--space-5);">';
    ['1', '2', '3'].forEach(function(tier) {
        html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Tier ' + tier + ' Threshold</label>';
        html += '<input type="text" id="raci-esc-t' + tier + '" value="' + (th[tier] || '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    });
    html += '</div>';

    html += '<div style="margin-bottom:var(--space-5);"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Response Required</label>';
    html += '<textarea id="raci-esc-response" rows="2" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;line-height:1.5;">' + (trig.response_required || '') + '</textarea></div>';

    html += '<div style="display:flex;gap:var(--space-4);">';
    html += '<button onclick="window.MG.saveRaciEscalation(\'' + triggerId + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'raci-escalation-edit-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRaciEscalation(triggerId) {
    console.log('[RACI] Saving escalation trigger', triggerId);
    var body = {
        tier_threshold: {
            '1': document.getElementById('raci-esc-t1').value,
            '2': document.getElementById('raci-esc-t2').value,
            '3': document.getElementById('raci-esc-t3').value,
        },
        response_required: document.getElementById('raci-esc-response').value,
        user: 'Dashboard User',
    };

    fetch(getBaseUrl() + '/api/v1/governance/raci/escalation-triggers/' + triggerId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[RACI] Escalation trigger', triggerId, 'saved successfully');
            raciData = data.raci;
            renderRACIDashboard();
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

