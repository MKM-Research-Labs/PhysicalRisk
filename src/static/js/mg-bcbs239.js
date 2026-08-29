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

var bcbs239Data = null;
var bcbs239ExpandedId = null;

function renderBCBS239() {
    var content = document.getElementById('mg-content');
    // Use overflow:hidden on content since inner flex layout handles its own scroll
    content.style.overflowY = 'hidden';
    content.innerHTML = '<div style="padding:40px;text-align:center;color:var(--muted);">Loading BCBS 239 assessment...</div>';

    console.log('[BCBS239] Fetching assessment data');
    fetch(getBaseUrl() + '/api/v1/governance/bcbs239', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:var(--red);">Assessment not found</div>';
                return;
            }
            bcbs239Data = data.assessment;
            var p = data.assessment.principles || [];
            var total = 0; var max = 0;
            p.forEach(function(pr) { total += pr.score; max += pr.max_score; });
            console.log('[BCBS239] Loaded', p.length, 'principles, score', total + '/' + max, '(' + Math.round(total/max*100) + '%)');
            renderBCBS239Dashboard(data.assessment);
        })
        .catch(function(err) {
            console.error('[BCBS239] Load error:', err);
            content.innerHTML = '<div style="padding:40px;text-align:center;color:var(--red);">Error: ' + err.message + '</div>';
        });
}

function bcbs239ScoreColor(score) {
    if (score === 4) return 'var(--green)';
    if (score === 3) return 'var(--accent)';
    if (score === 2) return 'var(--amber)';
    return 'var(--red)';
}

function bcbs239StatusLabel(score) {
    if (score === 4) return 'Fully Compliant';
    if (score === 3) return 'Largely Compliant';
    if (score === 2) return 'Materially Non-compliant';
    return 'Non-compliant';
}

function renderBCBS239Dashboard(a) {
    var content = document.getElementById('mg-content');
    var principles = a.principles || [];

    // Category aggregation
    var categories = [
        {name: 'Governance & Infrastructure', ids: [1, 2], color: 'var(--accent-mid)'},
        {name: 'Risk Data Aggregation', ids: [3, 4, 5, 6], color: 'var(--peril-wind)'},
        {name: 'Risk Reporting Practices', ids: [7, 8, 9, 10, 11], color: 'var(--product-ink)'},
        {name: 'Supervisory Review', ids: [12, 13, 14], color: 'var(--red-dark)'},
    ];

    var totalScore = 0;
    var totalMax = 0;
    principles.forEach(function(p) { totalScore += p.score; totalMax += p.max_score; });
    var pct = totalMax > 0 ? Math.round(totalScore / totalMax * 100) : 0;

    // Use a flex column layout: summary (fixed) + scrollable table
    var html = '<div style="display:flex;flex-direction:column;height:100%;">';
    html += '<div style="padding:16px;flex-shrink:0;">';

    // Header row
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">';
    html += '<div>';
    html += '<div style="font-size:15px;font-weight:700;color:var(--text);">BCBS 239 Self-Assessment</div>';
    html += '<div style="font-size:11px;color:var(--muted);">Principles for Effective Risk Data Aggregation and Risk Reporting</div>';
    html += '</div>';
    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.downloadBcbs239Pdf()" style="padding:5px 12px;font-size:11px;border:1px solid var(--accent);border-radius:4px;cursor:pointer;background:var(--accent-soft);color:var(--accent);font-weight:500;">&#x2913; Self-Assessment PDF</button>';
    html += '</div>';
    html += '</div>';

    // Assessment metadata + overall score
    html += '<div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">';

    // Overall compliance bar
    html += '<div style="flex:2;min-width:200px;padding:12px 16px;border-radius:6px;background:var(--sunken);border:1px solid var(--line);">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">';
    html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">Overall Compliance</div>';
    html += '<div style="font-size:18px;font-weight:700;color:' + bcbs239ScoreColor(Math.round(totalScore / principles.length)) + ';">' + pct + '%</div>';
    html += '</div>';
    html += '<div style="height:8px;background:var(--line);border-radius:4px;overflow:hidden;">';
    html += '<div style="height:100%;width:' + pct + '%;background:' + bcbs239ScoreColor(Math.round(totalScore / principles.length)) + ';border-radius:4px;transition:width 0.3s;"></div>';
    html += '</div>';
    html += '<div style="display:flex;justify-content:space-between;margin-top:6px;font-size:10px;color:var(--muted);">';
    html += '<span>' + totalScore + ' / ' + totalMax + ' points</span>';
    html += '<span>' + a.assessment_date + '</span>';
    html += '</div>';
    html += '</div>';

    // Metadata card
    html += '<div style="flex:1;min-width:150px;padding:12px 16px;border-radius:6px;background:var(--sunken);border:1px solid var(--line);">';
    html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Assessment</div>';
    html += '<div style="font-size:11px;color:var(--text);margin-bottom:2px;">Assessor: <b>' + a.assessor + '</b></div>';
    html += '<div style="font-size:11px;color:var(--text);margin-bottom:2px;">Version: <b>' + a.version + '</b></div>';
    html += '<div style="font-size:11px;color:var(--text);">Status: ' + badge(a.overall_status, 'var(--accent)') + '</div>';
    html += '</div>';
    html += '</div>';

    // Category cards
    html += '<div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:10px;margin-bottom:16px;">';
    categories.forEach(function(cat) {
        var catScore = 0;
        var catMax = 0;
        var catPrinciples = [];
        principles.forEach(function(p) {
            if (cat.ids.indexOf(p.id) !== -1) {
                catScore += p.score;
                catMax += p.max_score;
                catPrinciples.push(p);
            }
        });
        var catPct = catMax > 0 ? Math.round(catScore / catMax * 100) : 0;
        var avgScore = catPrinciples.length > 0 ? Math.round(catScore / catPrinciples.length) : 0;

        html += '<div style="padding:10px 14px;border-radius:6px;background:var(--panel);border:1px solid var(--line);border-top:3px solid ' + cat.color + ';">';
        html += '<div style="font-size:10px;font-weight:600;color:' + cat.color + ';margin-bottom:6px;">' + cat.name + '</div>';
        html += '<div style="display:flex;align-items:baseline;gap:4px;margin-bottom:4px;">';
        html += '<span style="font-size:20px;font-weight:700;color:' + bcbs239ScoreColor(avgScore) + ';">' + catPct + '%</span>';
        html += '<span style="font-size:10px;color:var(--muted);">' + catScore + '/' + catMax + '</span>';
        html += '</div>';
        html += '<div style="height:4px;background:var(--line);border-radius:2px;overflow:hidden;">';
        html += '<div style="height:100%;width:' + catPct + '%;background:' + cat.color + ';border-radius:2px;"></div>';
        html += '</div>';
        html += '</div>';
    });
    html += '</div>';
    // Close the summary section
    html += '</div>';

    // Scrollable principle table area
    html += '<div style="flex:1;overflow-y:auto;padding:0 16px 16px 16px;min-height:0;">';
    html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:var(--raised);position:sticky;top:0;z-index:1;">';
    ['#', 'Principle', 'Category', 'Score', 'Status', ''].forEach(function(h) {
        html += '<th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--line-strong);font-size:10px;color:var(--text-2);background:var(--raised);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';

    principles.forEach(function(p) {
        var sc = bcbs239ScoreColor(p.score);
        var isExpanded = bcbs239ExpandedId === p.id;

        html += '<tr style="cursor:pointer;" onmouseenter="this.style.background=\'var(--sunken)\'" onmouseleave="this.style.background=\'\'" onclick="window.MG.toggleBcbs239Principle(' + p.id + ')">';
        html += '<td style="padding:6px 10px;border-bottom:1px solid var(--code);font-weight:600;width:30px;color:var(--accent);">' + p.id + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid var(--code);font-weight:600;color:var(--text);">' + p.title + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid var(--code);font-size:10px;color:var(--muted);">' + p.category + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid var(--code);">';
        html += '<div style="display:flex;align-items:center;gap:4px;">';
        for (var s = 1; s <= 4; s++) {
            html += '<div style="width:10px;height:10px;border-radius:50%;background:' + (s <= p.score ? sc : 'var(--line)') + ';"></div>';
        }
        html += '<span style="font-size:10px;font-weight:600;color:' + sc + ';margin-left:4px;">' + p.score + '/4</span>';
        html += '</div></td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid var(--code);">' + badge(p.status, sc) + '</td>';
        html += '<td style="padding:6px 10px;border-bottom:1px solid var(--code);white-space:nowrap;">';
        html += '<button onclick="event.stopPropagation();window.MG.showBcbs239EditForm(' + p.id + ')" style="padding:2px 8px;font-size:10px;border:1px solid var(--accent);border-radius:3px;cursor:pointer;background:var(--panel);color:var(--accent);">Edit</button>';
        html += '</td>';
        html += '</tr>';

        // Expanded detail row
        if (isExpanded) {
            html += '<tr><td colspan="6" style="padding:0;border-bottom:1px solid var(--line);">';
            html += '<div style="padding:12px 16px;background:var(--wash-cool);border-left:3px solid var(--accent);">';

            html += '<div style="font-size:10px;color:var(--muted);margin-bottom:4px;">DESCRIPTION</div>';
            html += '<div style="font-size:11px;color:var(--text);margin-bottom:10px;line-height:1.5;">' + p.description + '</div>';

            html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';

            html += '<div>';
            html += '<div style="font-size:10px;color:var(--green);font-weight:600;margin-bottom:3px;">EVIDENCE</div>';
            html += '<div style="font-size:11px;color:var(--text);line-height:1.5;">' + (p.evidence || '\u2014') + '</div>';
            html += '</div>';

            html += '<div>';
            html += '<div style="font-size:10px;color:var(--red);font-weight:600;margin-bottom:3px;">GAPS</div>';
            html += '<div style="font-size:11px;color:var(--text);line-height:1.5;">' + (p.gaps || '\u2014') + '</div>';
            html += '</div>';

            html += '</div>';

            html += '<div style="margin-top:10px;display:grid;grid-template-columns:1fr auto;gap:12px;">';
            html += '<div>';
            html += '<div style="font-size:10px;color:var(--amber);font-weight:600;margin-bottom:3px;">REMEDIATION</div>';
            html += '<div style="font-size:11px;color:var(--text);line-height:1.5;">' + (p.remediation || '\u2014') + '</div>';
            html += '</div>';
            html += '<div>';
            html += '<div style="font-size:10px;color:var(--muted);font-weight:600;margin-bottom:3px;">TARGET DATE</div>';
            html += '<div style="font-size:11px;font-weight:600;color:var(--text);">' + (p.target_date || '\u2014') + '</div>';
            html += '</div>';
            html += '</div>';

            html += '</div>';
            html += '</td></tr>';
        }
    });

    html += '</tbody></table>';

    // Edit form area
    html += '<div id="bcbs239-edit-area"></div>';

    // Close scrollable table area
    html += '</div>';
    // Close outer flex column
    html += '</div>';
    content.innerHTML = html;
}

function toggleBcbs239Principle(id) {
    if (bcbs239ExpandedId === id) {
        bcbs239ExpandedId = null;
    } else {
        bcbs239ExpandedId = id;
    }
    renderBCBS239Dashboard(bcbs239Data);
}

function showBcbs239EditForm(principleId) {
    var area = document.getElementById('bcbs239-edit-area');
    if (!area) return;
    var p = null;
    (bcbs239Data.principles || []).forEach(function(pr) {
        if (pr.id === principleId) p = pr;
    });
    if (!p) return;

    var html = '<div style="padding:16px;border:1px solid var(--line);border-radius:6px;background:var(--wash-cool);margin-top:16px;">';
    html += '<div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:10px;">Edit Principle ' + p.id + ': ' + p.title + '</div>';

    html += '<div style="display:grid;grid-template-columns:auto 1fr;gap:8px;margin-bottom:10px;">';
    html += '<div><label style="font-size:10px;color:var(--text-3);display:block;margin-bottom:2px;">Score</label>';
    html += '<select id="bcbs239-ef-score" style="font-size:11px;padding:5px 8px;border:1px solid var(--line-strong);border-radius:4px;">';
    [1, 2, 3, 4].forEach(function(s) {
        var label = s === 4 ? '4 - Fully Compliant' : s === 3 ? '3 - Largely Compliant' : s === 2 ? '2 - Materially Non-compliant' : '1 - Non-compliant';
        html += '<option value="' + s + '"' + (p.score === s ? ' selected' : '') + '>' + label + '</option>';
    });
    html += '</select></div>';
    html += '<div><label style="font-size:10px;color:var(--text-3);display:block;margin-bottom:2px;">Target Date</label>';
    html += '<input type="date" id="bcbs239-ef-date" value="' + (p.target_date || '') + '" style="font-size:11px;padding:5px 8px;border:1px solid var(--line-strong);border-radius:4px;"></div>';
    html += '</div>';

    html += '<div style="margin-bottom:8px;"><label style="font-size:10px;color:var(--text-3);display:block;margin-bottom:2px;">Evidence</label>';
    html += '<textarea id="bcbs239-ef-evidence" rows="3" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid var(--line-strong);border-radius:4px;resize:vertical;box-sizing:border-box;line-height:1.5;">' + (p.evidence || '') + '</textarea></div>';

    html += '<div style="margin-bottom:8px;"><label style="font-size:10px;color:var(--text-3);display:block;margin-bottom:2px;">Gaps</label>';
    html += '<textarea id="bcbs239-ef-gaps" rows="2" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid var(--line-strong);border-radius:4px;resize:vertical;box-sizing:border-box;line-height:1.5;">' + (p.gaps || '') + '</textarea></div>';

    html += '<div style="margin-bottom:10px;"><label style="font-size:10px;color:var(--text-3);display:block;margin-bottom:2px;">Remediation</label>';
    html += '<textarea id="bcbs239-ef-remediation" rows="2" style="width:100%;font-size:11px;padding:5px 8px;border:1px solid var(--line-strong);border-radius:4px;resize:vertical;box-sizing:border-box;line-height:1.5;">' + (p.remediation || '') + '</textarea></div>';

    html += '<div style="display:flex;gap:8px;">';
    html += '<button onclick="window.MG.saveBcbs239Principle(' + principleId + ')" style="padding:5px 14px;font-size:11px;border:none;border-radius:4px;cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;">Save</button>';
    html += '<button onclick="document.getElementById(\'bcbs239-edit-area\').innerHTML=\'\';" style="padding:5px 14px;font-size:11px;border:1px solid var(--divider);border-radius:4px;cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveBcbs239Principle(principleId) {
    console.log('[BCBS239] Saving principle', principleId);
    var body = {
        score: parseInt(document.getElementById('bcbs239-ef-score').value),
        evidence: document.getElementById('bcbs239-ef-evidence').value,
        gaps: document.getElementById('bcbs239-ef-gaps').value,
        remediation: document.getElementById('bcbs239-ef-remediation').value,
        target_date: document.getElementById('bcbs239-ef-date').value,
    };

    fetch(getBaseUrl() + '/api/v1/governance/bcbs239/principles/' + principleId + '/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            console.log('[BCBS239] Principle', principleId, 'saved successfully');
            bcbs239Data = data.assessment;
            bcbs239ExpandedId = principleId;
            renderBCBS239Dashboard(data.assessment);
        } else {
            alert(data.message || 'Save failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function downloadBcbs239Pdf() {
    console.log('[BCBS239] Downloading self-assessment PDF');
    window.open(getBaseUrl() + '/api/v1/governance/bcbs239/pdf', '_blank');
}

