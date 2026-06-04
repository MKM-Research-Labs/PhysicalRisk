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
                var sheCount = phcData._she ? (phcData._she.flood_count || 0) : 0;
                var shdCount = phcData._shd ? (phcData._shd.flood_count || 0) : 0;
                var propElev = phcData.elevation_m || 0;
                var floorLevel = phcData.floor_level_m || 0;

                // Spread values + denominator come from the hazard payload —
                // the generator already used the correct storm count when
                // it built spread_decomposition. Previously these were
                // computed as count/20000*10000 in the panel, which baked
                // in the thames default --num-storms; for any catchment
                // with a different storm count (e.g. halong's 100) the
                // gauge/SHE/SHD values were 200× too small while the asset
                // (using the real prs_spread_bps) stayed correct.
                var sd = phcData.spread_decomposition || {};
                var numStorms = (phcData._metadata || {}).num_storms || 0;
                var gaugeSpread = sd.gauge_spread_bps || 0;
                var sheSpread = sd.she_spread_bps || 0;
                var shdSpread = sd.shd_spread_bps || 0;

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

                    // Asset section
                    '<div style="' + hdr + '">Asset</div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Elevation</span><span style="' + val + '">' + propElev.toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Floor level</span><span style="' + val + '">' + floorLevel.toFixed(2) + 'm</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Flood zone</span><span style="' + val + '">' + zone + '</span></div>' +

                    // Gauges section
                    '<div style="' + hdr + '">Nearest Gauges</div>' +
                    gaugeRows +

                    // Pricing summary — Scenarios now uses the real
                    // num_storms from the data (was hard-coded 20,000).
                    '<div style="' + hdr + '">Pricing</div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Scenarios</span><span style="' + val + '">' + (numStorms ? numStorms.toLocaleString() : '\\u2014') + '</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Asset floods</span><span style="' + val + '">' + floodCount + '</span></div>' +
                    '<div style="' + row + '"><span style="' + lbl + '">Asset spread</span><span style="' + val + 'color:#1976D2;">' + propSpread.toFixed(1) + 'bp</span></div>' +
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

                // BRI-adjusted (resilient) stage — only present once the
                // propertybri/commercialbri curve has been loaded. The spread
                // comes from spread_decomposition; the resilient flood count
                // comes from the /bri endpoint payload (phcData._bri).
                var hasBri = (sd.bri_spread_bps !== undefined && sd.bri_spread_bps !== null);
                var briSpread = sd.bri_spread_bps || 0;
                var briCount = phcData._bri ? (phcData._bri.flood_count || 0) : null;

                // --- Draw waterfall ---
                _drawBasisWaterfall(
                    document.getElementById('phc-waterfall-container'),
                    gaugeSevere, sheCount, shdCount, floodCount,
                    gaugeSpread, sheSpread, shdSpread, propSpread,
                    hasBri, briCount, briSpread
                );

                // Bottom stats bar — spreads now come from spread_decomposition
                // (was previously count/20000*10000 which hard-coded the
                // thames default storm count).
                var bar = document.getElementById('phc-stats-bar');
                var basis = gaugeSpread - propSpread;
                bar.innerHTML =
                    '<span><b>Gauge:</b> ' + gaugeSevere + ' severe (' + gaugeSpread.toFixed(1) + 'bp)</span>' +
                    '<span><b>SHE:</b> ' + sheCount + ' (' + sheSpread.toFixed(1) + 'bp)</span>' +
                    '<span><b>SHD:</b> ' + shdCount + ' (' + shdSpread.toFixed(1) + 'bp)</span>' +
                    '<span><b>Asset:</b> ' + floodCount + ' (' + propSpread.toFixed(1) + 'bp)</span>' +
                    '<span><b>Basis:</b> <span style="color:#E65100;">' + basis.toFixed(1) + 'bp</span></span>';
            }

            // ================================================================
            // Basis waterfall — simple table
            // ================================================================
            function _drawBasisWaterfall(container, gaugeCount, sheCount, shdCount, propCount,
                                          gaugeSpread, sheSpread, shdSpread, propSpread,
                                          hasBri, briCount, briSpread) {
                // All four spreads come from spread_decomposition in the
                // hazard payload — no per-step storm-count arithmetic in
                // the panel any more.
                var steps = [
                    { label: 'Gauge Severe', count: gaugeCount, spread: gaugeSpread, color: '#F44336', bg: '#FFEBEE' },
                    { label: 'SHE (elevation)', count: sheCount, spread: sheSpread, color: '#E65100', bg: '#FFF3E0' },
                    { label: 'SHD (distance)', count: shdCount, spread: shdSpread, color: '#2E7D32', bg: '#E8F5E9' },
                    { label: 'Asset', count: propCount, spread: propSpread, color: '#1565C0', bg: '#E3F2FD' },
                ];

                // 5th stage — BRI-adjusted (resilient) spread. Completes the
                // basis: raising the effective flood floor removes severe floods,
                // so the resilient spread <= the pure asset spread. The flood
                // count may be null if the /bri endpoint wasn't loaded; the
                // attenuation column then falls back to a count-free row.
                if (hasBri) {
                    steps.push({ label: 'BRI Resilient', count: (briCount == null ? propCount : briCount),
                                 spread: briSpread, color: '#4527A0', bg: '#EDE7F6',
                                 countMissing: (briCount == null) });
                }

                // Peril stages — wind's effect on the asset spread. These sit on
                // a different axis to the flood attenuation above: FAW is flood
                // AND wind (intersection, <= asset flood), FOW is flood OR wind
                // (union, the default PRS coupon, >= asset flood). Spreads come
                // from spread_decomposition; storm counts from prs_perils. For
                // FOW the Loss column carries the wind uplift in bps over the
                // pure (flood-only) asset spread; FAW shows the overlap value.
                var _psd = (typeof phcData !== 'undefined' && phcData.spread_decomposition) || {};
                var _pp = (typeof phcData !== 'undefined' && phcData.prs_perils) || {};
                function _perilCount(p) { return (p && typeof p.count === 'number') ? p.count : 0; }
                if (_psd.win_spread_bps !== undefined && _psd.win_spread_bps !== null) {
                    steps.push({ label: 'WIN (wind only)',
                                 count: _perilCount(_pp.wind_only),
                                 spread: _psd.win_spread_bps || 0,
                                 color: '#00897B', bg: '#E0F2F1',
                                 isPeril: true, perilFirst: true });
                }
                if (_psd.faw_spread_bps !== undefined && _psd.faw_spread_bps !== null) {
                    steps.push({ label: 'FAW (flood\\u2227wind)',
                                 count: _perilCount(_pp.flood_and_wind),
                                 spread: _psd.faw_spread_bps || 0,
                                 color: '#00838F', bg: '#E0F7FA',
                                 isPeril: true,
                                 perilFirst: (_psd.win_spread_bps === undefined || _psd.win_spread_bps === null) });
                }
                if (_psd.fow_spread_bps !== undefined && _psd.fow_spread_bps !== null) {
                    steps.push({ label: 'FOW (flood\\u2228wind)',
                                 count: _perilCount(_pp.flood_or_wind),
                                 spread: _psd.fow_spread_bps || 0,
                                 color: '#5D4037', bg: '#EFEBE9',
                                 isPeril: true, perilUplift: true });
                }

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
                    var barPct = (!s.countMissing && maxCount > 0) ? (s.count / maxCount * 100) : 0;
                    var countCell = s.countMissing ? '\\u2014' : s.count.toLocaleString();
                    var lossCell = '';

                    if (s.isPeril) {
                        // Peril rows aren't part of the flood attenuation chain.
                        // FOW (union) shows the wind uplift in bps over the pure
                        // asset (flood-only) spread; FAW (overlap) shows no delta.
                        if (s.perilUplift) {
                            var wUp = s.spread - propSpread;
                            if (Math.abs(wUp) >= 0.05) {
                                var upCol = wUp > 0 ? '#2E7D32' : '#E53935';
                                lossCell = '<span style="color:' + upCol + ';">' +
                                    (wUp > 0 ? '+' : '') + wUp.toFixed(1) + 'bp wind</span>';
                            }
                        }
                    } else {
                        // A stage with a missing count (BRI when /bri didn't load)
                        // shows a count-free row: dash for count, no loss, no bar.
                        var loss = (!s.countMissing && i > 0 && !steps[i - 1].countMissing)
                            ? steps[i - 1].count - s.count : 0;
                        var lossPct = (loss > 0 && steps[i - 1].count > 0)
                            ? (loss / steps[i - 1].count * 100).toFixed(0) : '';
                        if (loss > 0) {
                            lossCell = '<span style="color:#E53935;">-' + loss.toLocaleString() +
                                ' (' + lossPct + '%)</span>';
                        }
                    }

                    var rowStyle = s.perilFirst
                        ? 'border-top:2px solid #cfcfcf;border-bottom:1px solid #f0f0f0;'
                        : 'border-bottom:1px solid #f0f0f0;';

                    html += '<tr style="' + rowStyle + '">' +
                        '<td style="padding:8px;font-weight:600;color:' + s.color + ';">' + s.label + '</td>' +
                        '<td style="padding:8px;text-align:right;font-weight:700;font-size:14px;color:' + s.color + ';">' + countCell + '</td>' +
                        '<td style="padding:8px;text-align:right;color:#555;">' + s.spread.toFixed(1) + 'bp</td>' +
                        '<td style="padding:8px;text-align:right;">' + lossCell + '</td>' +
                        '<td style="padding:8px 12px;">' +
                        (s.countMissing ? '' :
                        '<div style="background:#f5f5f5;border-radius:3px;height:18px;position:relative;overflow:hidden;">' +
                        '<div style="background:' + s.color + '33;border-right:2px solid ' + s.color + ';height:100%;width:' + barPct + '%;min-width:2px;border-radius:3px 0 0 3px;"></div>' +
                        '</div>') +
                        '</td></tr>';
                });

                html += '</tbody></table>';
                container.insertAdjacentHTML('beforeend', html);
            }
"""
