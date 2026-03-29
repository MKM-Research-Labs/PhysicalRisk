# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Trade Blotter — filter sub-module.

Filter bar rendering, filter change handlers, programmatic filter API,
getFilteredTrades, and maturity formatting helper.
"""


def get_js() -> str:
    """Return JavaScript fragment for blotter filter bar and handlers."""
    return """
            // ==============================================================
            // Filter bar
            // ==============================================================
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
                        'style="padding:2px 6px;font-size:10px;border:1px solid #ccc;border-radius:3px;background:white;min-width:70px;">';
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
                    '<button onclick="tdClearFilters()" style="padding:2px 8px;font-size:10px;background:#78909c;color:white;border:none;border-radius:3px;cursor:pointer;">Clear</button>' :
                    '';

                // Active filter pills
                var pills = '';
                if (tdBlotterFilters.gauge_id) {
                    var areaName = gaugeSet[tdBlotterFilters.gauge_id] || tdBlotterFilters.gauge_id;
                    pills += '<span style="background:#e3f2fd;color:#1565c0;padding:1px 6px;border-radius:8px;font-size:10px;">' +
                        areaName + ' <span onclick="tdRemoveFilter(\\'gauge_id\\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.tenor) {
                    pills += '<span style="background:#e8f5e9;color:#2e7d32;padding:1px 6px;border-radius:8px;font-size:10px;">' +
                        tdBlotterFilters.tenor + ' <span onclick="tdRemoveFilter(\\'tenor\\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.counterparty) {
                    pills += '<span style="background:#fce4ec;color:#c62828;padding:1px 6px;border-radius:8px;font-size:10px;">' +
                        tdBlotterFilters.counterparty.substring(0, 12) + ' <span onclick="tdRemoveFilter(\\'counterparty\\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.trigger) {
                    pills += '<span style="background:#fff3e0;color:#e65100;padding:1px 6px;border-radius:8px;font-size:10px;">' +
                        tdBlotterFilters.trigger + ' <span onclick="tdRemoveFilter(\\'trigger\\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }
                if (tdBlotterFilters.status) {
                    pills += '<span style="background:#f3e5f5;color:#7b1fa2;padding:1px 6px;border-radius:8px;font-size:10px;">' +
                        tdBlotterFilters.status + ' <span onclick="tdRemoveFilter(\\'status\\')" style="cursor:pointer;font-weight:bold;">&times;</span></span>';
                }

                var statusSet = {'Live': 'Live', 'Closed': 'Closed'};

                bar.innerHTML =
                    '<span style="font-weight:600;color:#555;">Filter:</span>' +
                    buildSelect('td-filter-gauge', 'Gauges', gaugeSet, tdBlotterFilters.gauge_id || '') +
                    buildSelect('td-filter-ctpy', 'Ctpy', ctpySet, tdBlotterFilters.counterparty || '') +
                    buildSelect('td-filter-trigger', 'Triggers', triggerSet, tdBlotterFilters.trigger || '') +
                    buildSelect('td-filter-tenor', 'Tenors', tenorSet, tdBlotterFilters.tenor || '') +
                    buildSelect('td-filter-status', 'Status', statusSet, tdBlotterFilters.status || '') +
                    clearBtn +
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
                if (!dateStr) return '\\u2014';
                var parts = dateStr.split('-');
                if (parts.length !== 3) return dateStr;
                var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                var m = parseInt(parts[1]) - 1;
                return months[m] + '-' + parts[0].slice(2);
            }
"""
