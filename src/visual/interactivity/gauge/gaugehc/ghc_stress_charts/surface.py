# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Tab 3: P(flood) Surface Table — heat-map grid of probabilities."""


def get_js() -> str:
    """Return JS fragment for the P(flood) surface table."""
    return """
            // ---- Tab 3: P(flood) Surface Table ----
            function _renderSurfaceTable(data) {
                var wrap = document.getElementById('stress-surface-wrap');
                if (!wrap) return;

                var surface = data.probability_surface;
                if (!surface || !surface.water_levels || !surface.hours) {
                    wrap.innerHTML = '<div style="color:#999;text-align:center;padding:40px 0;">No surface data available</div>';
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
                var html = '<table style="border-collapse:collapse;font-size:10px;font-family:monospace;width:100%;">';
                // Header row: hours
                html += '<tr><th style="padding:3px 6px;border:1px solid #ddd;background:#f5f5f5;font-size:9px;position:sticky;left:0;z-index:1;">m \\\\ H</th>';
                for (var hi = 0; hi < hours.length; hi++) {
                    html += '<th style="padding:3px 5px;border:1px solid #ddd;background:#f5f5f5;font-size:9px;min-width:38px;text-align:center;">H' + hours[hi] + '</th>';
                }
                html += '</tr>';

                // Data rows: one per water level (descending)
                for (var li = 0; li < levels.length; li++) {
                    var lv = levels[li];
                    // Row background based on trigger band
                    var rowBg = '#fff';
                    if (severeLv > 0 && lv >= severeLv) rowBg = '#FFEBEE';
                    else if (warningLv > 0 && lv >= warningLv) rowBg = '#FFF3E0';
                    else if (alertLv > 0 && lv >= alertLv) rowBg = '#FFF8E1';

                    // Level label with trigger band colour indicator
                    var lvColor = '#333';
                    if (severeLv > 0 && lv >= severeLv) lvColor = '#c62828';
                    else if (warningLv > 0 && lv >= warningLv) lvColor = '#e65100';
                    else if (alertLv > 0 && lv >= alertLv) lvColor = '#f57f17';

                    html += '<tr>';
                    html += '<td style="padding:3px 6px;border:1px solid #ddd;background:#f5f5f5;font-weight:bold;color:' + lvColor + ';position:sticky;left:0;z-index:1;white-space:nowrap;">' + lv.toFixed(1) + '</td>';

                    for (var hi = 0; hi < hours.length; hi++) {
                        var p = probs[li][hi];
                        var cellBg = rowBg;
                        var cellText = '';
                        if (p == null) {
                            // After KO: blank
                            cellBg = '#f0f0f0';
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

                        html += '<td style="padding:2px 4px;border:1px solid #eee;text-align:right;background:' + cellBg + ';font-size:9px;">' + cellText + '</td>';
                    }
                    html += '</tr>';
                }
                html += '</table>';
                html += '<div style="padding:6px 8px;font-size:9px;color:#888;">P(flood) % at each water level (rows) and hour (columns). Capped at severe level. Shading: ' +
                    '<span style="background:#FFF8E1;padding:1px 6px;border:1px solid #ddd;">Alert</span> ' +
                    '<span style="background:#FFF3E0;padding:1px 6px;border:1px solid #ddd;">Warning</span> ' +
                    '<span style="background:#FFEBEE;padding:1px 6px;border:1px solid #ddd;">Severe</span>' +
                    (koHour != null ? ' | Columns trimmed at KO H' + koHour : '') +
                    '</div>';
                wrap.innerHTML = html;
            }
"""
