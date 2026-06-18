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

            // ================================================================
            // Summary — report card
            // ================================================================

            function loadSummary() {
                var summary = document.getElementById('sp-summary');
                var container = document.getElementById('sp-table-container');
                summary.innerHTML = '';  // report card uses the main container, not the cards row

                // Kick off any data we still need; re-enter when each arrives.
                var pending = [];
                if (!spBlotterData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/propertyts/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spBlotterData = d; })
                );
                if (!spCommercialData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/commercial/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spCommercialData = d; })
                );
                if (!spTradesData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/trading/client', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spTradesData = d; })
                );

                var stormSel = document.getElementById('sp-storm-select');
                var sid = stormSel ? stormSel.value : '';
                if (sid && (!spCommercialImpact || spCommercialImpact._storm_id !== sid)) {
                    pending.push(
                        fetch(getBaseUrl() + '/api/v1/commercial/' + sid + '/portfolio-impact', {mode:'cors'})
                            .then(function(r){return r.json();})
                            .then(function(d){
                                if (d.status === 'success') {
                                    d._storm_id = sid;
                                    spCommercialImpact = d;
                                }
                            })
                            .catch(function(){ /* leave spCommercialImpact null */ })
                    );
                }

                if (pending.length) {
                    container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">Building report card...</div>';
                    Promise.all(pending).then(_renderSummary);
                } else {
                    _renderSummary();
                }
            }

            function _renderSummary() {
                var container = document.getElementById('sp-table-container');

                // Pull aggregates --------------------------------------------
                var rp = (spData && spData.portfolio) || {};
                var cp = (spCommercialImpact && spCommercialImpact.portfolio) || {};
                var ts = (spTradesData && spTradesData.trader_summary) || {};

                var propAffected = rp.properties_affected || 0;
                var propTotal    = rp.total_properties || (spBlotterData ? (spBlotterData.summary || {}).num_properties || 0 : 0);
                var comAffected  = cp.assets_affected || 0;
                var comTotal     = cp.total_assets || (spCommercialData ? (spCommercialData.summary || {}).num_assets || 0 : 0);

                var floodLoss = (rp.total_damage || 0) + (cp.total_damage || 0);
                var windLoss  = null;  // pending wind model

                var impairedRes = rp.mortgages_in_negative_equity || 0;
                var impairedCom = cp.loans_in_negative_equity || 0;

                var trades = (spTradesData && spTradesData.trades) || [];
                var totalNotional = ts.total_notional_sold || 0;
                var totalNpv = 0;
                trades.forEach(function(t) { totalNpv += (t.npv || 0); });

                var net = (windLoss != null ? -(floodLoss + windLoss) : -floodLoss) + totalNpv;

                // Build report-card layout ----------------------------------
                var stormSel = document.getElementById('sp-storm-select');
                var stormLabel = (stormSel && stormSel.selectedIndex >= 0)
                    ? stormSel.options[stormSel.selectedIndex].textContent
                    : '\u2014';

                container.innerHTML = '';
                container.style.padding = '16px';
                container.style.overflowY = 'auto';

                var cardStyle = 'background:white;border:1px solid #e0e0e0;border-radius:8px;padding:14px 16px;';
                var labelStyle = 'font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin-bottom:4px;';
                var bigValStyle = 'font-size:22px;font-weight:700;';
                var smallStyle = 'font-size:11px;color:#555;margin-top:2px;';

                // Report-card HTML -------------------------------------------
                var html = '';
                html += '<div style="font-size:11px;color:#888;margin-bottom:6px;">Report card for storm</div>';
                html += '<div style="font-size:14px;font-weight:600;color:#222;margin-bottom:16px;">' + stormLabel + '</div>';

                // Row 1: assets affected
                html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;">';
                html += '<div style="' + cardStyle + 'border-left:3px solid #1976d2;">'
                      +  '<div style="' + labelStyle + '">Properties Affected</div>'
                      +  '<div style="' + bigValStyle + 'color:#1976d2;">' + propAffected + ' <span style="font-size:13px;color:#888;font-weight:400;">/ ' + propTotal + '</span></div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid #1976d2;">'
                      +  '<div style="' + labelStyle + '">Commercials Affected</div>'
                      +  '<div style="' + bigValStyle + 'color:#1976d2;">' + comAffected + ' <span style="font-size:13px;color:#888;font-weight:400;">/ ' + comTotal + '</span></div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid ' + ((impairedRes + impairedCom) > 0 ? '#d32f2f' : '#388e3c') + ';">'
                      +  '<div style="' + labelStyle + '">Impaired Mortgages</div>'
                      +  '<div style="' + bigValStyle + 'color:' + ((impairedRes + impairedCom) > 0 ? '#d32f2f' : '#388e3c') + ';">' + (impairedRes + impairedCom) + '</div>'
                      +  '<div style="' + smallStyle + '">' + impairedRes + ' residential / ' + impairedCom + ' commercial</div>'
                      + '</div>';
                html += '</div>';

                // Row 2: loss types
                html += '<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin:18px 0 6px 0;">Aggregate Losses</div>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;">';
                html += '<div style="' + cardStyle + 'border-left:3px solid #d32f2f;">'
                      +  '<div style="' + labelStyle + '">Flood Damage</div>'
                      +  '<div style="' + bigValStyle + 'color:#d32f2f;">' + fmtGBP(floodLoss) + '</div>'
                      +  '<div style="' + smallStyle + '">Residential ' + fmtGBP(rp.total_damage || 0) + ' + Commercial ' + fmtGBP(cp.total_damage || 0) + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid #d32f2f;">'
                      +  '<div style="' + labelStyle + '">Wind Damage</div>'
                      +  '<div style="' + bigValStyle + 'color:#999;">' + (windLoss != null ? fmtGBP(windLoss) : '\u2014') + '</div>'
                      +  '<div style="' + smallStyle + '">Model pending</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid #d32f2f;">'
                      +  '<div style="' + labelStyle + '">Total Loss (Gross)</div>'
                      +  '<div style="' + bigValStyle + 'color:#d32f2f;">' + fmtGBP(floodLoss + (windLoss || 0)) + '</div>'
                      + '</div>';
                html += '</div>';

                // Row 3: hedges
                html += '<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#888;margin:18px 0 6px 0;">PRS Hedges</div>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;">';
                html += '<div style="' + cardStyle + 'border-left:3px solid #7b1fa2;">'
                      +  '<div style="' + labelStyle + '">Trades Live</div>'
                      +  '<div style="' + bigValStyle + 'color:#7b1fa2;">' + (ts.num_trades || trades.length) + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid #7b1fa2;">'
                      +  '<div style="' + labelStyle + '">Total Notional</div>'
                      +  '<div style="' + bigValStyle + 'color:#7b1fa2;">' + fmtGBP(totalNotional) + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid ' + (totalNpv >= 0 ? '#2e7d32' : '#c62828') + ';">'
                      +  '<div style="' + labelStyle + '">Hedge NPV (REIT)</div>'
                      +  '<div style="' + bigValStyle + 'color:' + (totalNpv >= 0 ? '#2e7d32' : '#c62828') + ';">' + fmtGBP(totalNpv) + '</div>'
                      + '</div>';
                html += '</div>';

                // Net line
                html += '<div style="margin-top:18px;padding:14px 16px;border-radius:8px;background:' + (net >= 0 ? '#e8f5e9' : '#ffebee') + ';border-left:4px solid ' + (net >= 0 ? '#2e7d32' : '#c62828') + ';">';
                html += '<div style="' + labelStyle + '">Net Portfolio P&L (gross loss + hedge NPV)</div>';
                html += '<div style="font-size:24px;font-weight:700;color:' + (net >= 0 ? '#2e7d32' : '#c62828') + ';">' + fmtGBP(net) + '</div>';
                html += '</div>';

                container.innerHTML = html;
            }
