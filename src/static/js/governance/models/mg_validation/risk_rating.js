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

var riskRatingColors = Theme.ramp('risk_rating');

function riskRatingBadge(rating) {
    var c = riskRatingColors[rating] || 'var(--grey)';
    return '<span style="display:inline-block;padding:var(--space-1) var(--space-4);border-radius:var(--radius-xl);font-size:var(--size-xxs);font-weight:700;color:var(--inverse);background:' + c + ';">' + (rating || 'Not Rated') + '</span>';
}

function renderRiskRatingTab(m) {
    var rr = m.overall_risk_rating || {};
    var effRating = rr.effective_rating || 'Not Rated';
    var calcRating = rr.calculated_rating || 'Not Rated';
    var score = rr.calculated_score;
    var cs = rr.component_scores || {};
    var hasOverride = rr.mrc_override != null;

    var html = '';

    // Section header
    html += '<div style="font-size:var(--size-md);font-weight:700;color:var(--text);margin-bottom:var(--space-2);">Overall Model Risk Rating</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--text-3);margin-bottom:var(--space-8);">Composite assessment synthesising validation coverage, remediation health, review currency, assumption risk, and limitation risk.</div>';

    // Effective rating banner
    var bannerColor = riskRatingColors[effRating] || 'var(--grey)';
    html += '<div style="padding:var(--space-wide);border-radius:var(--radius-lg);background:linear-gradient(135deg, ' + bannerColor + '22 0%, ' + bannerColor + '11 100%);border:2px solid ' + bannerColor + ';margin-bottom:var(--space-8);text-align:center;">';
    html += '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;margin-bottom:var(--space-3);">Effective Rating</div>';
    html += '<div style="font-size:var(--size-28);font-weight:800;color:' + bannerColor + ';">' + effRating + '</div>';
    if (score !== null && score !== undefined) {
        html += '<div style="font-size:var(--size-sm);color:var(--text-3);margin-top:var(--space-2);">Composite Score: <b>' + Math.round(score * 100) + '%</b></div>';
    }
    if (hasOverride) {
        html += '<div style="font-size:var(--size-xxs);color:var(--accent);margin-top:var(--space-3);">MRC Override Active (calculated: ' + calcRating + ')</div>';
    }
    html += '</div>';

    // MRC override info box
    if (hasOverride) {
        html += '<div style="padding:var(--space-6) var(--space-8);border-radius:var(--radius-md);border:1px solid var(--accent-border);background:var(--accent-soft);margin-bottom:var(--space-8);">';
        html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--accent-mid);margin-bottom:var(--space-3);">MRC Override</div>';
        html += '<div style="font-size:var(--size-xs);color:var(--text);"><b>Rating:</b> ' + rr.mrc_override + '</div>';
        html += '<div style="font-size:var(--size-xs);color:var(--text);"><b>Reason:</b> ' + (rr.mrc_override_reason || '\u2014') + '</div>';
        html += '<div style="font-size:var(--size-xxs);color:var(--muted);margin-top:var(--space-2);">' + (rr.mrc_override_by || '') + ' on ' + (rr.mrc_override_date || '') + '</div>';
        html += '</div>';
    }

    // Component breakdown
    html += '<div style="font-size:var(--size-sm);font-weight:600;color:var(--text);margin-bottom:var(--space-6);">Component Breakdown</div>';

    var components = [
        {key: 'validation_coverage', label: 'Validation Coverage', weight: 0.30, desc: 'Fraction of 9 questions fully addressed'},
        {key: 'remediation_health', label: 'Remediation Health', weight: 0.25, desc: 'Open and overdue remediation items'},
        {key: 'review_currency', label: 'Review Currency', weight: 0.20, desc: 'Is the review schedule current'},
        {key: 'assumption_risk', label: 'Assumption Risk', weight: 0.15, desc: 'High-impact assumption count'},
        {key: 'limitation_risk', label: 'Limitation Risk', weight: 0.10, desc: 'High-impact limitation count'}
    ];

    components.forEach(function(comp) {
        var val = cs[comp.key];
        var pct = val !== null && val !== undefined ? Math.round(val * 100) : 0;
        var color = val === null || val === undefined ? 'var(--grey)' : val >= 0.75 ? 'var(--green)' : val >= 0.45 ? 'var(--amber)' : 'var(--red)';

        html += '<div style="margin-bottom:var(--space-6);">';
        html += '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:var(--space-2);">';
        html += '<div>';
        html += '<span style="font-size:var(--size-xs);color:var(--text);font-weight:600;">' + comp.label + '</span>';
        html += '<span style="font-size:var(--size-xxs);color:var(--muted);margin-left:var(--space-3);">(' + Math.round(comp.weight * 100) + '% weight)</span>';
        html += '</div>';
        html += '<span style="font-size:var(--size-sm);font-weight:700;color:' + color + ';">' + (val !== null && val !== undefined ? pct + '%' : 'N/A') + '</span>';
        html += '</div>';
        html += '<div style="height:8px;background:var(--line);border-radius:var(--radius-4);overflow:hidden;">';
        html += '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:var(--radius-4);transition:width 0.3s;"></div>';
        html += '</div>';
        html += '<div style="font-size:var(--size-xxs);color:var(--muted-2);margin-top:var(--space-1);">' + comp.desc + '</div>';
        html += '</div>';
    });

    // Last calculated
    if (rr.last_calculated) {
        html += '<div style="font-size:var(--size-xxs);color:var(--muted);margin-top:var(--space-4);margin-bottom:var(--space-8);">Last calculated: ' + rr.last_calculated.split('T')[0] + '</div>';
    }

    // Action buttons
    html += '<div style="display:flex;gap:var(--space-4);margin-top:var(--space-8);padding-top:var(--space-8);border-top:1px solid var(--line-soft);">';
    html += '<button onclick="window.MG.refreshRiskRating(\'' + m.model_id + '\')" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--accent);">Recalculate</button>';
    if (hasOverride) {
        html += '<button onclick="window.MG.clearRiskOverride(\'' + m.model_id + '\')" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--red);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--red);">Clear Override</button>';
    } else {
        html += '<button onclick="window.MG.showRiskOverrideForm(\'' + m.model_id + '\')" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--amber);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--amber);">Apply MRC Override</button>';
    }
    html += '</div>';

    // Override form area
    html += '<div id="rr-override-area" style="margin-top:var(--space-6);"></div>';

    return html;
}

function refreshRiskRating(modelId) {
    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/risk-rating', {mode: 'cors'})
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            var m = window._mgCurrentModel;
            m.overall_risk_rating = data.risk_rating;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderRiskRatingTab(m);
        }
    })
    .catch(function(err) { console.error('[RiskRating] Refresh error:', err); });
}

function showRiskOverrideForm(modelId) {
    var area = document.getElementById('rr-override-area');
    var html = '<div style="padding:var(--space-8);border:1px solid var(--line);border-radius:var(--radius-lg);background:var(--wash-cool);">';
    html += '<div style="font-size:var(--size-sm);font-weight:600;color:var(--text);margin-bottom:var(--space-6);">Apply MRC Override</div>';

    html += '<div style="margin-bottom:var(--space-5);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;display:block;margin-bottom:var(--space-2);">Override Rating</label>';
    html += '<select id="rr-of-rating" style="width:100%;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    ['Acceptable', 'Conditional', 'Unacceptable'].forEach(function(r) {
        html += '<option value="' + r + '">' + r + '</option>';
    });
    html += '</select></div>';

    html += '<div style="margin-bottom:var(--space-5);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;display:block;margin-bottom:var(--space-2);">Reason for Override</label>';
    html += '<textarea id="rr-of-reason" rows="3" placeholder="MRC rationale for overriding the calculated rating..." style="width:100%;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);resize:vertical;box-sizing:border-box;"></textarea>';
    html += '</div>';

    html += '<div style="margin-bottom:var(--space-6);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;display:block;margin-bottom:var(--space-2);">Override By</label>';
    html += '<input id="rr-of-user" type="text" value="Johnny Mattimore" style="width:100%;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;">';
    html += '</div>';

    html += '<div style="display:flex;gap:var(--space-4);">';
    html += '<button onclick="window.MG.saveRiskOverride(\'' + modelId + '\')" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--amber);color:var(--inverse);">Apply Override</button>';
    html += '<button onclick="document.getElementById(\'rr-override-area\').innerHTML=\'\';" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--text-3);">Cancel</button>';
    html += '</div></div>';

    area.innerHTML = html;
    area.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function saveRiskOverride(modelId) {
    var reason = document.getElementById('rr-of-reason').value.trim();
    if (!reason) { alert('A reason is required for the MRC override'); return; }

    var body = {
        rating: document.getElementById('rr-of-rating').value,
        reason: reason,
        user: document.getElementById('rr-of-user').value.trim() || 'unknown'
    };

    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/risk-rating/override', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mgCurrentModel = data.model;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderRiskRatingTab(data.model);
        } else {
            alert(data.message || 'Failed to save override');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

function clearRiskOverride(modelId) {
    var reason = prompt('Reason for clearing the MRC override:');
    if (!reason || !reason.trim()) return;

    var body = {
        rating: null,
        reason: reason.trim(),
        user: 'Johnny Mattimore'
    };

    fetch(getBaseUrl() + '/api/v1/governance/models/' + modelId + '/risk-rating/override', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mgCurrentModel = data.model;
            var dc = document.getElementById('mg-detail-content');
            dc.innerHTML = renderRiskRatingTab(data.model);
        } else {
            alert(data.message || 'Failed to clear override');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

