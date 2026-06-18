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

            // ---- Port Stress: P(flood) Sub-Tab — Storm P&L Heatmap ----
            function _psRenderPFloodTab(result) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                // Only gauges with positions
                var gauges = (result.gauges || []).filter(function(g) {
                    return g.num_trades > 0 && g.hydrograph && g.hydrograph.length > 0 && g.severe_level > 0;
                });

                if (gauges.length === 0) {
                    content.innerHTML = '<div style="padding:40px;text-align:center;color:#999;">No gauges with open positions and hydrograph data.</div>';
                    return;
                }

                // Sort by peak stress P&L (worst first)
                gauges.sort(function(a, b) { return a.stress_pnl - b.stress_pnl; });

                content.innerHTML =
                    '<div style="padding:4px 16px 0;font-size:10px;color:#666;flex-shrink:0;display:flex;align-items:center;gap:16px;">' +
                    '<span style="font-weight:600;">Storm P&amp;L Heatmap</span>' +
                    '<span>Gauges with positions, sorted by peak stress P&amp;L</span>' +
                    '<span style="margin-left:auto;display:flex;align-items:center;gap:4px;">' +
                    '<span style="display:inline-block;width:60px;height:10px;background:linear-gradient(to right,#b71c1c,#e53935,#ff8a80,#f5f5f5,#81c784,#2e7d32);border-radius:2px;"></span>' +
                    '<span style="font-size:9px;">Loss → Gain</span>' +
                    '</span>' +
                    '</div>' +
                    '<div id="ps-pflood-chart-area" style="flex:1;overflow:hidden;padding:4px 0;position:relative;">' +
                    '<canvas id="ps-heatmap-canvas" style="display:block;"></canvas>' +
                    '</div>';

                _psDrawHeatmap(gauges);
            }

            function _psDrawHeatmap(gauges) {
                var canvas = document.getElementById('ps-heatmap-canvas');
                var area = document.getElementById('ps-pflood-chart-area');
                if (!canvas || !area) return;

                var labelWidth = 160;
                var topPad = 20;
                var bottomPad = 28;
                var rightPad = 100;
                var totalRows = gauges.length + 1;  // +1 for TOTAL row
                var rowHeight = Math.max(16, Math.min(32, Math.floor((area.clientHeight - topPad - bottomPad) / totalRows)));
                var totalHeight = topPad + totalRows * rowHeight + bottomPad;
                var totalWidth = area.clientWidth;
                var heatWidth = totalWidth - labelWidth - rightPad;

                var dpr = window.devicePixelRatio || 1;
                canvas.width = totalWidth * dpr;
                canvas.height = totalHeight * dpr;
                canvas.style.width = totalWidth + 'px';
                canvas.style.height = totalHeight + 'px';

                var ctx = canvas.getContext('2d');
                ctx.scale(dpr, dpr);

                // Compute hourly P&L grid
                var nHours = gauges[0].hydrograph.length;
                var colWidth = heatWidth / nHours;

                // Find global P&L extremes for colour scale
                var globalMin = 0, globalMax = 0;
                var pnlGrid = [];
                for (var gi = 0; gi < gauges.length; gi++) {
                    var g = gauges[gi];
                    var hydro = g.hydrograph;
                    var sev = g.severe_level;
                    var netNot = 0, totalMtm = 0;
                    (g.trades || []).forEach(function(t) { netNot += t.notional; totalMtm += t.mtm; });

                    var row = [];
                    for (var hr = 0; hr < nHours; hr++) {
                        var pf = _fpPFlood(hydro[hr], hr, sev);
                        var spnl = netNot * pf - totalMtm;
                        row.push(spnl);
                        if (spnl < globalMin) globalMin = spnl;
                        if (spnl > globalMax) globalMax = spnl;
                    }
                    pnlGrid.push(row);
                }

                // Colour mapping: red (loss) → white (zero) → green (gain)
                function pnlColor(val) {
                    var r, g, b;
                    if (val < 0 && globalMin < 0) {
                        var t = Math.min(1, val / globalMin);
                        // white → red
                        r = Math.round(245 - t * (245 - 183));
                        g = Math.round(245 - t * (245 - 28));
                        b = Math.round(245 - t * (245 - 28));
                    } else if (val > 0 && globalMax > 0) {
                        var t = Math.min(1, val / globalMax);
                        // white → green
                        r = Math.round(245 - t * (245 - 46));
                        g = Math.round(245 - t * (245 - 125));
                        b = Math.round(245 - t * (245 - 50));
                    } else {
                        r = 245; g = 245; b = 245;
                    }
                    return 'rgb(' + r + ',' + g + ',' + b + ')';
                }

                // Clear
                ctx.fillStyle = '#fff';
                ctx.fillRect(0, 0, totalWidth, totalHeight);

                // Draw heatmap cells
                for (var gi = 0; gi < gauges.length; gi++) {
                    var y = topPad + gi * rowHeight;
                    for (var hr = 0; hr < nHours; hr++) {
                        var x = labelWidth + hr * colWidth;
                        ctx.fillStyle = pnlColor(pnlGrid[gi][hr]);
                        ctx.fillRect(x, y, Math.ceil(colWidth) + 1, rowHeight);
                    }

                    // Row border
                    ctx.strokeStyle = 'rgba(0,0,0,0.06)';
                    ctx.beginPath();
                    ctx.moveTo(labelWidth, y + rowHeight);
                    ctx.lineTo(totalWidth - rightPad, y + rowHeight);
                    ctx.stroke();

                    // Gauge label
                    var gName = gauges[gi].gauge_name || gauges[gi].gauge_id;
                    if (gName.length > 22) gName = gName.substring(0, 20) + '…';
                    var thColor = gauges[gi].threshold === 'severe' ? '#c62828' :
                                  gauges[gi].threshold === 'warning' ? '#e65100' :
                                  gauges[gi].threshold === 'alert' ? '#f9a825' : '#757575';

                    ctx.fillStyle = thColor;
                    ctx.font = '600 ' + Math.min(10, rowHeight - 4) + 'px system-ui, sans-serif';
                    ctx.textAlign = 'right';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(gName, labelWidth - 6, y + rowHeight / 2);

                    // P&L label at end of row
                    var peakPnl = gauges[gi].stress_pnl;
                    ctx.fillStyle = peakPnl >= 0 ? '#2e7d32' : '#c62828';
                    ctx.font = '700 ' + Math.min(9, rowHeight - 4) + 'px system-ui, sans-serif';
                    ctx.textAlign = 'left';
                    ctx.fillText(fmtGBP(peakPnl), totalWidth - rightPad + 4, y + rowHeight / 2);
                }

                // TOTAL row — portfolio sum per hour
                var totalY = topPad + gauges.length * rowHeight;

                // Separator line
                ctx.strokeStyle = '#333';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(labelWidth, totalY);
                ctx.lineTo(totalWidth - rightPad, totalY);
                ctx.stroke();
                ctx.lineWidth = 1;

                // Compute & draw total row
                var portTotal = 0;
                for (var hr = 0; hr < nHours; hr++) {
                    var colSum = 0;
                    for (var gi = 0; gi < gauges.length; gi++) colSum += pnlGrid[gi][hr];
                    var x = labelWidth + hr * colWidth;
                    ctx.fillStyle = pnlColor(colSum);
                    ctx.fillRect(x, totalY, Math.ceil(colWidth) + 1, rowHeight);
                    if (hr === nHours - 1) portTotal = colSum;
                }

                // "TOTAL" label
                ctx.fillStyle = '#333';
                ctx.font = '700 ' + Math.min(10, rowHeight - 4) + 'px system-ui, sans-serif';
                ctx.textAlign = 'right';
                ctx.textBaseline = 'middle';
                ctx.fillText('TOTAL', labelWidth - 6, totalY + rowHeight / 2);

                // Total P&L value
                var portPnlSum = 0;
                gauges.forEach(function(g) { portPnlSum += g.stress_pnl; });
                ctx.fillStyle = portPnlSum >= 0 ? '#2e7d32' : '#c62828';
                ctx.font = '700 ' + Math.min(10, rowHeight - 4) + 'px system-ui, sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText(fmtGBP(portPnlSum), totalWidth - rightPad + 4, totalY + rowHeight / 2);

                // X-axis: hour labels
                ctx.fillStyle = '#666';
                ctx.font = '9px system-ui, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                var axisY = topPad + totalRows * rowHeight + 4;
                var tickInterval = nHours <= 48 ? 6 : nHours <= 96 ? 12 : 24;
                for (var hr = 0; hr <= nHours; hr += tickInterval) {
                    var tx = labelWidth + hr * colWidth;
                    ctx.fillText(hr + 'h', tx, axisY);
                }

                // Title
                ctx.fillStyle = '#333';
                ctx.font = '600 10px system-ui, sans-serif';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'top';
                ctx.fillText('Storm Hour →', labelWidth, 4);

                // Tooltip on hover
                canvas.onmousemove = function(e) {
                    var rect = canvas.getBoundingClientRect();
                    var mx = e.clientX - rect.left;
                    var my = e.clientY - rect.top;
                    var gi = Math.floor((my - topPad) / rowHeight);
                    var hr = Math.floor((mx - labelWidth) / colWidth);
                    if (hr >= 0 && hr < nHours && mx >= labelWidth) {
                        if (gi >= 0 && gi < gauges.length) {
                            var g = gauges[gi];
                            var spnl = pnlGrid[gi][hr];
                            var pf = _fpPFlood(g.hydrograph[hr], hr, g.severe_level);
                            canvas.title = g.gauge_name + ' | Hour ' + hr +
                                ' | P(flood): ' + (pf * 100).toFixed(1) + '%' +
                                ' | Stress P&L: ' + fmtGBP(Math.round(spnl));
                        } else if (gi === gauges.length) {
                            var colSum = 0;
                            for (var i = 0; i < gauges.length; i++) colSum += pnlGrid[i][hr];
                            canvas.title = 'TOTAL | Hour ' + hr +
                                ' | Portfolio Stress P&L: ' + fmtGBP(Math.round(colSum));
                        } else {
                            canvas.title = '';
                        }
                    } else {
                        canvas.title = '';
                    }
                };

                // Click to navigate to Gauge P&L
                canvas.onclick = function(e) {
                    var rect = canvas.getBoundingClientRect();
                    var my = e.clientY - rect.top;
                    var gi = Math.floor((my - topPad) / rowHeight);
                    if (gi >= 0 && gi < gauges.length) {
                        psSelectedGaugeId = gauges[gi].gauge_id;
                        psSwitchSubTab('gaugepnl');
                    }
                };
                canvas.style.cursor = 'pointer';
            }
