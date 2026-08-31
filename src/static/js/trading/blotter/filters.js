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

            function renderFilterBar() {
                var bar = document.getElementById('td-filter-bar');
                if (!bar || !tdBlotterData) return;

                // Build distinct values from trades
                var gaugeSet = {};
                var ctpySet = {};
                var triggerSet = {};
                var tenorSet = {};

                for (var i = 0; i < tdBlotterData.length; i++) {
                    var t = tdBlotterData[i];
                    if (t.gauge_id) gaugeSet[t.gauge_id] = extractAreaName(t.gauge_name || t.gauge_id);
                    if (t.counterparty) ctpySet[t.counterparty] = t.counterparty;
                    if (t.trigger) triggerSet[t.trigger] = t.trigger;
                    if (t.tenor) tenorSet[t.tenor + 'Y'] = t.tenor + 'Y';
                }

                function buildSelect(id, label, opts, currentVal) {
                    var html = '<select id="' + id + '" onchange="tdFilterChanged()" ' +
                        'style="padding:var(--space-1) var(--space-3);font-size:var(--size-xxs);border:1px solid var(--divider);border-radius:var(--radius-sm);background:var(--panel);min-width:70px;">';
                    html += '<option value="">All ' + label + '</option>';
                    var keys = Object.keys(opts).sort();
                    for (var k = 0; k < keys.length; k++) {
                        var sel = keys[k] === currentVal ? ' selected' : '';
                        html += '<option value="' + keys[k] + '"' + sel + '>' + opts[keys[k]] + '</option>';
                    }
                    html += '</select>';
                    return html;
                }

                var hasFilter = Object.keys(tdBlotterFilters).length > 0;
                var clearBtn = hasFilter ?
                    '<button onclick="tdClearFilters()" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);background:var(--blue-grey-light);color:var(--inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;">Clear</button>' :
                    '';
                var newPrsBtn = tdBlotterFilters.gauge_id ?
                    '<button onclick="tdNewPRS()" style="margin-left:var(--space-3);padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);background:var(--accent-mid);color:var(--inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;">New PRS</button>' :
                    '';

                // Active filter pills
                var pills = '';
                if (tdBlotterFilters.gauge_id) {
                    var areaName = gaugeSet[tdBlotterFilters.gauge_id] || tdBlotterFilters.gauge_name || tdBlotterFilters.gauge_id;
                    pills += '<span style="background:var(--accent-soft);color:var(--accent-mid);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-lg);font-size:var(--size-xxs);">' +
                        areaName + ' <span onclick="tdRemoveFilter(\'gauge_id\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.tenor) {
                    pills += '<span style="background:var(--ok-bg);color:var(--green-dark);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-lg);font-size:var(--size-xxs);">' +
                        tdBlotterFilters.tenor + ' <span onclick="tdRemoveFilter(\'tenor\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.counterparty) {
                    pills += '<span style="background:var(--pink-bg);color:var(--red-dark);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-lg);font-size:var(--size-xxs);">' +
                        tdBlotterFilters.counterparty.substring(0, 12) + ' <span onclick="tdRemoveFilter(\'counterparty\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.trigger) {
                    pills += '<span style="background:var(--warn-bg-warm);color:var(--amber-deep);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-lg);font-size:var(--size-xxs);">' +
                        tdBlotterFilters.trigger + ' <span onclick="tdRemoveFilter(\'trigger\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.status) {
                    pills += '<span style="background:var(--purple-bg);color:var(--purple);padding:var(--space-hair) var(--space-3);border-radius:var(--radius-lg);font-size:var(--size-xxs);">' +
                        tdBlotterFilters.status + ' <span onclick="tdRemoveFilter(\'status\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }

                var statusSet = {'Live': 'Live', 'Closed': 'Closed'};

                // Ensure programmatically-set gauge appears in dropdown even if no trades
                if (tdBlotterFilters.gauge_id && !gaugeSet[tdBlotterFilters.gauge_id]) {
                    gaugeSet[tdBlotterFilters.gauge_id] = tdBlotterFilters.gauge_name || tdBlotterFilters.gauge_id;
                }

                bar.innerHTML =
                    '<span style="font-weight:600;color:var(--text-2);">Filter:</span>' +
                    buildSelect('td-filter-gauge', 'Gauges', gaugeSet, tdBlotterFilters.gauge_id || '') +
                    buildSelect('td-filter-ctpy', 'Ctpy', ctpySet, tdBlotterFilters.counterparty || '') +
                    buildSelect('td-filter-trigger', 'Triggers', triggerSet, tdBlotterFilters.trigger || '') +
                    buildSelect('td-filter-tenor', 'Tenors', tenorSet, tdBlotterFilters.tenor || '') +
                    buildSelect('td-filter-status', 'Status', statusSet, tdBlotterFilters.status || '') +
                    clearBtn +
                    newPrsBtn +
                    '<div style="flex:1;"></div>' +
                    pills;
            }

            function extractAreaName(name) {
                if (!name) return '';
                return name;
            }

            window.tdFilterChanged = function() {
                var gaugeEl = document.getElementById('td-filter-gauge');
                var ctpyEl = document.getElementById('td-filter-ctpy');
                var trigEl = document.getElementById('td-filter-trigger');
                var tenorEl = document.getElementById('td-filter-tenor');
                var statusEl = document.getElementById('td-filter-status');

                tdBlotterFilters = {};
                if (gaugeEl && gaugeEl.value) tdBlotterFilters.gauge_id = gaugeEl.value;
                if (ctpyEl && ctpyEl.value) tdBlotterFilters.counterparty = ctpyEl.value;
                if (trigEl && trigEl.value) tdBlotterFilters.trigger = trigEl.value;
                if (tenorEl && tenorEl.value) tdBlotterFilters.tenor = tenorEl.value;
                if (statusEl && statusEl.value) tdBlotterFilters.status = statusEl.value;

                renderBlotterPnlBar();
                renderFilterBar();
                renderBlotterTable();
            };

            window.tdClearFilters = function() {
                tdBlotterFilters = {};
                renderBlotterPnlBar();
                renderFilterBar();
                renderBlotterTable();
            };

            window.tdRemoveFilter = function(key) {
                delete tdBlotterFilters[key];
                renderBlotterPnlBar();
                renderFilterBar();
                renderBlotterTable();
            };

            window.tdNewPRS = function() {
                var gaugeId = tdBlotterFilters.gauge_id;
                if (!gaugeId) return;
                if (window.TradingDesk && window.TradingDesk.hide) window.TradingDesk.hide();
                if (window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                    window.GaugeHazardCurve.show(gaugeId);
                } else if (window.viewHazardCurve) {
                    window.viewHazardCurve(gaugeId);
                }
            };

            // Apply filter programmatically (called from FS01 cell click, gauge blotter menu)
            window.tdApplyFilter = function(filters) {
                tdBlotterFilters = filters || {};
                if (!tdBlotterData) {
                    // Data not loaded yet — stash for when it arrives
                    window._tdPendingFilter = tdBlotterFilters;
                    return;
                }
                renderBlotterPnlBar();
                renderFilterBar();
                renderBlotterTable();
            };

            function getFilteredTrades() {
                if (!tdBlotterData) return [];
                var f = tdBlotterFilters;
                if (!f || Object.keys(f).length === 0) return tdBlotterData;

                return tdBlotterData.filter(function(t) {
                    if (f.gauge_id && t.gauge_id !== f.gauge_id) return false;
                    if (f.counterparty && t.counterparty !== f.counterparty) return false;
                    if (f.trigger && t.trigger !== f.trigger) return false;
                    if (f.tenor && (t.tenor + 'Y') !== f.tenor) return false;
                    var tStatus = (t.trade_status || 'Open').toLowerCase();
                    if (f.status === 'Live' && tStatus === 'closed') return false;
                    if (f.status === 'Closed' && tStatus !== 'closed') return false;
                    return true;
                });
            }

            function fmtMaturity(dateStr) {
                // Format YYYY-MM-DD to "May-29" style
                if (!dateStr) return '\u2014';
                var parts = dateStr.split('-');
                if (parts.length !== 3) return dateStr;
                var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                var m = parseInt(parts[1]) - 1;
                return months[m] + '-' + parts[0].slice(2);
            }
