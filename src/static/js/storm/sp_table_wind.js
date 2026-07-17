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

            var spWindData = null;  // last loaded wind-impact response

            function loadWindDamage() {
                var sid = (document.getElementById('sp-storm-select') || {}).value || '';
                var container = document.getElementById('sp-table-container');
                if (!sid) {
                    _renderWindEmpty('Select a storm to view wind impact.');
                    return;
                }
                container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">Loading wind impact…</div>';
                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/' + sid + '/wind-impact', {mode:'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        spWindData = d;
                        if (d.status !== 'success') {
                            _renderWindEmpty(d.message || 'Wind impact unavailable.');
                            return;
                        }
                        _renderWindDamage();
                    })
                    .catch(function(err) {
                        console.error('Wind impact error:', err);
                        _renderWindEmpty('Failed to load wind impact.');
                    });
            }

            function _renderWindEmpty(msg) {
                _renderWindSummary(null);
                var container = document.getElementById('sp-table-container');
                container.innerHTML =
                    '<div style="padding:48px 24px;text-align:center;color:#888;font-size:13px;">' +
                    '<div style="font-size:36px;margin-bottom:12px;">\u26A1</div>' +
                    '<div>' + msg + '</div></div>';
            }

            function _renderWindDamage() {
                if (!spWindData) return;
                var rows = spWindData.rows || [];
                _renderWindSummary(spWindData);
                if (!rows.length) {
                    _renderWindEmpty('No typhoon paired with this storm — pick a storm with the ⚡ TYPHOON badge to see wind impact.');
                    return;
                }
                _renderDamageTable(rows, 'wind');
            }

            function _renderWindSummary(data) {
                var summary = document.getElementById('sp-summary');
                var typhoonInfo = '';
                var resCount = 0, comCount = 0, totalDamage = 0;
                if (data && data.summary) {
                    resCount = data.summary.properties_in_scope || 0;
                    comCount = data.summary.commercials_in_scope || 0;
                    totalDamage = data.summary.total_wind_damage || 0;
                }
                var modelLabel = (data && data.typhoon)
                    ? '⚡ ' + (data.typhoon.event_id || '?') + ' (' + (data.typhoon.scenario_family || '?') + ')'
                    : 'No typhoon';
                var modelColor = (data && data.typhoon) ? '#bf360c' : '#888';
                var cards = [
                    { label: 'Properties Affected', value: resCount, color: '#1976d2' },
                    { label: 'Commercials Affected', value: comCount, color: '#1976d2' },
                    { label: 'Total Wind Damage', value: totalDamage ? fmtGBP(totalDamage) : '\u2014', color: '#d32f2f' },
                    { label: 'Typhoon', value: modelLabel, color: modelColor },
                ];
                summary.innerHTML = '';
                cards.forEach(function(card) {
                    var div = document.createElement('div');
                    div.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + card.color + ';';
                    div.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + card.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + card.color + ';margin-top:2px;">' + card.value + '</div>';
                    summary.appendChild(div);
                });
            }
