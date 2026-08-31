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

function renderParameterInventory() {
    var content = document.getElementById('mg-content');
    var pdfUrl = getBaseUrl() + '/api/v1/governance/parameter-inventory/pdf';

    var html = '<div style="padding:var(--space-8);">';
    html += '<div style="font-size:var(--size-md);font-weight:700;color:var(--text);margin-bottom:var(--space-4);">Model Parameter Inventory</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--text-3);margin-bottom:var(--space-8);">Complete inventory of all hard-coded input parameters across the analytical model codebase. Maintained for model governance and MRC review.</div>';

    // Action bar
    html += '<div style="display:flex;gap:var(--space-5);margin-bottom:var(--space-8);">';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:var(--space-3);padding:var(--space-4) var(--space-8);background:var(--accent);color:var(--inverse);border-radius:var(--radius-4);text-decoration:none;font-size:var(--size-sm);font-weight:500;">&#x2913; Download PDF</a>';
    html += '</div>';

    // Embedded PDF viewer
    html += '<div id="mg-params-pdf-container" style="border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="600" style="border:none;">';
    html += '<div style="padding:var(--space-inset);text-align:center;">';
    html += '<div style="font-size:var(--size-32);margin-bottom:var(--space-6);">&#x1F4CB;</div>';
    html += '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">Parameter Inventory PDF</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--muted);margin-bottom:var(--space-8);">Your browser cannot display the PDF inline.</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-block;padding:var(--space-4) var(--space-wide);background:var(--accent);color:var(--inverse);border-radius:var(--radius-4);text-decoration:none;font-size:var(--size-sm);">Open PDF</a>';
    html += '</div>';
    html += '</object>';
    html += '</div>';

    html += '</div>';
    content.innerHTML = html;

    // Check if PDF exists
    fetch(pdfUrl, {method: 'HEAD'}).then(function(resp) {
        if (!resp.ok) {
            var container = document.getElementById('mg-params-pdf-container');
            if (container) {
                container.innerHTML = '<div style="padding:var(--space-inset);text-align:center;">' +
                    '<div style="font-size:var(--size-32);margin-bottom:var(--space-6);">&#x26A0;</div>' +
                    '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">No Parameter Inventory Available</div>' +
                    '<div style="font-size:var(--size-xs);color:var(--muted);">Run: <code style="background:var(--sunken);padding:var(--space-1) var(--space-3);border-radius:var(--radius-sm);">python phys.py check params --pdf</code></div>' +
                    '</div>';
            }
        }
    });
}


// ================================================================
// MRC — Main view with sub-tabs
// ================================================================
var mrcSubTab = 'meetings';

function renderMRC() {
    console.log('[MRC] Rendering MRC view');
    var content = document.getElementById('mg-content');

    var html = '<div style="padding:0;">';

    // Members summary bar
    html += '<div style="display:flex;gap:var(--space-5);padding:var(--space-6) var(--space-8);border-bottom:1px solid var(--line-soft);flex-wrap:wrap;">';
    html += '<div style="flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid var(--accent);">';
    html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Chair</div>';
    html += '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);">Johnny Mattimore</div></div>';
    html += '<div style="flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid var(--green);">';
    html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Model Owner</div>';
    html += '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);">David K Kelly</div></div>';
    html += '<div style="flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid var(--amber);">';
    html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Frequency</div>';
    html += '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);">Quarterly</div></div>';
    html += '</div>';

    // Sub-tabs
    html += '<div style="display:flex;border-bottom:1px solid var(--line-soft);background:var(--raised);">';
    var subTabs = [
        {id: 'meetings', label: 'Meetings'},
        {id: 'tor', label: 'Terms of Reference'},
    ];
    subTabs.forEach(function(t) {
        html += '<button id="mrc-stab-' + t.id + '" onclick="window.MG.switchMrcTab(\'' + t.id + '\')" style="padding:var(--space-4) var(--space-7);font-size:var(--size-xs);border:none;cursor:pointer;border-bottom:2px solid ' + (t.id === mrcSubTab ? 'var(--accent)' : 'transparent') + ';background:transparent;color:' + (t.id === mrcSubTab ? 'var(--accent)' : 'var(--text-3)') + ';font-weight:' + (t.id === mrcSubTab ? '600' : '400') + ';">' + t.label + '</button>';
    });
    html += '</div>';

    html += '<div id="mrc-sub-content" style="padding:0;"></div>';
    html += '</div>';

    content.innerHTML = html;

    // Render active sub-tab
    if (mrcSubTab === 'meetings') renderMrcMeetingsList();
    else if (mrcSubTab === 'tor') renderMrcToR();
}

function switchMrcSubTab(tabId) {
    mrcSubTab = tabId;
    ['meetings', 'tor'].forEach(function(t) {
        var btn = document.getElementById('mrc-stab-' + t);
        if (btn) {
            btn.style.borderBottomColor = t === tabId ? 'var(--accent)' : 'transparent';
            btn.style.color = t === tabId ? 'var(--accent)' : 'var(--text-3)';
            btn.style.fontWeight = t === tabId ? '600' : '400';
        }
    });
    if (tabId === 'meetings') renderMrcMeetingsList();
    else if (tabId === 'tor') renderMrcToR();
}

function renderMrcToR() {
    var sc = document.getElementById('mrc-sub-content');
    var pdfUrl = getBaseUrl() + '/api/v1/governance/mrc/terms-of-reference/pdf';

    var html = '<div style="padding:var(--space-8);">';
    html += '<div style="display:flex;gap:var(--space-5);margin-bottom:var(--space-8);">';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:var(--space-3);padding:var(--space-4) var(--space-8);background:var(--accent);color:var(--inverse);border-radius:var(--radius-4);text-decoration:none;font-size:var(--size-sm);font-weight:500;">&#x2913; Download Terms of Reference</a>';
    html += '</div>';
    html += '<div id="mrc-tor-pdf-container" style="border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="550" style="border:none;">';
    html += '<div style="padding:var(--space-inset);text-align:center;"><a href="' + pdfUrl + '" target="_blank" style="padding:var(--space-4) var(--space-wide);background:var(--accent);color:var(--inverse);border-radius:var(--radius-4);text-decoration:none;font-size:var(--size-sm);">Open PDF</a></div>';
    html += '</object></div></div>';
    sc.innerHTML = html;

    fetch(pdfUrl, {method: 'HEAD'}).then(function(resp) {
        if (!resp.ok) {
            var c = document.getElementById('mrc-tor-pdf-container');
            if (c) c.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">ToR PDF not generated. Run: <code>python -m docs.models.mrc_tor.generator --pdf</code></div>';
        }
    });
}

// ================================================================
// MRC Meetings list
// ================================================================
function renderMrcMeetingsList() {
    var sc = document.getElementById('mrc-sub-content');
    sc.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">Loading meetings...</div>';

    console.log('[MRC] Fetching meetings list');
    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                sc.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Failed to load meetings</div>';
                return;
            }
            var meetings = data.meetings;
            console.log('[MRC] Loaded', meetings.length, 'meetings');
            var html = '<div style="padding:var(--space-8);">';

            // Action bar
            html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-8);">';
            html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + meetings.length + ' meeting' + (meetings.length !== 1 ? 's' : '') + '</div>';
            html += '<button onclick="window.MG.showNewMeetingForm()" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">+ New Meeting</button>';
            html += '</div>';

            if (meetings.length === 0) {
                html += '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);font-size:var(--size-sm);">No meetings recorded yet.</div>';
            } else {
                html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
                html += '<thead><tr style="background:var(--raised);">';
                ['Date', 'Title', 'Status', 'Chair', 'Models', 'Agenda', 'Minutes', 'Docs'].forEach(function(h) {
                    html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
                });
                html += '</tr></thead><tbody>';

                meetings.forEach(function(m) {
                    var statusColor = m.status === 'Completed' ? 'var(--green)' : m.status === 'Scheduled' ? 'var(--accent)' : 'var(--amber)';
                    html += '<tr style="cursor:pointer;" onmouseenter="this.style.background=\'var(--sunken)\'" onmouseleave="this.style.background=\'\'" onclick="window.MG.showMeeting(\'' + m.id + '\')">';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;white-space:nowrap;">' + m.date + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);color:var(--accent);font-weight:500;">' + m.title + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + badge(m.status, statusColor) + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + m.chair + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);text-align:center;">' + m.models_in_scope + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);text-align:center;">' + m.agenda_items + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);text-align:center;">' + (m.has_minutes ? '<span style="color:var(--green);">&#x2713;</span>' : '<span style="color:var(--divider);">—</span>') + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);text-align:center;">' + m.documents + '</td>';
                    html += '</tr>';
                });

                html += '</tbody></table>';
            }

            html += '</div>';
            sc.innerHTML = html;
        })
        .catch(function(err) {
            sc.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Error: ' + err.message + '</div>';
        });
}

// ================================================================

