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

            function buildPRSControls() {
                var controls = document.getElementById('hazard-controls');
                var inputStyle = 'padding:3px 6px;border:1px solid var(--divider);border-radius:3px;width:90px;font-size:11px;';
                var labelStyle = 'font-weight:600;font-size:11px;color:var(--text-2);margin-right:3px;';
                var selectStyle = 'padding:3px 6px;border:1px solid var(--divider);border-radius:3px;font-size:11px;';

                // Build counterparty options from loaded data
                var ctpyOptions = '<option value="">-- Select --</option>';
                counterpartyData.forEach(function(c) {
                    var label = c.short_name + ' (' + c.credit_rating + ')';
                    ctpyOptions += '<option value="' + c.counterparty_id + '">' + label + '</option>';
                });

                // Build maturity options (1Y through 5Y)
                var maturityOptions = '';
                for (var t = 1; t <= 5; t++) {
                    var matDate = computeMaturityDate(t);
                    var matLabel = formatMaturityShort(matDate) + ' (' + t + 'Y)';
                    var matValue = maturityDateToStr(matDate);
                    var sel = t === 5 ? ' selected' : '';
                    maturityOptions += '<option value="' + matValue + '" data-tenor="' + t + '"' + sel + '>' + matLabel + '</option>';
                }

                controls.innerHTML =
                    '<div style="display:flex;align-items:center;gap:8px;padding:8px 16px;">' +
                    '<span style="' + labelStyle + '">Direction:</span>' +
                    '<select id="prs-direction" style="' + selectStyle + '">' +
                    '<option value="payer">Payer (buy protection)</option>' +
                    '<option value="receiver">Receiver (sell protection)</option>' +
                    '</select>' +
                    '<span style="' + labelStyle + '">Ctpy:</span>' +
                    '<select id="prs-counterparty" style="' + selectStyle + 'min-width:140px;">' +
                    ctpyOptions +
                    '</select>' +
                    '<input id="prs-trigger" type="hidden" value="severe">' +
                    '<span style="' + labelStyle + '">Notional:</span>' +
                    '<input id="prs-notional" type="text" value="10,000,000" style="' + inputStyle + '">' +
                    '<span style="' + labelStyle + '">Tenor:</span>' +
                    '<select id="prs-maturity" style="' + selectStyle + 'min-width:100px;">' +
                    maturityOptions +
                    '</select>' +
                    '<button id="prs-maturity-info" onclick="showMaturityPopup()" ' +
                    'style="padding:2px 7px;font-size:10px;border:1px solid var(--divider);border-radius:3px;background:var(--bg);cursor:pointer;color:var(--accent-mid);font-weight:bold;" ' +
                    'title="Show maturity schedule">i</button>' +
                    '<span style="' + labelStyle + '">Spread (bps):</span>' +
                    '<input id="prs-spread" type="number" value="0" min="0" max="1000" style="' + inputStyle + 'width:60px;">' +
                    '<span id="prs-hazard-display" style="font-size:10px;color:var(--muted);"></span>' +
                    '</div>';

                // Auto-recompute on any input change
                var ids = ['prs-direction', 'prs-counterparty', 'prs-trigger', 'prs-notional', 'prs-maturity', 'prs-spread'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.addEventListener('change', function() { if (activeTab === 0) renderPRSPricing(); });
                });
            }

            // Maturity schedule popup
            window.showMaturityPopup = function() {
                // Remove existing popup if any
                var existing = document.getElementById('maturity-popup');
                if (existing) { existing.remove(); return; }

                var popup = document.createElement('div');
                popup.id = 'maturity-popup';
                popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'background:var(--panel);border:1px solid var(--divider);border-radius:6px;box-shadow:var(--shadow-toast);' +
                    'z-index:3000;padding:16px;font-family:monospace;font-size:12px;min-width:320px;';

                var today = new Date();
                var roll = currentRollDate(today);
                var rollLabel = formatMaturityDate(roll);

                var html = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">' +
                    '<span style="font-weight:bold;font-size:13px;font-family:Arial;">PRS Maturity Schedule</span>' +
                    '<button onclick="document.getElementById(\'maturity-popup\').remove()" ' +
                    'style="border:none;background:none;font-size:18px;cursor:pointer;color:var(--text-3);">&times;</button></div>' +
                    '<div style="font-size:10px;color:var(--muted);margin-bottom:8px;">Roll: ' + rollLabel + '</div>' +
                    '<table style="width:100%;border-collapse:collapse;">' +
                    '<tr style="border-bottom:2px solid var(--line-strong);"><th style="text-align:left;padding:4px 8px;">Tenor</th>' +
                    '<th style="text-align:left;padding:4px 8px;">Maturity</th>' +
                    '<th style="text-align:right;padding:4px 8px;">Actual</th></tr>';

                for (var t = 1; t <= 5; t++) {
                    var matDate = computeMaturityDate(t, today);
                    var actualYears = ((matDate - today) / (365.25 * 86400000)).toFixed(2);
                    html += '<tr style="border-bottom:1px solid var(--line-soft);">' +
                        '<td style="padding:4px 8px;font-weight:600;">' + t + 'Y</td>' +
                        '<td style="padding:4px 8px;">' + formatMaturityDate(matDate) + '</td>' +
                        '<td style="padding:4px 8px;text-align:right;">' + actualYears + 'y</td></tr>';
                }
                html += '</table>';
                popup.innerHTML = html;
                document.body.appendChild(popup);
            };
