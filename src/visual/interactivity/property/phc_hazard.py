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

"""Property hazard curve — Hazard Curve tab (basis waterfall + property detail)."""


def get_js():
    """Return JS fragment for hazard curve tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // Tab 0: Hazard Curve — Basis Waterfall + Property Detail
            // ================================================================
            function renderHazardCurve() {
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                var container = document.getElementById('phc-chart-container');
                container.style.display = 'flex';
                container.style.flexDirection = 'row';

                var severe = (phcData.depth_thresholds || {}).severe || {};
                var annualProb = severe.annual_probability || 0;
                var returnPeriod = severe.return_period_yrs;
                var floodCount = phcData.flood_count || 0;
                var summary = phcData.summary || {};
                var zone = phcData.flood_zone || '';
                var spreadBps = ((phcData.term_structure || {}).severe || {}).prs_spread_bps;
                var propSpread = spreadBps ? spreadBps[0] : 0;
                var rpStr = returnPeriod ? (returnPeriod.toFixed(0) + ' yr') : '\\u221E';

                // Gauge data
                var nearestGauges = phcData.nearest_gauges || [];
                var ng0 = nearestGauges[0] || {};
                var gaugeSevere = phcData._severe_at_gauge || 0;
                var gaugeSpread = gaugeSevere > 0 ? (gaugeSevere / 20000 * 10000) : 0;
                var sheCount = phcData._she ? (phcData._she.flood_count || 0) : 0;
                var shdCount = phcData._shd ? (phcData._shd.flood_count || 0) : 0;
                var propElev = phcData.elevation_m || 0;
                var floorLevel = phcData.floor_level_m || 0;

                // --- Left panel: Detail ---
                var lbl = 'font-size:10px;color:#888;';
                var val = 'font-size:13px;font-weight:600;color:#333;';
                var hdr = 'font-size:11px;font-weight:700;color:#555;margin:10px 0 4px 0;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #eee;padding-bottom:3px;';
                var row = 'display:flex;justify-content:space-between;padding:2px 0;';

                var gaugeRows = '';
                nearestGauges.forEach(function(ng) {
                    var isSynth = ng.gauge_id.indexOf('SYNTH') === 0;
                    var icon = isSynth ? '\\u2605 ' : '';
                    var tag = isSynth ? ' <span style="font-size:9px;color:#1976D2;background:#E3F2FD;padding:1px 4px;border-radius:3px;">controlling</span>' : '';
                    gaugeRows +=
                        '<div style="padding:4px 0;border-bottom:1px solid #f5f5f5;">' +
                        '<div style="font-size:11px;font-weight:600;">' + icon + ng.gauge_id.substring(0, 20) + tag + '</div>' +
                        '<div style="' + row + '"><span style="' + lbl + '">Distance</span><span style="' + val + '">' + (ng.distance_km || 0).toFixed(2) + 'km</span></div>' +
                        '<div style="' + row + '"><span style="' + lbl + '">Elevation</span><span style="' + val + '">' + (ng.gauge_elevation_m || 0).toFixed(2) + 'm AOD</span></div>';
                    var thr = ng.gauge_thresholds || {};
                    if (thr.severe_level) {
                        gaugeRows += '<div style="' + row + '"><span style="' + lbl + '">Severe</span><span style="' + val + 'color:#F44336;">' + thr.severe_level.toFixed(2) + 'm</span></div>';
                    }
                    gaugeRows += '</div>';
                });

                var elevDiff = propElev - (ng0.gauge_elevation_m || 0);
                var effectiveDiff = elevDiff + floorLevel - 0.5;

                var detailHtml =
                    '<div style="width:300px;min-width:260px;padding:8px 12px;overflow-y:auto;border-right:1px solid #eee;font-size:12px;">' +

                    // Property section
                    '<div style="' + hdr + '">Property</div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Elevation</span><span style="' + val + '">' + propElev.toFixed(2) + 'm AOD</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Floor level</span><span style="' + val + '">' + floorLevel.toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Flood zone</span><span style="' + val + '">' + zone + '</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Height diff</span><span style="' + val + '">' + elevDiff.toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Effective diff</span><span style="' + val + 'color:#E65100;">' + effectiveDiff.toFixed(2) + 'm</span></div>' +

                    // Gauges section
                    '<div style="' + hdr + '">Nearest Gauges</div>' +
                    gaugeRows +

                    // Pricing summary
                    '<div style="' + hdr + '">Pricing</div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Scenarios</span><span style="' + val + '">20,000</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Property floods</span><span style="' + val + '">' + floodCount + '</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Property spread</span><span style="' + val + 'color:#1976D2;">' + propSpread.toFixed(1) + 'bp</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Annual prob</span><span style="' + val + '">' + (annualProb * 100).toFixed(3) + '%</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Return period</span><span style="' + val + '">' + rpStr + '</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Max depth</span><span style="' + val + '">' + (summary.max_depth_m || 0).toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Mean depth</span><span style="' + val + '">' + (summary.mean_depth_m || 0).toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Transmission</span><span style="' + val + '">' + (gaugeSevere > 0 ? (floodCount / gaugeSevere * 100).toFixed(2) : '0') + '%</span></div>' +

                    '</div>';

                // --- Right panel: Waterfall chart ---
                var chartHtml =
                    '<div style="flex:1;display:flex;flex-direction:column;padding:8px;">' +
                    '<div style="text-align:center;font-size:12px;font-weight:600;color:#555;padding:4px 0;">Basis Waterfall: Storm Attenuation</div>' +
                    '<canvas id="phc-waterfall-canvas" style="flex:1;"></canvas>' +
                    '</div>';

                container.innerHTML = detailHtml + chartHtml;

                // --- Draw waterfall ---
                _drawBasisWaterfall(
                    document.getElementById('phc-waterfall-canvas'),
                    gaugeSevere, sheCount, shdCount, floodCount,
                    gaugeSpread, propSpread
                );

                var bar = document.getElementById('phc-stats-bar');
                var basis = gaugeSpread - propSpread;
                bar.innerHTML =
                    '<span><b>Gauge:</b> ' + gaugeSevere + ' severe (' + gaugeSpread.toFixed(1) + 'bp)</span>' +
                    '<span><b>SHE:</b> ' + sheCount + ' (' + (sheCount/20000*10000).toFixed(1) + 'bp)</span>' +
                    '<span><b>SHD:</b> ' + shdCount + ' (' + (shdCount/20000*10000).toFixed(1) + 'bp)</span>' +
                    '<span><b>Property:</b> ' + floodCount + ' (' + propSpread.toFixed(1) + 'bp)</span>' +
                    '<span><b>Basis:</b> <span style="color:#E65100;">' + basis.toFixed(1) + 'bp</span></span>';
            }

            // ================================================================
            // Basis waterfall — simple equal step-down
            // ================================================================
            function _drawBasisWaterfall(canvas, gaugeCount, sheCount, shdCount, propCount, gaugeSpread, propSpread) {
                if (!canvas) return;
                var ctx = canvas.getContext('2d');
                var dpr = window.devicePixelRatio || 1;
                var w = canvas.offsetWidth;
                var h = canvas.offsetHeight;
                canvas.width = w * dpr;
                canvas.height = h * dpr;
                ctx.scale(dpr, dpr);

                var pad = { top: 30, bottom: 50, left: 20, right: 20 };
                var plotW = w - pad.left - pad.right;
                var plotH = h - pad.top - pad.bottom;

                var steps = [
                    { label: 'Gauge Severe', count: gaugeCount, color: '#F44336', spread: gaugeSpread },
                    { label: 'SHE', count: sheCount, color: '#FF9800', spread: sheCount / 20000 * 10000 },
                    { label: 'SHD', count: shdCount, color: '#4CAF50', spread: shdCount / 20000 * 10000 },
                    { label: 'Property', count: propCount, color: '#1976D2', spread: propSpread },
                ];

                // Equal vertical steps — each bar drops by the same visual amount
                var nSteps = steps.length;
                var stepH = plotH / nSteps;
                var barW = plotW / (nSteps * 2 - 1);

                steps.forEach(function(s, i) {
                    var x = pad.left + i * barW * 2;
                    var barTop = pad.top + i * stepH;
                    var barH = plotH - i * stepH;

                    // Bar fill
                    ctx.fillStyle = s.color + '25';
                    ctx.fillRect(x, barTop, barW, barH);
                    ctx.strokeStyle = s.color;
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x, barTop, barW, barH);

                    // Coloured cap
                    ctx.fillStyle = s.color + '55';
                    ctx.fillRect(x, barTop, barW, Math.min(barH, 6));

                    // Count + spread above bar
                    ctx.textAlign = 'center';
                    ctx.fillStyle = s.color;
                    ctx.font = 'bold 14px Arial';
                    ctx.fillText(s.count.toLocaleString(), x + barW / 2, barTop - 8);
                    ctx.font = '10px Arial';
                    ctx.fillStyle = '#777';
                    ctx.fillText(s.spread.toFixed(0) + 'bp', x + barW / 2, barTop - 22);

                    // Label at bottom
                    ctx.fillStyle = '#444';
                    ctx.font = '10px Arial';
                    ctx.fillText(s.label, x + barW / 2, pad.top + plotH + 14);

                    // Connector to next step
                    if (i < nSteps - 1) {
                        var nextX = pad.left + (i + 1) * barW * 2;
                        var nextTop = pad.top + (i + 1) * stepH;

                        // Horizontal dashed line
                        ctx.setLineDash([3, 3]);
                        ctx.strokeStyle = '#ccc';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(x + barW, barTop);
                        ctx.lineTo(nextX, barTop);
                        ctx.stroke();
                        ctx.setLineDash([]);

                        // Drop arrow
                        var midX = x + barW + (nextX - x - barW) / 2;
                        ctx.strokeStyle = '#E5393580';
                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        ctx.moveTo(midX, barTop + 4);
                        ctx.lineTo(midX, nextTop - 4);
                        ctx.stroke();
                        ctx.beginPath();
                        ctx.moveTo(midX - 3, nextTop - 9);
                        ctx.lineTo(midX, nextTop - 4);
                        ctx.lineTo(midX + 3, nextTop - 9);
                        ctx.stroke();

                        // Loss label
                        var loss = s.count - steps[i + 1].count;
                        if (loss > 0) {
                            ctx.fillStyle = '#E5393580';
                            ctx.font = '9px Arial';
                            ctx.textAlign = 'center';
                            ctx.fillText('-' + loss.toLocaleString(), midX, (barTop + nextTop) / 2 + 4);
                        }
                    }
                });
            }
"""
