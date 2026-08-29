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

var vqExpandedId = null;

var vqStatusColors = Theme.ramp('validation_question');

function vqStatusBadge(status) {
    var c = vqStatusColors[status] || 'var(--grey)';
    return '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;color:var(--inverse);background:' + c + ';">' + (status || 'Not Addressed') + '</span>';
}

function renderValidationTab(m) {
    var questions = m.validation_questions || [];
    var addressed = 0, partial = 0, notAddressed = 0, na = 0;
    questions.forEach(function(q) {
        if (q.status === 'Addressed') addressed++;
        else if (q.status === 'Partially Addressed') partial++;
        else if (q.status === 'Not Applicable') na++;
        else notAddressed++;
    });
    var applicable = questions.length - na;
    var coveragePct = applicable > 0 ? Math.round((addressed / applicable) * 100) : 0;

    var html = '';

    // Section header
    html += '<div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:12px;">SR 11-7 Validation Questions</div>';
    html += '<div style="font-size:11px;color:var(--text-3);margin-bottom:16px;">The nine fundamental questions from the Handbook of Model Risk Management (Chapter 5) that every model owner should be able to answer.</div>';

    // Summary cards
    html += '<div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">';
    var cards = [
        {label: 'Addressed', value: addressed, color: 'var(--green)'},
        {label: 'Partially', value: partial, color: 'var(--amber)'},
        {label: 'Not Addressed', value: notAddressed, color: 'var(--red)'},
        {label: 'N/A', value: na, color: 'var(--grey)'}
    ];
    cards.forEach(function(c) {
        html += '<div style="flex:1;min-width:90px;padding:8px 12px;border-radius:6px;background:var(--sunken);border-left:3px solid ' + c.color + ';">';
        html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;">' + c.label + '</div>';
        html += '<div style="font-size:18px;font-weight:700;color:' + c.color + ';">' + c.value + '</div>';
        html += '</div>';
    });
    html += '</div>';

    // Progress bar
    var barColor = coveragePct >= 75 ? 'var(--green)' : coveragePct >= 45 ? 'var(--amber)' : 'var(--red)';
    html += '<div style="margin-bottom:16px;">';
    html += '<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">';
    html += '<span style="color:var(--text-2);">Coverage</span>';
    html += '<span style="font-weight:600;color:' + barColor + ';">' + addressed + '/' + applicable + ' (' + coveragePct + '%)</span>';
    html += '</div>';
    html += '<div style="height:8px;background:var(--line);border-radius:4px;overflow:hidden;">';
    html += '<div style="height:100%;width:' + coveragePct + '%;background:' + barColor + ';border-radius:4px;transition:width 0.3s;"></div>';
    html += '</div></div>';

    // Questions table
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:var(--raised);">';
    html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--line-strong);width:30px;font-size:10px;color:var(--text-2);">#</th>';
    html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--line-strong);font-size:10px;color:var(--text-2);">Question</th>';
    html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--line-strong);font-size:10px;color:var(--text-2);width:130px;">Status</th>';
    html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--line-strong);font-size:10px;color:var(--text-2);width:100px;">Last Reviewed</th>';
    html += '<th style="padding:8px 10px;text-align:center;border-bottom:2px solid var(--line-strong);font-size:10px;color:var(--text-2);width:50px;"></th>';
    html += '</tr></thead><tbody>';

    questions.forEach(function(q) {
        var expanded = vqExpandedId === q.question_id;
        var rowBg = expanded ? 'background:var(--accent-soft);' : '';

        html += '<tr style="cursor:pointer;' + rowBg + '" onclick="window.MG.toggleVqQuestion(' + q.question_id + ')" onmouseenter="this.style.background=\'' + (expanded ? 'var(--accent-soft)' : 'var(--sunken)') + '\'" onmouseleave="this.style.background=\'' + (expanded ? 'var(--accent-soft)' : '') + '\'">';
        html += '<td style="padding:8px 10px;border-bottom:1px solid var(--code);font-weight:600;color:var(--accent);">' + q.question_id + '</td>';
        html += '<td style="padding:8px 10px;border-bottom:1px solid var(--code);">';
        html += '<div style="font-weight:600;color:var(--text);">' + q.short_label + '</div>';
        html += '<div style="font-size:10px;color:var(--muted);margin-top:2px;">' + q.question + '</div>';
        html += '</td>';
        html += '<td style="padding:8px 10px;border-bottom:1px solid var(--code);">' + vqStatusBadge(q.status) + '</td>';
        html += '<td style="padding:8px 10px;border-bottom:1px solid var(--code);font-size:10px;color:var(--text-3);">' + (q.last_reviewed || '\u2014') + '</td>';
        html += '<td style="padding:8px 10px;border-bottom:1px solid var(--code);text-align:center;">';
        html += '<button onclick="event.stopPropagation();window.MG.showVqEditForm(\'' + m.model_id + '\', ' + q.question_id + ')" style="padding:2px 8px;font-size:10px;border:1px solid var(--accent);border-radius:3px;cursor:pointer;background:var(--panel);color:var(--accent);">Edit</button>';
        html += '</td>';
        html += '</tr>';

        // Expanded detail row
        if (expanded) {
            html += '<tr><td colspan="5" style="padding:0;border-bottom:1px solid var(--code);">';
            html += '<div style="padding:12px 16px;background:var(--wash-cool);border-left:3px solid var(--accent);">';
            html += '<div style="display:flex;gap:24px;flex-wrap:wrap;">';

            html += '<div style="flex:2;min-width:200px;">';
            html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;">Evidence / Response</div>';
            html += '<div style="font-size:11px;color:var(--text);">' + (q.evidence || '<span style="color:var(--faint);font-style:italic;">No evidence provided yet</span>') + '</div>';
            html += '</div>';

            html += '<div style="flex:1;min-width:120px;">';
            html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;">Reviewed By</div>';
            html += '<div style="font-size:11px;color:var(--text);">' + (q.reviewed_by || '\u2014') + '</div>';
            html += '</div>';

            html += '<div style="flex:1;min-width:120px;">';
            html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;">Handbook Reference</div>';
            html += '<div style="font-size:11px;color:var(--accent);">' + (q.handbook_ref || '\u2014') + '</div>';
            html += '</div>';

            html += '</div></div>';
            html += '</td></tr>';
        }
    });

    html += '</tbody></table>';

    // Edit form area
    html += '<div id="vq-edit-area" style="margin-top:12px;"></div>';

    return html;
}

function toggleVqQuestion(questionId) {
    if (vqExpandedId === questionId) {
        vqExpandedId = null;
    } else {
        vqExpandedId = questionId;
    }
    var m = window._mgCurrentModel;
    var dc = document.getElementById('mg-detail-content');
    dc.innerHTML = renderValidationTab(m);
}

function showVqEditForm(modelId, questionId) {
    var m = window._mgCurrentModel;
    var q = (m.validation_questions || []).find(function(x) { return x.question_id === questionId; });
    if (!q) return;

    var area = document.getElementById('vq-edit-area');
    var html = '<div style="padding:16px;border:1px solid var(--line);border-radius:8px;background:var(--wash-cool);">';
    html += '<div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:12px;">Q' + q.question_id + ': ' + q.short_label + '</div>';
    html += '<div style="font-size:11px;color:var(--text-3);margin-bottom:12px;">' + q.question + '</div>';

    // Status dropdown
    html += '<div style="margin-bottom:10px;">';
    html += '<label style="font-size:10px;color:var(--muted);text-transform:uppercase;display:block;margin-bottom:3px;">Status</label>';
    html += '<select id="vq-ef-status" style="width:100%;padding:6px 8px;font-size:11px;border:1px solid var(--line-strong);border-radius:4px;">';
    ['Addressed', 'Partially Addressed', 'Not Addressed', 'Not Applicable'].forEach(function(s) {
        html += '<option value="' + s + '"' + (q.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div>';

    // Evidence textarea
    html += '<div style="margin-bottom:10px;">';
    html += '<label style="font-size:10px;color:var(--muted);text-transform:uppercase;display:block;margin-bottom:3px;">Evidence / Response</label>';
    html += '<textarea id="vq-ef-evidence" rows="4" style="width:100%;padding:6px 8px;font-size:11px;border:1px solid var(--line-strong);border-radius:4px;resize:vertical;box-sizing:border-box;">' + (q.evidence || '') + '</textarea>';
    html += '</div>';

    // Reviewed by
    html += '<div style="margin-bottom:12px;">';
    html += '<label style="font-size:10px;color:var(--muted);text-transform:uppercase;display:block;margin-bottom:3px;">Reviewed By</label>';
    html += '<input id="vq-ef-reviewer" type="text" value="' + (q.reviewed_by || 'David K Kelly') + '" style="width:100%;padding:6px 8px;font-size:11px;border:1px solid var(--line-strong);border-radius:4px;box-sizing:border-box;">';
    html += '</div>';

    // Buttons
    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.saveVqQuestion(\'' + modelId + '\', ' + questionId + ')" style="padding:6px 16px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:var(--accent);color:var(--inverse);">Save</button>';
    html += '<button onclick="document.getElementById(\'vq-edit-area\').innerHTML=\'\';" style="padding:6px 16px;font-size:11px;border:1px solid var(--line-strong);border-radius:4px;cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveVqQuestion(modelId, questionId) {
    var body = {
        status: document.getElementById('vq-ef-status').value,
        evidence: document.getElementById('vq-ef-evidence').value,
        reviewed_by: document.getElementById('vq-ef-reviewer').value.trim() || 'unknown'
    };

    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/validation-questions/' + questionId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mgCurrentModel = data.model;
            vqExpandedId = questionId;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderValidationTab(data.model);
        } else {
            alert(data.message || 'Failed to save');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

