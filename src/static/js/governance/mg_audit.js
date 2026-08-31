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

function renderAuditTrail() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">Loading audit trail...</div>';

    console.log('[AuditTrail] Fetching audit entries');
    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/audit-trail?limit=200', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Error loading audit trail</div>';
                return;
            }
            console.log('[AuditTrail] Loaded', data.returned, 'of', data.total_entries, 'entries');

            if (data.entries.length === 0) {
                content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">' +
                    '<div style="font-size:var(--size-14);font-weight:600;margin-bottom:var(--space-4);">No Audit Entries Yet</div>' +
                    '<div style="font-size:var(--size-sm);">Model usage events will appear here as models are invoked through the platform.</div>' +
                    '</div>';
                return;
            }

            var html = '<div style="padding:var(--space-6) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--sunken);">';
            html += '<span style="font-size:var(--size-xs);color:var(--text-3);">Showing <b>' + data.returned + '</b> of <b>' + data.total_entries + '</b> entries</span>';
            html += '</div>';

            html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
            html += '<thead><tr style="background:var(--raised);">';
            ['Timestamp', 'Model', 'Event', 'User', 'Action', 'Source'].forEach(function(h) {
                html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);position:sticky;top:0;background:var(--raised);">' + h + '</th>';
            });
            html += '</tr></thead><tbody>';

            data.entries.forEach(function(e) {
                html += '<tr>';
                html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;font-size:var(--size-xxs);">' + e.timestamp + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;color:var(--accent);cursor:pointer;" onclick="window.MG.showDetail(\'' + e.model_id + '\')">' + e.model_id + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(e.event_type, 'var(--accent)') + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + e.user + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + e.action + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + e.source + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';

            content.innerHTML = html;

            document.getElementById('mg-stats-bar').innerHTML =
                '<span>Total audit entries: <b>' + data.total_entries + '</b></span>' +
                '<span>Showing: <b>' + data.returned + '</b></span>';
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Failed to load audit trail</div>';
            console.error('Audit trail error:', err);
        });
}

// ================================================================
// Show / Hide

