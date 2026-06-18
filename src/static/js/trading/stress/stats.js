// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            // ---- Stats bar with links ----
            function _tdRenderStressStats(data) {
                var bar = document.getElementById('td-stress-stats-bar');
                if (!bar) return;

                var s = data.summary || {};
                var stFmt = function(v) {
                    var abs = Math.abs(v);
                    var str = abs >= 1e6 ? (abs/1e6).toFixed(1) + 'M' :
                              abs >= 1e3 ? (abs/1e3).toFixed(1) + 'K' :
                              abs.toFixed(0);
                    return (v < 0 ? '-' : '+') + '\u00A3' + str;
                };
                var stCol = function(v) { return v >= 0 ? '#2e7d32' : '#c62828'; };

                var koText = s.num_triggered > 0 ?
                    '<span style="font-weight:700;color:#c62828;"><b>Knocked Out:</b> ' +
                        s.num_triggered + '/' + s.num_trades + ' @ H' + s.first_trigger_hour + '</span>' :
                    '<span style="color:#2e7d32;"><b>No KO</b></span>';

                var gaugeId = data.gauge_id || '';
                var stormId = data.storm_id || '';

                // Model AUC badge — colour indicates reliability
                var aucVal = data.model_auc;
                var aucText = '';
                if (aucVal !== null && aucVal !== undefined) {
                    var aucPct = (aucVal * 100).toFixed(1);
                    var aucCol = aucVal >= 0.95 ? '#2e7d32' :
                                 aucVal >= 0.88 ? '#e65100' : '#c62828';
                    var aucTip = aucVal >= 0.95 ? 'High confidence' :
                                 aucVal >= 0.88 ? 'Moderate confidence' :
                                 'Low confidence — rare flood gauge';
                    aucText = '<span title="' + aucTip + '" style="font-weight:700;color:' + aucCol + ';">' +
                        '<b>Model AUC:</b> ' + aucPct + '%</span>';
                }

                var linkStyle = 'font-size:10px;color:#1565c0;cursor:pointer;text-decoration:underline;font-weight:600;margin-left:4px;';

                var parts = [
                    '<span><b>MTM:</b> <span style="color:' + stCol(s.total_mtm) + ';">' +
                        stFmt(s.total_mtm) + '</span></span>',
                    '<span style="color:#e65100;"><b>Peak P:</b> ' +
                        (s.peak_p_flood * 100).toFixed(1) + '% @ H' + s.peak_p_flood_hour + '</span>',
                    koText,
                    '<span style="font-weight:700;color:' + stCol(s.max_stress_pnl) + ';">' +
                        '<b>Max Stress:</b> ' + stFmt(s.max_stress_pnl) +
                        ' @ H' + s.max_stress_hour + '</span>',
                ];
                if (aucText) parts.push(aucText);
                bar.innerHTML = parts.join('<span style="margin:0 6px;color:#ddd;">|</span>');
            }

            // ---- Link handlers ----
            function tdStressOpenGauge(gaugeId) {
                if (!gaugeId) return;
                // Hide trading desk and open gauge panel
                if (window.TradingDesk && window.TradingDesk.hide) window.TradingDesk.hide();
                if (window.viewHazardCurve) {
                    window.viewHazardCurve(gaugeId);
                } else {
                    console.warn('[Stress] viewHazardCurve not available');
                }
            }

            window.tdStressOpenGauge = tdStressOpenGauge;

            function tdStressOpenDamage(stormId) {
                if (!stormId) return;
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                // Fetch portfolio impact for this storm
                fetch(baseUrl + '/api/v1/propertyts/' + stormId + '/portfolio-impact', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            _tdShowDamageOverlay(data, stormId);
                        } else {
                            _tdShowDamageOverlay({message: data.message || 'No data available'}, stormId);
                        }
                    })
                    .catch(function(err) {
                        console.error('[Stress] Damage fetch error:', err);
                        _tdShowDamageOverlay({message: 'Error fetching portfolio impact'}, stormId);
                    });
            }

            window.tdStressOpenDamage = tdStressOpenDamage;

            function _tdShowDamageOverlay(data, stormId) {
                // Remove existing overlay
                var existing = document.getElementById('td-stress-damage-overlay');
                if (existing) existing.remove();

                var overlay = document.createElement('div');
                overlay.id = 'td-stress-damage-overlay';
                overlay.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'background:white;border:1px solid #ccc;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3);' +
                    'z-index:3000;padding:20px;min-width:340px;max-width:500px;font-family:Arial,sans-serif;';

                if (data.message) {
                    overlay.innerHTML =
                        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">' +
                            '<span style="font-weight:700;font-size:13px;">Property Damage</span>' +
                            '<button onclick="this.parentElement.parentElement.remove()" ' +
                                'style="border:none;background:none;font-size:18px;cursor:pointer;color:#666;">&times;</button>' +
                        '</div>' +
                        '<div style="color:#999;font-size:12px;">' + data.message + '</div>';
                } else {
                    var impact = data.impact || data;
                    var fmtK = function(v) {
                        if (!v && v !== 0) return '\u2014';
                        return '\u00A3' + Math.round(v/1000).toLocaleString() + 'K';
                    };

                    overlay.innerHTML =
                        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">' +
                            '<span style="font-weight:700;font-size:13px;">Portfolio Damage \u2014 ' + (data.storm_name || stormId) + '</span>' +
                            '<button onclick="this.parentElement.parentElement.remove()" ' +
                                'style="border:none;background:none;font-size:18px;cursor:pointer;color:#666;">&times;</button>' +
                        '</div>' +
                        '<table style="width:100%;font-size:12px;border-collapse:collapse;">' +
                            '<tr style="border-bottom:1px solid #eee;">' +
                                '<td style="padding:6px 0;color:#666;">Properties Flooded</td>' +
                                '<td style="padding:6px 0;text-align:right;font-weight:600;">' + (impact.properties_flooded || 0) + '</td>' +
                            '</tr>' +
                            '<tr style="border-bottom:1px solid #eee;">' +
                                '<td style="padding:6px 0;color:#666;">Total Properties</td>' +
                                '<td style="padding:6px 0;text-align:right;">' + (impact.total_properties || 0) + '</td>' +
                            '</tr>' +
                            '<tr style="border-bottom:1px solid #eee;">' +
                                '<td style="padding:6px 0;color:#666;">Total Damage</td>' +
                                '<td style="padding:6px 0;text-align:right;font-weight:700;color:#c62828;">' + fmtK(impact.total_damage) + '</td>' +
                            '</tr>' +
                            '<tr style="border-bottom:1px solid #eee;">' +
                                '<td style="padding:6px 0;color:#666;">Max Flood Depth</td>' +
                                '<td style="padding:6px 0;text-align:right;">' + ((impact.max_depth || 0).toFixed(2)) + 'm</td>' +
                            '</tr>' +
                            '<tr>' +
                                '<td style="padding:6px 0;color:#666;">Avg Damage per Property</td>' +
                                '<td style="padding:6px 0;text-align:right;">' + fmtK(impact.avg_damage) + '</td>' +
                            '</tr>' +
                        '</table>';
                }

                document.body.appendChild(overlay);
            }

            // ---- Cleanup ----
            function tdCleanupStressCharts() {
                if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }
                tdStressResult = null;
            }
