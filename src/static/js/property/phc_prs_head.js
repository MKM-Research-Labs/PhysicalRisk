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
                var controls = document.getElementById('phc-controls');
                var inputStyle = 'padding:var(--space-2) var(--space-3);border:1px solid var(--divider);border-radius:var(--radius-sm);width:90px;font-size:var(--size-xs);';
                var labelStyle = 'font-weight:600;font-size:var(--size-xs);color:var(--text-2);margin-right:var(--space-2);';
                var selectStyle = 'padding:var(--space-2) var(--space-3);border:1px solid var(--divider);border-radius:var(--radius-sm);font-size:var(--size-xs);';

                // Build counterparty options
                var ctpyOptions = '<option value="">-- Select --</option>';
                counterpartyData.forEach(function(c) {
                    var label = c.short_name + ' (' + c.credit_rating + ')';
                    ctpyOptions += '<option value="' + c.counterparty_id + '">' + label + '</option>';
                });

                // Build EA zone dropdown, default to property's actual zone
                var zoneOrder = ['Zone 3b', 'Zone 3a', 'Zone 3', 'Zone 2', 'Zone 1'];
                var actualZone = phcData.flood_zone || 'Zone 1';
                var zoneOptions = '';
                zoneOrder.forEach(function(z) {
                    var sel = (z === actualZone) ? ' selected' : '';
                    zoneOptions += '<option value="' + z + '"' + sel + '>' + z + '</option>';
                });

                controls.innerHTML =
                    '<div style="display:flex;align-items:center;gap:var(--space-6);padding:var(--space-4) var(--space-8);flex-wrap:wrap;">' +
                    '<span style="' + labelStyle + '">Direction:</span>' +
                    '<select id="phc-direction" style="' + selectStyle + '">' +
                    '<option value="payer">Payer (buy protection)</option>' +
                    '<option value="receiver">Receiver (sell protection)</option>' +
                    '</select>' +
                    '<span style="' + labelStyle + '">Ctpy:</span>' +
                    '<select id="phc-counterparty" style="' + selectStyle + 'min-width:140px;">' +
                    ctpyOptions +
                    '</select>' +
                    '<span style="' + labelStyle + '">EA Zone:</span>' +
                    '<select id="phc-ea-zone" style="' + selectStyle + '">' +
                    zoneOptions +
                    '</select>' +
                    '<span style="' + labelStyle + '">Notional:</span>' +
                    '<input id="phc-notional" type="text" value="10,000,000" style="' + inputStyle + '">' +
                    '<span style="' + labelStyle + '">Tenor (yr):</span>' +
                    '<input id="phc-tenor" type="number" value="5" min="1" max="30" style="' + inputStyle + 'width:50px;">' +
                    '<span style="' + labelStyle + '">Spread (bps):</span>' +
                    '<input id="phc-spread" type="number" value="' + Math.round(((phcData.term_structure || {}).severe || {}).prs_spread_bps ? phcData.term_structure.severe.prs_spread_bps[0] : 100) + '" min="1" max="10000" style="' + inputStyle + 'width:60px;">' +
                    '</div>';

                // Auto-recompute on any input change
                var ids = ['phc-direction', 'phc-counterparty', 'phc-ea-zone', 'phc-notional', 'phc-tenor', 'phc-spread'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.addEventListener('change', function() { if (activeTab === 2) renderPRSPricing(); });
                });
            }

