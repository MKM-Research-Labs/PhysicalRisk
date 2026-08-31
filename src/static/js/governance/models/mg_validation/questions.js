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
    return '<span style="display:inline-block;padding:var(--space-1) var(--space-4);border-radius:var(--radius-xl);font-size:var(--size-xxs);font-weight:700;color:var(--inverse);background:' + c + ';">' + (status || 'Not Addressed') + '</span>';
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
    html += '<div style="font-size:var(--size-md);font-weight:700;color:var(--text);margin-bottom:var(--space-6);">SR 11-7 Validation Questions</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--text-3);margin-bottom:var(--space-8);">The nine fundamental questions from the Handbook of Model Risk Management (Chapter 5) that every model owner should be able to answer.</div>';

    // Summary cards
    html += '<div style="display:flex;gap:var(--space-5);margin-bottom:var(--space-8);flex-wrap:wrap;">';
    var cards = [
        {label: 'Addressed', value: addressed, color: 'var(--green)'},
        {label: 'Partially', value: partial, color: 'var(--amber)'},
        {label: 'Not Addressed', value: notAddressed, color: 'var(--red)'},
        {label: 'N/A', value: na, color: 'var(--grey)'}
    ];
    cards.forEach(function(c) {
        html += '<div style="flex:1;min-width:90px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + c.color + ';">';
        html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">' + c.label + '</div>';
        html += '<div style="font-size:var(--size-18);font-weight:700;color:' + c.color + ';">' + c.value + '</div>';
        html += '</div>';
    });
    html += '</div>';

    // Progress bar
    var barColor = coveragePct >= 75 ? 'var(--green)' : coveragePct >= 45 ? 'var(--amber)' : 'var(--red)';
    html += '<div style="margin-bottom:var(--space-8);">';
    html += '<div style="display:flex;justify-content:space-between;font-size:var(--size-xs);margin-bottom:var(--space-2);">';
    html += '<span style="color:var(--text-2);">Coverage</span>';
    html += '<span style="font-weight:600;color:' + barColor + ';">' + addressed + '/' + applicable + ' (' + coveragePct + '%)</span>';
    html += '</div>';
    html += '<div style="height:8px;background:var(--line);border-radius:var(--radius-4);overflow:hidden;">';
    html += '<div style="height:100%;width:' + coveragePct + '%;background:' + barColor + ';border-radius:var(--radius-4);transition:width 0.3s;"></div>';
    html += '</div></div>';

    // Questions table
    html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);width:30px;font-size:var(--size-xxs);color:var(--text-2);">#</th>';
    html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">Question</th>';
    html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);width:130px;">Status</th>';
    html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);width:100px;">Last Reviewed</th>';
    html += '<th style="padding:var(--space-4) var(--space-5);text-align:center;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);width:50px;"></th>';
    html += '</tr></thead><tbody>';

    questions.forEach(function(q) {
        var expanded = vqExpandedId === q.question_id;
        var rowBg = expanded ? 'background:var(--accent-soft);' : '';

        html += '<tr style="cursor:pointer;' + rowBg + '" onclick="window.MG.toggleVqQuestion(' + q.question_id + ')" onmouseenter="this.style.background=\'' + (expanded ? 'var(--accent-soft)' : 'var(--sunken)') + '\'" onmouseleave="this.style.background=\'' + (expanded ? 'var(--accent-soft)' : '') + '\'">';
        html += '<td style="padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;color:var(--accent);">' + q.question_id + '</td>';
        html += '<td style="padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--code);">';
        html += '<div style="font-weight:600;color:var(--text);">' + q.short_label + '</div>';
        html += '<div style="font-size:var(--size-xxs);color:var(--muted);margin-top:var(--space-1);">' + q.question + '</div>';
        html += '</td>';
        html += '<td style="padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--code);">' + vqStatusBadge(q.status) + '</td>';
        html += '<td style="padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--text-3);">' + (q.last_reviewed || '\u2014') + '</td>';
        html += '<td style="padding:var(--space-4) var(--space-5);border-bottom:1px solid var(--code);text-align:center;">';
        html += '<button onclick="event.stopPropagation();window.MG.showVqEditForm(\'' + m.model_id + '\', ' + q.question_id + ')" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);border:1px solid var(--accent);border-radius:var(--radius-sm);cursor:pointer;background:var(--panel);color:var(--accent);">Edit</button>';
        html += '</td>';
        html += '</tr>';

        // Expanded detail row
        if (expanded) {
            html += '<tr><td colspan="5" style="padding:0;border-bottom:1px solid var(--code);">';
            html += '<div style="padding:var(--space-6) var(--space-8);background:var(--wash-cool);border-left:3px solid var(--accent);">';
            html += '<div style="display:flex;gap:var(--space-10);flex-wrap:wrap;">';

            html += '<div style="flex:2;min-width:200px;">';
            html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;margin-bottom:var(--space-2);">Evidence / Response</div>';
            html += '<div style="font-size:var(--size-xs);color:var(--text);">' + (q.evidence || '<span style="color:var(--faint);font-style:italic;">No evidence provided yet</span>') + '</div>';
            html += '</div>';

            html += '<div style="flex:1;min-width:120px;">';
            html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;margin-bottom:var(--space-2);">Reviewed By</div>';
            html += '<div style="font-size:var(--size-xs);color:var(--text);">' + (q.reviewed_by || '\u2014') + '</div>';
            html += '</div>';

            html += '<div style="flex:1;min-width:120px;">';
            html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;margin-bottom:var(--space-2);">Handbook Reference</div>';
            html += '<div style="font-size:var(--size-xs);color:var(--accent);">' + (q.handbook_ref || '\u2014') + '</div>';
            html += '</div>';

            html += '</div></div>';
            html += '</td></tr>';
        }
    });

    html += '</tbody></table>';

    // Edit form area
    html += '<div id="vq-edit-area" style="margin-top:var(--space-6);"></div>';

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
    var html = '<div style="padding:var(--space-8);border:1px solid var(--line);border-radius:var(--radius-lg);background:var(--wash-cool);">';
    html += '<div style="font-size:var(--size-sm);font-weight:600;color:var(--text);margin-bottom:var(--space-6);">Q' + q.question_id + ': ' + q.short_label + '</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--text-3);margin-bottom:var(--space-6);">' + q.question + '</div>';

    // Status dropdown
    html += '<div style="margin-bottom:var(--space-5);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;display:block;margin-bottom:var(--space-2);">Status</label>';
    html += '<select id="vq-ef-status" style="width:100%;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    ['Addressed', 'Partially Addressed', 'Not Addressed', 'Not Applicable'].forEach(function(s) {
        html += '<option value="' + s + '"' + (q.status === s ? ' selected' : '') + '>' + s + '</option>';
    });
    html += '</select></div>';

    // Evidence textarea
    html += '<div style="margin-bottom:var(--space-5);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;display:block;margin-bottom:var(--space-2);">Evidence / Response</label>';
    html += '<textarea id="vq-ef-evidence" rows="4" style="width:100%;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;">' + (q.evidence || '') + '</textarea>';
    html += '</div>';

    // Reviewed by
    html += '<div style="margin-bottom:var(--space-6);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;display:block;margin-bottom:var(--space-2);">Reviewed By</label>';
    html += '<input id="vq-ef-reviewer" type="text" value="' + (q.reviewed_by || 'David K Kelly') + '" style="width:100%;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;">';
    html += '</div>';

    // Buttons
    html += '<div style="display:flex;gap:var(--space-4);">';
    html += '<button onclick="window.MG.saveVqQuestion(\'' + modelId + '\', ' + questionId + ')" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);">Save</button>';
    html += '<button onclick="document.getElementById(\'vq-edit-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
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

