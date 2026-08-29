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

            function _clRenderSummaryTable(gauges) {
                var pane = document.getElementById('cl-table-pane');
                if (!pane) return;

                if (!gauges || gauges.length === 0) {
                    pane.innerHTML = '<div style="padding:20px;color:var(--muted-2);font-size:12px;">No gauges found</div>';
                    return;
                }

                var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
                html += '<thead><tr style="background:var(--header-from);border-bottom:2px solid var(--line-strong);">';
                html += '<th style="padding:6px 10px;text-align:left;font-weight:600;">Gauge</th>';
                html += '<th style="padding:6px 8px;text-align:center;font-weight:600;">Status</th>';
                html += '<th style="padding:6px 8px;text-align:right;font-weight:600;">AUC</th>';
                html += '<th style="padding:6px 8px;text-align:right;font-weight:600;">Accuracy</th>';
                html += '<th style="padding:6px 8px;text-align:right;font-weight:600;">Flood Rate</th>';
                html += '<th style="padding:6px 8px;text-align:right;font-weight:600;">Samples</th>';
                html += '<th style="padding:6px 10px;text-align:center;font-weight:600;">Action</th>';
                html += '</tr></thead><tbody>';

                for (var i = 0; i < gauges.length; i++) {
                    var g = gauges[i];
                    var isTrained = g.has_model;
                    var isSelected = (g.gauge_id === clSelectedGaugeId);
                    var rowBg = isSelected ? 'var(--accent-soft)' : (i % 2 === 0 ? 'var(--panel)' : 'var(--tray-bg)');

                    html += '<tr data-gauge-id="' + g.gauge_id + '" ';
                    html += 'style="cursor:pointer;background:' + rowBg + ';border-bottom:1px solid var(--code);" ';
                    html += 'onmouseover="this.style.background=\'var(--rv-wash)\'" ';
                    html += 'onmouseout="this.style.background=\'' + rowBg + '\'">';

                    // Gauge name
                    html += '<td style="padding:6px 10px;font-weight:500;">' + g.gauge_name + '</td>';

                    // Status dot
                    var dotColor = isTrained ? 'var(--green-bright)' : 'var(--faint)';
                    var dotLabel = isTrained ? 'Trained' : 'Not trained';
                    html += '<td style="padding:6px 8px;text-align:center;">';
                    html += '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' +
                            dotColor + ';margin-right:4px;vertical-align:middle;"></span>';
                    html += '<span style="color:var(--text-3);">' + dotLabel + '</span></td>';

                    // AUC
                    if (g.auc_roc != null) {
                        var aucColor = g.auc_roc >= 0.95 ? 'var(--green-dark)' : (g.auc_roc >= 0.90 ? 'var(--gold-dark)' : 'var(--red-dark)');
                        html += '<td style="padding:6px 8px;text-align:right;color:' + aucColor + ';font-weight:600;">' +
                                g.auc_roc.toFixed(4) + '</td>';
                    } else {
                        html += '<td style="padding:6px 8px;text-align:right;color:var(--divider);">\u2014</td>';
                    }

                    // Accuracy
                    html += '<td style="padding:6px 8px;text-align:right;">' +
                            (g.accuracy != null ? g.accuracy.toFixed(4) : '\u2014') + '</td>';

                    // Flood rate
                    html += '<td style="padding:6px 8px;text-align:right;">' +
                            (g.flood_rate != null ? (g.flood_rate * 100).toFixed(1) + '%' : '\u2014') + '</td>';

                    // Samples
                    html += '<td style="padding:6px 8px;text-align:right;">' +
                            (g.n_samples != null ? g.n_samples.toLocaleString() : '\u2014') + '</td>';

                    // Action button
                    html += '<td style="padding:6px 10px;text-align:center;">';
                    var btnLabel = isTrained ? 'Retrain' : 'Train';
                    var btnColor = isTrained ? 'var(--gold-dark)' : 'var(--accent)';
                    html += '<button data-train-gauge="' + g.gauge_id + '" ';
                    html += 'style="padding:3px 10px;font-size:10px;font-weight:600;background:' + btnColor + ';';
                    html += 'color:var(--inverse);border:none;border-radius:3px;cursor:pointer;">' + btnLabel + '</button>';
                    html += '</td>';

                    html += '</tr>';
                }

                html += '</tbody></table>';
                pane.innerHTML = html;

                // Bind row clicks → detail panel
                var rows = pane.querySelectorAll('tr[data-gauge-id]');
                for (var r = 0; r < rows.length; r++) {
                    rows[r].addEventListener('click', function(e) {
                        // Don't trigger on button click
                        if (e.target.tagName === 'BUTTON') return;
                        var gid = this.getAttribute('data-gauge-id');
                        clSelectedGaugeId = gid;
                        var gauge = (clSummary.gauges || []).find(function(x) { return x.gauge_id === gid; });
                        if (gauge) _clRenderDetail(gauge);
                        // Re-render table to update selected row highlight
                        _clRenderSummaryTable(clSummary.gauges || []);
                    });
                }

                // Bind train buttons
                var btns = pane.querySelectorAll('button[data-train-gauge]');
                for (var b = 0; b < btns.length; b++) {
                    btns[b].addEventListener('click', function(e) {
                        e.stopPropagation();
                        var gid = this.getAttribute('data-train-gauge');
                        _clStartSingleTraining(gid);
                    });
                }
            }
