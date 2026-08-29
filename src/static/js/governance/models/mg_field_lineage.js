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

function renderFieldLineage() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:40px;text-align:center;color:var(--muted);">Loading field lineage registry...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/field-lineage', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:40px;text-align:center;color:var(--red);">Error: ' + (data.message || 'Unknown') + '</div>';
                return;
            }
            window._fieldLineageData = data;
            _drawFieldLineagePanel(data);
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:40px;text-align:center;color:var(--red);">Failed to load field lineage registry.</div>';
            console.error('[Governance] Field lineage load error:', err);
        });
}

function _flSourceBadge(source) {
    if (!source || source === 'computed at runtime' || source === 'hardcoded') {
        return '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;color:var(--inverse);background:var(--purple-bright);">COMPUTED</span>';
    }
    return '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;color:var(--inverse);background:var(--accent);">FILE</span>';
}

function _flStepBadge(step) {
    if (!step) return '<span style="font-size:9px;color:var(--muted-2);">\u2014</span>';
    var colors = Theme.ramp('dataset');
    var bg = colors[step] || 'var(--muted-2)';
    return '<span style="display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;color:var(--inverse);background:' + bg + ';">' + step + '</span>';
}

function _drawFieldLineagePanel(data) {
    var content = document.getElementById('mg-content');
    var reports = data.reports || {};
    var summary = data.summary || [];
    var html = '<div style="padding:16px;">';

    // Header
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">';
    html += '<div>';
    html += '<div style="font-size:13px;font-weight:700;color:var(--text);">Field-Level Data Lineage</div>';
    html += '<div style="font-size:11px;color:var(--text-3);margin-top:2px;">BCBS 239 Principle 3 \u2014 every field traceable to its source</div>';
    html += '</div>';
    html += '<div style="text-align:right;">';
    html += '<span style="font-size:22px;font-weight:700;color:var(--accent);">' + data.total_fields + '</span>';
    html += '<div style="font-size:10px;color:var(--muted);">fields mapped across ' + data.total_reports + ' reports</div>';
    html += '</div></div>';

    // Search bar
    html += '<div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">';
    html += '<input id="fl-search" type="text" placeholder="Search fields (e.g. fair_spread, notional, GEV...)" style="flex:1;padding:6px 10px;font-size:11px;border:1px solid var(--line-strong);border-radius:4px;" />';
    html += '<button onclick="window._flSearch()" style="padding:6px 14px;font-size:11px;font-weight:600;border:1px solid var(--accent);border-radius:4px;background:var(--accent);color:var(--inverse);cursor:pointer;">Search</button>';
    html += '</div>';
    html += '<div id="fl-search-result"></div>';

    // Report cards
    html += '<div style="font-size:11px;font-weight:600;color:var(--text-2);margin:8px 0;">Reports & Screens</div>';
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-bottom:16px;">';
    summary.forEach(function(r) {
        html += '<div onclick="window._flExpandReport(\'' + r.report + '\')" style="padding:12px;border:1px solid var(--line);border-radius:6px;cursor:pointer;transition:box-shadow 0.15s;" onmouseover="this.style.boxShadow=\'var(--shadow-ghost)\'" onmouseout="this.style.boxShadow=\'none\'">';
        html += '<div style="font-size:11px;font-weight:700;color:var(--text);">' + r.label + '</div>';
        html += '<div style="font-size:9px;color:var(--muted);margin-top:2px;font-family:monospace;">' + r.generator + '</div>';
        html += '<div style="margin-top:6px;display:flex;gap:12px;">';
        html += '<span style="font-size:10px;color:var(--text-3);">' + r.section_count + ' sections</span>';
        html += '<span style="font-size:10px;color:var(--accent);font-weight:600;">' + r.field_count + ' fields</span>';
        html += '</div></div>';
    });
    html += '</div>';

    // Expanded report detail area
    html += '<div id="fl-report-detail"></div>';

    html += '</div>';
    content.innerHTML = html;

    // Enter key triggers search
    var searchInput = document.getElementById('fl-search');
    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') window._flSearch();
        });
    }
}

window._flSearch = function() {
    var query = document.getElementById('fl-search').value.trim();
    var resultDiv = document.getElementById('fl-search-result');
    if (!query) {
        resultDiv.innerHTML = '';
        return;
    }
    resultDiv.innerHTML = '<div style="font-size:11px;color:var(--muted);">Searching...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/field-lineage/lookup?search=' + encodeURIComponent(query), {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success' || data.count === 0) {
                resultDiv.innerHTML = '<div style="font-size:11px;color:var(--muted);padding:8px 0;">No fields matched "<b>' + query + '</b>".</div>';
                return;
            }
            var html = '<div style="margin-bottom:12px;font-size:10px;color:var(--text-3);">' + data.count + ' field(s) matched</div>';
            html += '<table style="width:100%;border-collapse:collapse;font-size:10px;margin-bottom:16px;">';
            html += '<thead><tr style="background:var(--sunken);">';
            ['Report', 'Field', 'Label', 'Source', 'Pipeline Step', 'CDM Path'].forEach(function(h) {
                html += '<th style="padding:5px 8px;text-align:left;border-bottom:2px solid var(--line-strong);font-size:9px;color:var(--text-2);">' + h + '</th>';
            });
            html += '</tr></thead><tbody>';
            data.results.forEach(function(r) {
                var l = r.lineage;
                html += '<tr>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid var(--code);color:var(--text);font-weight:500;">' + r.report_label + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid var(--code);font-family:monospace;color:var(--accent);">' + r.field + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid var(--code);">' + (l.label || '') + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid var(--code);">' + _flSourceBadge(l.source_field) + ' <span style="font-family:monospace;font-size:9px;color:var(--text-3);">' + (l.source_file || 'runtime') + '</span></td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid var(--code);">' + _flStepBadge(l.pipeline_step) + '</td>';
                html += '<td style="padding:4px 8px;border-bottom:1px solid var(--code);font-family:monospace;font-size:9px;color:var(--muted);">' + (l.cdm_path || '\u2014') + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';
            resultDiv.innerHTML = html;
        })
        .catch(function(err) {
            resultDiv.innerHTML = '<div style="font-size:11px;color:var(--red-bright);">Search failed.</div>';
        });
};

window._flExpandReport = function(reportKey) {
    var detailDiv = document.getElementById('fl-report-detail');
    var data = window._fieldLineageData;
    if (!data || !data.reports[reportKey]) return;

    var report = data.reports[reportKey];
    var html = '<div style="border:1px solid var(--line);border-radius:6px;padding:14px;margin-top:4px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">';
    html += '<div style="font-size:12px;font-weight:700;color:var(--text);">' + report.label + '</div>';
    html += '<button onclick="document.getElementById(\'fl-report-detail\').innerHTML=\'\'" style="border:none;background:none;font-size:16px;cursor:pointer;color:var(--muted-2);">&times;</button>';
    html += '</div>';

    var sections = report.sections || {};
    Object.keys(sections).forEach(function(skey) {
        var sec = sections[skey];
        var fields = sec.fields || {};
        html += '<div style="margin-bottom:14px;">';
        html += '<div style="font-size:10px;font-weight:600;color:var(--text-2);padding:4px 0;border-bottom:1px solid var(--line-soft);margin-bottom:6px;">' + sec.label + '</div>';
        html += '<table style="width:100%;border-collapse:collapse;font-size:10px;">';
        html += '<thead><tr style="background:var(--raised);">';
        ['Field', 'Label', 'Source File', 'Source Field', 'Step', 'CDM Path', 'Computation'].forEach(function(h) {
            html += '<th style="padding:4px 6px;text-align:left;font-size:9px;color:var(--text-4);border-bottom:1px solid var(--line-soft);">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';
        Object.keys(fields).forEach(function(fkey) {
            var f = fields[fkey];
            html += '<tr>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);font-family:monospace;color:var(--accent);font-weight:500;">' + fkey + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);">' + (f.label || '') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);font-family:monospace;font-size:9px;color:var(--text-3);">' + (f.source_file || '\u2014') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);font-family:monospace;font-size:9px;color:var(--text-3);">' + (f.source_field || '\u2014') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);">' + _flStepBadge(f.pipeline_step) + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);font-family:monospace;font-size:9px;color:var(--muted);">' + (f.cdm_path || '\u2014') + '</td>';
            html += '<td style="padding:3px 6px;border-bottom:1px solid var(--sunken);font-size:9px;color:var(--text-2);max-width:200px;">' + (f.computation || '\u2014') + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div>';
    });

    html += '</div>';
    detailDiv.innerHTML = html;
    detailDiv.scrollIntoView({behavior: 'smooth', block: 'nearest'});
};

// ================================================================

