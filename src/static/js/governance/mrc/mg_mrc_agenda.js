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

function renderMrcAgenda(m) {
    var items = m.agenda || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + items.length + ' agenda item' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showAgendaForm()" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">+ Add Item</button>';
    html += '</div>';

    html += '<div id="mrc-agenda-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);padding:var(--space-wide);text-align:center;">No agenda items yet. Click "+ Add Item" to create one.</div>';
        return html;
    }

    html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['#', 'Title', 'Presenter', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    items.forEach(function(item) {
        var sc = item.status === 'Completed' ? 'var(--green)' : item.status === 'Pending' ? 'var(--amber)' : 'var(--accent)';
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;width:30px;">' + item.item + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">';
        html += '<div style="font-weight:600;color:var(--text);">' + item.title + '</div>';
        if (item.description) html += '<div style="font-size:var(--size-xxs);color:var(--muted);margin-top:var(--space-1);">' + item.description + '</div>';
        html += '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + (item.presenter || '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(item.status, sc) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">';
        html += '<button onclick="window.MG.showAgendaForm(' + item.item + ')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--accent);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--accent);margin-right:var(--space-2);">Edit</button>';
        html += '<button onclick="window.MG.deleteAgendaItem(' + item.item + ')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--red);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--red);">Del</button>';
        html += '</td>';
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function showAgendaForm(editItemNum) {
    var area = document.getElementById('mrc-agenda-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editItemNum) {
        existing = (m.agenda || []).find(function(a) { return a.item === editItemNum; });
    }

    var html = '<div style="padding:var(--space-6);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' + (existing ? 'Edit Agenda Item #' + editItemNum : 'New Agenda Item') + '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Title</label>';
    html += '<input type="text" id="mrc-af-title" value="' + (existing ? existing.title : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Presenter</label>';
    html += '<input type="text" id="mrc-af-presenter" value="' + (existing ? (existing.presenter || '') : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '</div>';
    html += '<div style="margin-top:var(--space-4);"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Description</label>';
    html += '<input type="text" id="mrc-af-desc" value="' + (existing ? (existing.description || '') : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div style="display:flex;gap:var(--space-4);margin-top:var(--space-4);align-items:flex-end;">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Duration</label>';
    html += '<input type="text" id="mrc-af-duration" value="' + (existing ? (existing.duration || '') : '') + '" placeholder="e.g. 15 min" style="width:100px;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Status</label>';
    html += '<select id="mrc-af-status" style="font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    ['Pending', 'In Progress', 'Completed'].forEach(function(s) {
        html += '<option value="' + s + '"' + (existing && existing.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div>';
    html += '<button onclick="window.MG.saveAgendaItem(' + (editItemNum || 0) + ')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-agenda-form-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveAgendaItem(editItemNum) {
    var m = window._mrcMeeting;
    var title = document.getElementById('mrc-af-title').value.trim();
    if (!title) { alert('Title is required'); return; }
    var body = {
        title: title,
        presenter: document.getElementById('mrc-af-presenter').value.trim(),
        description: document.getElementById('mrc-af-desc').value.trim(),
        duration: document.getElementById('mrc-af-duration').value.trim(),
        status: document.getElementById('mrc-af-status').value,
    };
    if (editItemNum) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/agenda/' + editItemNum + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/agenda', body, m.id);
    }
}

function deleteAgendaItem(itemNum) {
    if (!confirm('Delete agenda item #' + itemNum + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/agenda/' + itemNum + '/delete', {}, m.id);
}

// ================================================================
// Minutes — structured item list with Add / Edit / Delete
// ================================================================
function renderMrcMinutes(m) {
    var minutes = m.minutes;

    // Legacy string format: show as read-only markdown
    if (typeof minutes === 'string') {
        return renderMrcMinutesLegacy(minutes);
    }

    var items = minutes || [];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + items.length + ' minute' + (items.length !== 1 ? 's' : '') + ' item' + (items.length !== 1 ? 's' : '') + '</div>';
    html += '<button onclick="window.MG.showMinuteForm()" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">+ Add Item</button>';
    html += '</div>';

    html += '<div id="mrc-minute-form-area"></div>';

    if (items.length === 0) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);padding:var(--space-wide);text-align:center;">No minutes items yet. Click "+ Add Item" to create one.</div>';
        return html;
    }

    html += '<div style="display:flex;flex-direction:column;gap:var(--space-4);">';
    items.forEach(function(item) {
        html += '<div style="padding:var(--space-5) var(--space-7);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--control);border-left:3px solid var(--accent);">';
        html += '<div style="display:flex;align-items:center;justify-content:space-between;">';
        html += '<div style="display:flex;align-items:center;gap:var(--space-4);">';
        html += '<span style="font-size:var(--size-xxs);font-weight:700;color:var(--accent);background:var(--accent-soft);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-sm);">#' + item.item + '</span>';
        html += '<span style="font-size:var(--size-sm);font-weight:600;color:var(--text);">' + item.title + '</span>';
        if (item.presenter) html += '<span style="font-size:var(--size-xxs);color:var(--muted);">(' + item.presenter + ')</span>';
        html += '</div>';
        html += '<div>';
        html += '<button onclick="window.MG.showMinuteForm(' + item.item + ')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--accent);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--accent);margin-right:var(--space-2);">Edit</button>';
        html += '<button onclick="window.MG.deleteMinuteItem(' + item.item + ')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--red);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--red);">Del</button>';
        html += '</div></div>';
        if (item.text) {
            html += '<div style="font-size:var(--size-xs);color:var(--text-2);margin-top:var(--space-3);line-height:1.6;white-space:pre-wrap;">' + item.text + '</div>';
        }
        html += '</div>';
    });
    html += '</div>';
    return html;
}

function renderMrcMinutesLegacy(text) {
    // Read-only rendering of legacy markdown minutes
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">Meeting Minutes (legacy format)</div>';
    html += '</div>';

    if (!text) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);padding:var(--space-wide);text-align:center;">No minutes recorded.</div>';
        return html;
    }

    var lines = text.split('\n');
    html += '<div style="font-size:var(--size-sm);line-height:1.7;color:var(--text);">';
    var inList = false;
    lines.forEach(function(line) {
        if (line.match(/^### /)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h4 style="font-size:var(--size-sm);font-weight:700;color:var(--accent-mid);margin:var(--space-8) 0 var(--space-3) 0;border-bottom:1px solid var(--line);padding-bottom:var(--space-2);">' + line.replace(/^### /, '') + '</h4>';
        } else if (line.match(/^## /)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h3 style="font-size:var(--size-md);font-weight:700;color:var(--text);margin:var(--space-wide) 0 var(--space-4) 0;">' + line.replace(/^## /, '') + '</h3>';
        } else if (line.match(/^\*\*.*\*\*$/)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<div style="font-weight:600;margin-top:var(--space-4);">' + line.replace(/\*\*/g, '') + '</div>';
        } else if (line.match(/^- /)) {
            if (!inList) { html += '<ul style="margin:var(--space-2) 0;padding-left:var(--space-wide);">'; inList = true; }
            html += '<li>' + line.replace(/^- /, '').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') + '</li>';
        } else if (line.match(/^\d+\. /)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<div style="margin:var(--space-1) 0;padding-left:var(--space-4);">' + line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') + '</div>';
        } else if (line.trim() === '') {
            if (inList) { html += '</ul>'; inList = false; }
        } else {
            html += '<div>' + line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') + '</div>';
        }
    });
    if (inList) html += '</ul>';
    html += '</div>';
    return html;
}

function showMinuteForm(editItemNum) {
    var area = document.getElementById('mrc-minute-form-area');
    if (!area) return;
    var m = window._mrcMeeting;
    var existing = null;
    if (editItemNum) {
        var items = Array.isArray(m.minutes) ? m.minutes : [];
        existing = items.find(function(mi) { return mi.item === editItemNum; });
    }

    var html = '<div style="padding:var(--space-6);border:1px solid var(--line);border-radius:var(--radius-md);background:var(--wash-cool);margin-bottom:var(--space-6);">';
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' + (existing ? 'Edit Minutes Item #' + editItemNum : 'New Minutes Item') + '</div>';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Title</label>';
    html += '<input type="text" id="mrc-mf-title" value="' + (existing ? existing.title : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Presenter</label>';
    html += '<input type="text" id="mrc-mf-presenter" value="' + (existing ? (existing.presenter || '') : '') + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    html += '</div>';
    html += '<div style="margin-top:var(--space-4);"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Minutes Text</label>';
    html += '<textarea id="mrc-mf-text" rows="6" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;line-height:1.5;">' + (existing ? (existing.text || '') : '') + '</textarea></div>';
    html += '<div style="display:flex;gap:var(--space-4);margin-top:var(--space-4);">';
    html += '<button onclick="window.MG.saveMinuteItem(' + (editItemNum || 0) + ')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">' + (existing ? 'Update' : 'Add') + '</button>';
    html += '<button onclick="document.getElementById(\'mrc-minute-form-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';
    area.innerHTML = html;
}

function saveMinuteItem(editItemNum) {
    var m = window._mrcMeeting;
    var title = document.getElementById('mrc-mf-title').value.trim();
    if (!title) { alert('Title is required'); return; }
    var body = {
        title: title,
        presenter: document.getElementById('mrc-mf-presenter').value.trim(),
        text: document.getElementById('mrc-mf-text').value,
    };
    if (editItemNum) {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/minutes-items/' + editItemNum + '/update', body, m.id);
    } else {
        mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/minutes-items', body, m.id);
    }
}

function deleteMinuteItem(itemNum) {
    if (!confirm('Delete minutes item #' + itemNum + '?')) return;
    var m = window._mrcMeeting;
    mrcCrudPost('/api/v1/governance/mrc/meetings/' + m.id + '/minutes-items/' + itemNum + '/delete', {}, m.id);
}

