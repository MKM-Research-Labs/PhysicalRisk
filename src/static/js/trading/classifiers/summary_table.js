
            function _clRenderSummaryTable(gauges) {
                var pane = document.getElementById('cl-table-pane');
                if (!pane) return;

                if (!gauges || gauges.length === 0) {
                    pane.innerHTML = '<div style="padding:20px;color:#999;font-size:12px;">No gauges found</div>';
                    return;
                }

                var html = '<table style="width:100%;border-collapse:collapse;font-size:11px;">';
                html += '<thead><tr style="background:#f5f7fa;border-bottom:2px solid #ddd;">';
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
                    var rowBg = isSelected ? '#e3f2fd' : (i % 2 === 0 ? '#fff' : '#fafbfc');

                    html += '<tr data-gauge-id="' + g.gauge_id + '" ';
                    html += 'style="cursor:pointer;background:' + rowBg + ';border-bottom:1px solid #f0f0f0;" ';
                    html += 'onmouseover="this.style.background=\'#e8f0fe\'" ';
                    html += 'onmouseout="this.style.background=\'' + rowBg + '\'">';

                    // Gauge name
                    html += '<td style="padding:6px 10px;font-weight:500;">' + g.gauge_name + '</td>';

                    // Status dot
                    var dotColor = isTrained ? '#4caf50' : '#bbb';
                    var dotLabel = isTrained ? 'Trained' : 'Not trained';
                    html += '<td style="padding:6px 8px;text-align:center;">';
                    html += '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' +
                            dotColor + ';margin-right:4px;vertical-align:middle;"></span>';
                    html += '<span style="color:#666;">' + dotLabel + '</span></td>';

                    // AUC
                    if (g.auc_roc != null) {
                        var aucColor = g.auc_roc >= 0.95 ? '#2e7d32' : (g.auc_roc >= 0.90 ? '#f57f17' : '#c62828');
                        html += '<td style="padding:6px 8px;text-align:right;color:' + aucColor + ';font-weight:600;">' +
                                g.auc_roc.toFixed(4) + '</td>';
                    } else {
                        html += '<td style="padding:6px 8px;text-align:right;color:#ccc;">\u2014</td>';
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
                    var btnColor = isTrained ? '#f57f17' : '#1976d2';
                    html += '<button data-train-gauge="' + g.gauge_id + '" ';
                    html += 'style="padding:3px 10px;font-size:10px;font-weight:600;background:' + btnColor + ';';
                    html += 'color:white;border:none;border-radius:3px;cursor:pointer;">' + btnLabel + '</button>';
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
