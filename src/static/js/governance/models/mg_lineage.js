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

function renderDataLineage() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">Loading data lineage...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/data-lineage', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Error: ' + (data.message || 'Unknown') + '</div>';
                return;
            }
            window._lineageData = data;
            _drawLineagePanel(data);
        })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Failed to load data lineage.</div>';
            console.error('[Governance] Lineage load error:', err);
        });
}

function _lineageStatusBadge(status) {
    var colors = Theme.ramp('lineage_freshness');
    var labels = {fresh: 'Fresh', stale: 'Stale', missing: 'Missing'};
    var bg = colors[status] || 'var(--muted-2)';
    var label = labels[status] || status;
    return '<span style="display:inline-block;padding:var(--space-1) var(--space-4);border-radius:var(--radius-xl);font-size:var(--size-xxs);font-weight:700;color:var(--inverse);background:' + bg + ';">' + label + '</span>';
}

function _lineageHealthBadge(health) {
    var colors = Theme.ramp('lineage_health');
    var bg = colors[health] || 'var(--muted-2)';
    return '<span style="display:inline-block;padding:var(--space-2) var(--space-5);border-radius:var(--radius-pill);font-size:var(--size-xxs);font-weight:700;color:var(--inverse);background:' + bg + ';text-transform:uppercase;">' + health + '</span>';
}

function _drawLineagePanel(data) {
    var content = document.getElementById('mg-content');
    var steps = data.pipeline_steps || [];
    var summary = data.summary || {};
    var html = '<div style="padding:var(--space-8);">';

    // Header with health badge
    html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-8);">';
    html += '<div>';
    html += '<div style="font-size:var(--size-md);font-weight:700;color:var(--text);">Data Pipeline Lineage</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--text-3);margin-top:var(--space-1);">Pipeline health and data provenance tracking</div>';
    html += '</div>';
    html += '<div style="text-align:right;">';
    html += _lineageHealthBadge(summary.health || 'unknown');
    html += '<div style="font-size:var(--size-xxs);color:var(--muted);margin-top:var(--space-2);">' + (summary.fresh || 0) + '/' + (summary.total || 0) + ' steps fresh</div>';
    html += '</div></div>';

    // Pipeline DAG
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text-2);margin-bottom:var(--space-4);">Pipeline DAG</div>';
    html += '<div style="display:flex;align-items:center;gap:0;padding:var(--space-6) 0;overflow-x:auto;flex-wrap:wrap;justify-content:center;">';
    steps.forEach(function(s, idx) {
        var borderColor = Theme.ramp('lineage_freshness')[s.status];
        var bgColor = Theme.ramp('lineage_freshness_bg')[s.status];
        html += '<div style="text-align:center;min-width:90px;padding:var(--space-5) var(--space-4);border:2px solid ' + borderColor + ';border-radius:var(--radius-lg);background:' + bgColor + ';margin:var(--space-2) 0;">';
        html += '<div style="font-size:var(--size-xxs);font-weight:700;color:var(--text);">' + s.step + '</div>';
        if (s.last_run) {
            var d = s.last_run.substring(0, 16).replace('T', ' ');
            html += '<div style="font-size:var(--size-8);color:var(--text-3);margin-top:var(--space-2);">' + d + '</div>';
        } else {
            html += '<div style="font-size:var(--size-8);color:var(--red-bright);margin-top:var(--space-2);font-weight:600;">Not run</div>';
        }
        html += '<div style="margin-top:var(--space-2);">' + _lineageStatusBadge(s.status) + '</div>';
        html += '</div>';
        if (idx < steps.length - 1) {
            html += '<div style="font-size:var(--size-lg);color:var(--muted-2);padding:0 var(--space-2);">\u2192</div>';
        }
    });
    html += '</div>';

    // Staleness table
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text-2);margin:var(--space-wide) 0 var(--space-4);">Staleness Detail</div>';
    html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
    html += '<thead><tr style="background:var(--raised);">';
    ['Step', 'Generator', 'Last Run', 'Status', 'Issues'].forEach(function(h) {
        html += '<th style="padding:var(--space-3) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
    });
    html += '</tr></thead><tbody>';
    steps.forEach(function(s) {
        html += '<tr>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:600;color:var(--text);">' + s.step + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-family:monospace;font-size:var(--size-xxs);color:var(--text-3);">' + s.generator + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--text-3);">';
        if (s.last_run) {
            html += s.last_run.substring(0, 19).replace('T', ' ');
        } else {
            html += '<span style="color:var(--red-bright);">\u2014</span>';
        }
        html += '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + _lineageStatusBadge(s.status) + '</td>';
        html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-size:var(--size-xxs);color:var(--muted);">' + (s.issues.length > 0 ? s.issues.join('; ') : '\u2014') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';

    // Trace search
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text-2);margin:var(--space-10) 0 var(--space-4);">Provenance Trace</div>';
    html += '<div style="display:flex;gap:var(--space-4);align-items:center;margin-bottom:var(--space-6);">';
    html += '<select id="lineage-trace-type" onchange="window._lineagePopulateIds()" style="padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    html += '<option value="gauge">Gauge</option>';
    html += '<option value="property">Property</option>';
    html += '<option value="trade">Trade (PRS)</option>';
    html += '<option value="counterparty">Counterparty</option>';
    html += '</select>';
    html += '<select id="lineage-trace-id" style="flex:1;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--line-strong);border-radius:var(--radius-4);">';
    html += '<option value="">Loading...</option>';
    html += '</select>';
    html += '<button onclick="window._lineageTrace()" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);font-weight:600;border:1px solid var(--accent);border-radius:var(--radius-4);background:var(--accent);color:var(--inverse);cursor:pointer;">Trace</button>';
    html += '</div>';
    html += '<div id="lineage-trace-result"></div>';

    // Populate the ID dropdown on first render
    setTimeout(function() { window._lineagePopulateIds(); }, 100);

    html += '</div>';
    content.innerHTML = html;
}

// Cache for entity ID lists (avoid re-fetching on each type switch)
var _lineageIdCache = {};

window._lineagePopulateIds = function() {
    var typeSelect = document.getElementById('lineage-trace-type');
    var idSelect = document.getElementById('lineage-trace-id');
    if (!typeSelect || !idSelect) return;
    var dataType = typeSelect.value;

    // Return cached if available
    if (_lineageIdCache[dataType]) {
        _lineageRenderIdOptions(idSelect, _lineageIdCache[dataType]);
        return;
    }

    idSelect.innerHTML = '<option value="">Loading...</option>';
    var baseUrl = getBaseUrl();

    // Fetch entity list based on type
    var url;
    if (dataType === 'gauge') url = baseUrl + '/api/v1/gauges';
    else if (dataType === 'property') url = baseUrl + '/api/v1/properties';
    else if (dataType === 'trade') url = baseUrl + '/api/v1/trading/blotter';
    else if (dataType === 'counterparty') url = baseUrl + '/api/v1/counterparties';
    else { idSelect.innerHTML = '<option value="">Select type first</option>'; return; }

    fetch(url, {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var items = [];
            if (dataType === 'gauge') {
                (data.gauges || data.flood_gauges || []).forEach(function(g) {
                    var fg = g.FloodGauge || g;
                    var hdr = (fg.Header || fg.header || g);
                    var id = hdr.GaugeID || hdr.gauge_id || g.gaugeId || g.gauge_id || '';
                    var name = hdr.GaugeName || hdr.gauge_name || g.name || hdr.name || '';
                    if (id) items.push({id: id, label: name ? id + ' — ' + name : id});
                });
            } else if (dataType === 'property') {
                (data.properties || []).forEach(function(p) {
                    var hdr = (p.PropertyHeader || {}).Header || p.Header || p;
                    var id = hdr.PropertyID || hdr.property_id || p.propertyId || '';
                    var addr = (p.PropertyHeader || {}).Location || p;
                    var label = addr.Street || addr.AddressLine1 || addr.address || addr.county || '';
                    if (id) items.push({id: id, label: label ? id + ' — ' + label : id});
                });
            } else if (dataType === 'trade') {
                (data.trades || []).forEach(function(t) {
                    var id = t.swap_id || t.SwapID || '';
                    var gauge = t.gauge_name || t.gauge_id || '';
                    if (id) items.push({id: id, label: gauge ? id + ' — ' + gauge : id});
                });
            } else if (dataType === 'counterparty') {
                (data.counterparties || []).forEach(function(c) {
                    var id = c.counterparty_id || '';
                    var name = c.short_name || c.name || '';
                    if (id) items.push({id: id, label: name ? id + ' — ' + name : id});
                });
            }
            items.sort(function(a, b) { return a.label.localeCompare(b.label); });
            _lineageIdCache[dataType] = items;
            _lineageRenderIdOptions(idSelect, items);
        })
        .catch(function() {
            idSelect.innerHTML = '<option value="">Failed to load</option>';
        });
};

function _lineageRenderIdOptions(selectEl, items) {
    var html = '<option value="">— Select (' + items.length + ') —</option>';
    items.forEach(function(item) {
        html += '<option value="' + item.id + '">' + item.label + '</option>';
    });
    selectEl.innerHTML = html;
}

window._lineageTrace = function() {
    var dataType = document.getElementById('lineage-trace-type').value;
    var idSelect = document.getElementById('lineage-trace-id');
    var dataId = idSelect ? idSelect.value : '';
    var resultDiv = document.getElementById('lineage-trace-result');
    if (!dataId) {
        resultDiv.innerHTML = '<div style="font-size:var(--size-xs);color:var(--red-bright);">Please select an entity to trace.</div>';
        return;
    }
    resultDiv.innerHTML = '<div style="font-size:var(--size-xs);color:var(--muted);">Tracing...</div>';

    fetch(getBaseUrl() + '/api/v1/governance/data-lineage/trace?data_type=' + encodeURIComponent(dataType) + '&data_id=' + encodeURIComponent(dataId), {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                resultDiv.innerHTML = '<div style="font-size:var(--size-xs);color:var(--red-bright);">Error: ' + (data.message || 'Unknown') + '</div>';
                return;
            }
            if (!data.found || data.trace.length === 0) {
                resultDiv.innerHTML = '<div style="font-size:var(--size-xs);color:var(--muted);">No provenance records found for <b>' + dataType + '/' + dataId + '</b>.</div>';
                return;
            }
            // Render visual provenance trail
            var roleColors = Theme.ramp('lineage_role');
            var roleIcons = {origin: '\u25cf', derived: '\u2192', consumed: '\u25b6', found: '\u2605'};
            var html = '<div style="padding:var(--space-4) 0;">';
            html += '<div style="font-size:var(--size-xs);color:var(--text);margin-bottom:var(--space-4);font-weight:600;">' +
                data.trace.length + ' provenance step' + (data.trace.length > 1 ? 's' : '') +
                ' for <span style="font-family:monospace;color:var(--accent-mid);">' + dataId + '</span></div>';

            // Breadcrumb arrows
            html += '<div style="display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap;margin-bottom:var(--space-6);">';
            data.trace.forEach(function(t, i) {
                var col = roleColors[t.role] || 'var(--grey-dark)';
                html += '<div style="padding:var(--space-2) var(--space-5);border-radius:var(--radius-pill);background:' + col + ';color:var(--inverse);font-size:var(--size-xxs);font-weight:600;">' + t.step + '</div>';
                if (i < data.trace.length - 1) html += '<span style="color:var(--faint);font-size:var(--size-14);">\u25b8</span>';
            });
            html += '</div>';

            // Detail table
            html += '<table style="width:100%;font-size:var(--size-xxs);border-collapse:collapse;">';
            html += '<thead><tr style="background:var(--blue-grey-bg);">';
            html += '<th style="padding:var(--space-3) var(--space-4);text-align:left;">Step</th>';
            html += '<th style="padding:var(--space-3) var(--space-4);text-align:left;">Role</th>';
            html += '<th style="padding:var(--space-3) var(--space-4);text-align:left;">File</th>';
            html += '<th style="padding:var(--space-3) var(--space-4);text-align:left;">Context</th>';
            html += '</tr></thead><tbody>';
            data.trace.forEach(function(t, i) {
                var col = roleColors[t.role] || 'var(--grey-dark)';
                var bg = i % 2 === 0 ? 'var(--panel)' : 'var(--wash)';
                html += '<tr style="background:' + bg + ';border-bottom:1px solid var(--line-soft);">';
                html += '<td style="padding:var(--space-3) var(--space-4);font-weight:600;color:' + col + ';">' + (roleIcons[t.role] || '') + ' ' + t.step + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-4);color:var(--text-3);">' + t.role + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-4);font-family:monospace;font-size:var(--size-xxs);color:var(--text-2);">' + (t.file || '') + '</td>';
                html += '<td style="padding:var(--space-3) var(--space-4);color:var(--muted);">' + (t.context || '') + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table></div>';
            resultDiv.innerHTML = html;
        })
        .catch(function(err) {
            resultDiv.innerHTML = '<div style="font-size:var(--size-xs);color:var(--red-bright);">Trace request failed.</div>';
            console.error('[Governance] Trace error:', err);
        });
};

// ================================================================

