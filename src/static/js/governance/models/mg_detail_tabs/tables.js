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

function renderRemediationTab(m) {
    var steps = m.remediation_steps || [];
    if (steps.length === 0) return '<div style="padding:var(--space-wide);text-align:center;color:var(--muted);">No remediation steps recorded</div>';

    var openCount = steps.filter(function(r) { return r.status === 'Open'; }).length;
    var closedCount = steps.filter(function(r) { return r.status === 'Closed'; }).length;

    var html = '<div style="padding:var(--space-6);">';

    // Summary bar
    html += '<div style="display:flex;gap:var(--space-8);margin-bottom:var(--space-6);">';
    html += '<div style="padding:var(--space-4) var(--space-7);border-radius:var(--radius-md);background:var(--warn-bg-warm);border-left:3px solid var(--amber);">';
    html += '<span style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">Open</span>';
    html += '<span style="font-size:var(--size-lg);font-weight:700;color:var(--amber-deep);margin-left:var(--space-4);">' + openCount + '</span></div>';
    html += '<div style="padding:var(--space-4) var(--space-7);border-radius:var(--radius-md);background:var(--ok-bg);border-left:3px solid var(--green);">';
    html += '<span style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">Closed</span>';
    html += '<span style="font-size:var(--size-lg);font-weight:700;color:var(--green);margin-left:var(--space-4);">' + closedCount + '</span></div>';
    html += '<div style="padding:var(--space-4) var(--space-7);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid var(--text-3);">';
    html += '<span style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">Total</span>';
    html += '<span style="font-size:var(--size-lg);font-weight:700;color:var(--text);margin-left:var(--space-4);">' + steps.length + '</span></div>';
    html += '</div>';

    // Table
    html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['ID', 'Description', 'Owner', 'Priority', 'Due Date', 'Status'].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    var priorityColors = Theme.ramp('priority');
    var statusColors = Theme.ramp('task_status');

    steps.forEach(function(r) {
        var isOverdue = r.status === 'Open' && r.due_date && new Date(r.due_date) < new Date();
        var rowStyle = isOverdue ? 'background:var(--warn-bg);' : '';
        html += '<tr style="' + rowStyle + '">';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;white-space:nowrap;">' + r.id + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + r.description + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + r.owner + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(r.priority, priorityColors[r.priority] || 'var(--muted-2)') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + (r.due_date || '\u2014') + (isOverdue ? ' <span style="color:var(--red);font-size:var(--size-xxs);font-weight:600;">OVERDUE</span>' : '') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(r.status, statusColors[r.status] || 'var(--muted-2)') + '</td>';
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    return html;
}

function renderLimitationsTab(m) {
    var lims = m.limitations || [];
    if (lims.length === 0) return '<div style="padding:var(--space-wide);text-align:center;color:var(--muted);">No limitations documented</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['ID', 'Description', 'Impact', 'Monitoring Trigger', 'Compensating Control'].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    lims.forEach(function(l) {
        var impactColor = l.impact === 'High' ? 'var(--red)' : l.impact === 'Medium' ? 'var(--amber)' : 'var(--green)';
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;white-space:nowrap;">' + l.id + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + l.description + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(l.impact, impactColor) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--text-3);">' + (l.monitoring_trigger || '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--text);">' + (l.compensating_control || '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderAssumptionsTab(m) {
    var assumptions = m.assumptions || [];
    if (assumptions.length === 0) return '<div style="padding:var(--space-wide);text-align:center;color:var(--muted);">No assumptions documented</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['ID', 'Assumption', 'Impact', 'Monitoring', 'Mitigation'].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    assumptions.forEach(function(a) {
        var impactColor = a.impact === 'High' ? 'var(--red)' : a.impact === 'Medium' ? 'var(--amber)' : 'var(--green)';
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;white-space:nowrap;">' + a.id + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + a.description + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(a.impact, impactColor) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--text-3);">' + (a.monitoring || '\u2014') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--text);">' + (a.mitigation || '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderChangesTab(m) {
    var changes = m.change_history || [];
    if (changes.length === 0) return '<div style="padding:var(--space-wide);text-align:center;color:var(--muted);">No change history</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['Version', 'Date', 'Author', 'Type', 'Description'].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    changes.forEach(function(c) {
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;">' + c.version + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + c.date + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + c.author + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(c.type, 'var(--accent)') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + c.description + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function renderAuditTab(entries) {
    if (!entries || entries.length === 0) return '<div style="padding:var(--space-wide);text-align:center;color:var(--muted);">No audit entries for this model</div>';

    var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['Timestamp', 'Event', 'User', 'Action', 'Source'].forEach(function(h) {
        html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    entries.slice().reverse().forEach(function(e) {
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;font-size:var(--size-xxs);">' + e.timestamp + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(e.event_type, 'var(--accent)') + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + e.user + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + e.action + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + e.source + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}
