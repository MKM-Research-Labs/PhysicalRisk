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

            function _tdRenderSurfaceTable(data) {
                var wrap = document.getElementById('td-stress-surface-wrap');
                if (!wrap) return;

                var surface = data.probability_surface;
                if (!surface || !surface.water_levels || !surface.hours) {
                    wrap.innerHTML = '<div style="color:var(--muted-2);text-align:center;padding:var(--space-inset) 0;">No surface data available</div>';
                    return;
                }

                var levels = surface.water_levels;
                var hours = surface.hours;
                var probs = surface.probabilities;
                var alertLv = data.alert_level || 0;
                var warningLv = data.warning_level || 0;
                var severeLv = data.severe_level || 0;
                var koHour = (data.summary || {}).first_trigger_hour;

                // Build HTML table
                var html = '<table style="border-collapse:collapse;font-size:var(--size-xxs);font-family:monospace;">';
                // Header row: hours
                html += '<tr><th style="padding:var(--space-2) var(--space-3);border:1px solid var(--line-strong);background:var(--sunken);font-size:var(--size-xxs);position:sticky;left:0;z-index:1;">m \\ H</th>';
                for (var hi = 0; hi < hours.length; hi++) {
                    html += '<th style="padding:var(--space-2) var(--space-3);border:1px solid var(--line-strong);background:var(--sunken);font-size:var(--size-xxs);min-width:38px;text-align:center;">H' + hours[hi] + '</th>';
                }
                html += '</tr>';

                // Data rows: one per water level (descending)
                for (var li = 0; li < levels.length; li++) {
                    var lv = levels[li];
                    // Row background based on trigger band
                    var rowBg = 'var(--panel)';
                    if (severeLv > 0 && lv >= severeLv) rowBg = 'var(--danger-bg-soft)';
                    else if (warningLv > 0 && lv >= warningLv) rowBg = 'var(--warn-bg-warm)';
                    else if (alertLv > 0 && lv >= alertLv) rowBg = 'var(--warn-bg)';

                    // Level label with trigger band colour indicator
                    var lvColor = 'var(--text)';
                    if (severeLv > 0 && lv >= severeLv) lvColor = 'var(--red-dark)';
                    else if (warningLv > 0 && lv >= warningLv) lvColor = 'var(--amber-deep)';
                    else if (alertLv > 0 && lv >= alertLv) lvColor = 'var(--gold-dark)';

                    html += '<tr>';
                    html += '<td style="padding:var(--space-2) var(--space-3);border:1px solid var(--line-strong);background:var(--sunken);font-weight:bold;color:' + lvColor + ';position:sticky;left:0;z-index:1;white-space:nowrap;">' + lv.toFixed(1) + '</td>';

                    for (var hi = 0; hi < hours.length; hi++) {
                        var p = probs[li][hi];
                        var cellBg = rowBg;
                        var cellText = '';
                        if (p == null) {
                            // After KO: blank
                            cellBg = 'var(--code)';
                            cellText = '';
                        } else {
                            cellText = p.toFixed(1);
                            // Intensity shading within band
                            var alpha = Math.min(p / 100, 1.0) * 0.3;
                            if (severeLv > 0 && lv >= severeLv) cellBg = 'rgba(211,47,47,' + (0.08 + alpha) + ')';
                            else if (warningLv > 0 && lv >= warningLv) cellBg = 'rgba(230,81,0,' + (0.06 + alpha * 0.8) + ')';
                            else if (alertLv > 0 && lv >= alertLv) cellBg = 'rgba(255,193,7,' + (0.06 + alpha * 0.6) + ')';
                            else cellBg = 'rgba(200,200,200,' + (alpha * 0.3) + ')';
                        }

                        html += '<td style="padding:var(--space-1) var(--space-2);border:1px solid var(--line-soft);text-align:right;background:' + cellBg + ';font-size:var(--size-xxs);">' + cellText + '</td>';
                    }
                    html += '</tr>';
                }
                html += '</table>';
                html += '<div style="padding:var(--space-3) var(--space-4);font-size:var(--size-xxs);color:var(--muted);">P(flood) % at each water level (rows) and hour (columns). Capped at severe level. Shading: ' +
                    '<span style="background:var(--warn-bg);padding:var(--space-hair) var(--space-3);border:1px solid var(--line-strong);">Alert</span> ' +
                    '<span style="background:var(--warn-bg-warm);padding:var(--space-hair) var(--space-3);border:1px solid var(--line-strong);">Warning</span> ' +
                    '<span style="background:var(--danger-bg-soft);padding:var(--space-hair) var(--space-3);border:1px solid var(--line-strong);">Severe</span>' +
                    (koHour != null ? ' | Columns trimmed at KO H' + koHour : '') +
                    '</div>';
                wrap.innerHTML = html;
            }
