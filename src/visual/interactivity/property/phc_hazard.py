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

                // Gauge info — fetch severe counts from storms data if available
                var stormsData = phcData._storms_data || {};
                var stormsNearestGauges = stormsData.nearest_gauges || [];

                var gaugeRows = '';
                nearestGauges.forEach(function(ng) {
                    var isSynth = ng.gauge_id.indexOf('SYNTH') === 0;
                    var icon = isSynth ? '\\u2605 ' : '';
                    var tag = isSynth ? ' <span style="font-size:9px;color:#1976D2;background:#E3F2FD;padding:1px 4px;border-radius:3px;">controlling</span>' : '';

                    // Find severe count and name from storms endpoint
                    var stormGauge = stormsNearestGauges.find(function(sg) { return sg.gauge_id === ng.gauge_id; }) || {};
                    var sevCount = stormGauge.severe_count;
                    var sevSpread = stormGauge.severe_spread_bps;
                    var gaugeName = stormGauge.gauge_name || ng.gauge_id;

                    gaugeRows +=
                        '<div style="padding:4px 0;border-bottom:1px solid #f5f5f5;">' +
                        '<div style="font-size:11px;font-weight:600;">' + icon + gaugeName + tag + '</div>' +
                        '<div style="' + row + '"><span style="' + lbl + '">Distance</span><span style="' + val + '">' + (ng.distance_km || 0).toFixed(2) + 'km</span></div>' +
                        '<div style="' + row + '"><span style="' + lbl + '">Elevation</span><span style="' + val + '">' + (ng.gauge_elevation_m || 0).toFixed(1) + 'm</span></div>';
                    if (sevCount !== undefined) {
                        gaugeRows += '<div style="' + row + '"><span style="' + lbl + '">Severe storms</span><span style="' + val + 'color:#F44336;">' + sevCount + ' (' + (sevSpread || 0).toFixed(0) + 'bp)</span></div>';
                    }
                    gaugeRows += '</div>';
                });

                var elevDiff = propElev - (ng0.gauge_elevation_m || 0);
                var effectiveDiff = elevDiff + floorLevel - 0.5;

                var detailHtml =
                    '<div style="width:300px;min-width:260px;padding:8px 12px;overflow-y:auto;border-right:1px solid #eee;font-size:12px;">' +

                    // Property section
                    '<div style="' + hdr + '">Property</div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Elevation</span><span style="' + val + '">' + propElev.toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Floor level</span><span style="' + val + '">' + floorLevel.toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Flood zone</span><span style="' + val + '">' + zone + '</span></div>' +

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

                // --- Right panel: Waterfall table ---
                var chartHtml =
                    '<div id="phc-waterfall-container" style="flex:1;display:flex;flex-direction:column;padding:8px;overflow-y:auto;">' +
                    '<div style="text-align:center;font-size:12px;font-weight:600;color:#555;padding:4px 0 8px 0;">Basis Waterfall: Storm Attenuation</div>' +
                    '</div>';

                container.innerHTML = detailHtml + chartHtml;

                // --- Draw waterfall ---
                _drawBasisWaterfall(
                    document.getElementById('phc-waterfall-container'),
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
            // Basis waterfall — simple table
            // ================================================================
            function _drawBasisWaterfall(container, gaugeCount, sheCount, shdCount, propCount, gaugeSpread, propSpread) {
                var steps = [
                    { label: 'Gauge Severe', count: gaugeCount, spread: gaugeSpread, color: '#F44336', bg: '#FFEBEE' },
                    { label: 'SHE (elevation)', count: sheCount, spread: sheCount / 20000 * 10000, color: '#E65100', bg: '#FFF3E0' },
                    { label: 'SHD (distance)', count: shdCount, spread: shdCount / 20000 * 10000, color: '#2E7D32', bg: '#E8F5E9' },
                    { label: 'Property', count: propCount, spread: propSpread, color: '#1565C0', bg: '#E3F2FD' },
                ];

                var maxCount = Math.max(gaugeCount, 1);
                if (!container) return;
                var html = '<table style="width:100%;border-collapse:collapse;font-size:12px;font-family:Arial,sans-serif;">';
                html += '<thead><tr style="border-bottom:2px solid #ddd;font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' +
                    '<th style="padding:6px 8px;text-align:left;">Stage</th>' +
                    '<th style="padding:6px 8px;text-align:right;">Storms</th>' +
                    '<th style="padding:6px 8px;text-align:right;">Spread</th>' +
                    '<th style="padding:6px 8px;text-align:right;">Loss</th>' +
                    '<th style="padding:6px 12px;text-align:left;width:45%;">Attenuation</th>' +
                    '</tr></thead><tbody>';

                steps.forEach(function(s, i) {
                    var loss = i > 0 ? steps[i - 1].count - s.count : 0;
                    var lossPct = i > 0 && steps[i - 1].count > 0 ? (loss / steps[i - 1].count * 100).toFixed(0) : '';
                    var barPct = maxCount > 0 ? (s.count / maxCount * 100) : 0;

                    html += '<tr style="border-bottom:1px solid #f0f0f0;">' +
                        '<td style="padding:8px;font-weight:600;color:' + s.color + ';">' + s.label + '</td>' +
                        '<td style="padding:8px;text-align:right;font-weight:700;font-size:14px;color:' + s.color + ';">' + s.count.toLocaleString() + '</td>' +
                        '<td style="padding:8px;text-align:right;color:#555;">' + s.spread.toFixed(1) + 'bp</td>' +
                        '<td style="padding:8px;text-align:right;color:#E53935;">' + (loss > 0 ? '-' + loss.toLocaleString() + ' (' + lossPct + '%)' : '') + '</td>' +
                        '<td style="padding:8px 12px;">' +
                        '<div style="background:#f5f5f5;border-radius:3px;height:18px;position:relative;overflow:hidden;">' +
                        '<div style="background:' + s.color + '33;border-right:2px solid ' + s.color + ';height:100%;width:' + barPct + '%;min-width:2px;border-radius:3px 0 0 3px;"></div>' +
                        '</div></td></tr>';
                });

                html += '</tbody></table>';
                container.insertAdjacentHTML('beforeend', html);
            }
"""
