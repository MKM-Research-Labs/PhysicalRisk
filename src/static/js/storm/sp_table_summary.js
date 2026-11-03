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
                if (sid && (!spHedgeData || spHedgeData.storm_id !== sid)) {
                    pending.push(fetchHedgeData(sid).catch(function(){ /* leave spHedgeData as is */ }));
                }
                if (sid && (!spWindData || spWindData.storm_id !== sid)) {
                    pending.push(
                        fetch(getBaseUrl() + '/api/v1/propertyts/' + sid + '/wind-impact', {mode:'cors'})
                            .then(function(r){return r.json();})
                            .then(function(d){ if (d.status === 'success') spWindData = d; })
                            .catch(function(){ /* leave spWindData as is */ })
                    );
                }
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
                    container.innerHTML = '<div style="padding:var(--space-10);text-align:center;color:var(--muted-2);">Building report card...</div>';
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

                // Wind: the typhoon paired with this storm, if any. The wind
                // model covers residential properties only.
                var stormSelW = document.getElementById('sp-storm-select');
                var wd = (spWindData && stormSelW && spWindData.storm_id === stormSelW.value) ? spWindData : null;
                var hasTyphoon = !!(wd && wd.typhoon);
                var windLoss  = wd ? ((wd.summary || {}).total_wind_damage || 0) : null;
                var windNote  = !wd ? 'Not loaded'
                    : (hasTyphoon ? '⚡ ' + (wd.typhoon.event_id || '') + ' — residential only' : 'No typhoon paired with this storm');

                var impairedRes = rp.mortgages_in_negative_equity || 0;
                var impairedCom = cp.loans_in_negative_equity || 0;

                // Hedges: what the REIT's gauge hedges pay in this storm
                var stormSel0 = document.getElementById('sp-storm-select');
                var hd = (spHedgeData && stormSel0 && spHedgeData.storm_id === stormSel0.value) ? spHedgeData : null;
                var reit = (hd && hd.reit) || {};
                var numHedges = reit.num_hedges != null ? reit.num_hedges : (ts.num_trades || 0);
                var hedgePayout = reit.total_payout || 0;
                var deskNet = (hd && hd.desk) ? hd.desk.net : null;

                var net = (windLoss != null ? -(floodLoss + windLoss) : -floodLoss) + hedgePayout;

                // Build report-card layout ----------------------------------
                var stormSel = document.getElementById('sp-storm-select');
                var stormLabel = (stormSel && stormSel.selectedIndex >= 0)
                    ? stormSel.options[stormSel.selectedIndex].textContent
                    : '\u2014';

                container.innerHTML = '';
                container.style.padding = '16px';
                container.style.overflowY = 'auto';

                var cardStyle = 'background:var(--panel);border:1px solid var(--line);border-radius:var(--radius-lg);padding:var(--space-7) var(--space-8);';
                var labelStyle = 'font-size:var(--size-xxs);text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);margin-bottom:var(--space-2);';
                var bigValStyle = 'font-size:22px;font-weight:700;';
                var smallStyle = 'font-size:var(--size-xs);color:var(--text-2);margin-top:var(--space-1);';

                // Report-card HTML -------------------------------------------
                var html = '';
                html += '<div style="font-size:var(--size-xs);color:var(--muted);margin-bottom:var(--space-3);">Report card for storm</div>';
                html += '<div style="font-size:var(--size-14);font-weight:600;color:var(--text);margin-bottom:var(--space-8);">' + stormLabel + '</div>';

                // Row 1: assets affected
                html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-6);margin-bottom:var(--space-6);">';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--accent);">'
                      +  '<div style="' + labelStyle + '">Properties Affected</div>'
                      +  '<div style="' + bigValStyle + 'color:var(--accent);">' + propAffected + ' <span style="font-size:var(--size-md);color:var(--muted);font-weight:400;">/ ' + propTotal + '</span></div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--accent);">'
                      +  '<div style="' + labelStyle + '">Commercials Affected</div>'
                      +  '<div style="' + bigValStyle + 'color:var(--accent);">' + comAffected + ' <span style="font-size:var(--size-md);color:var(--muted);font-weight:400;">/ ' + comTotal + '</span></div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid ' + ((impairedRes + impairedCom) > 0 ? 'var(--red)' : 'var(--green)') + ';">'
                      +  '<div style="' + labelStyle + '">Impaired Mortgages</div>'
                      +  '<div style="' + bigValStyle + 'color:' + ((impairedRes + impairedCom) > 0 ? 'var(--red)' : 'var(--green)') + ';">' + (impairedRes + impairedCom) + '</div>'
                      +  '<div style="' + smallStyle + '">' + impairedRes + ' residential / ' + impairedCom + ' commercial</div>'
                      + '</div>';
                html += '</div>';

                // Row 2: loss types
                html += '<div style="font-size:var(--size-xs);text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);margin:var(--space-9) 0 var(--space-3) 0;">Aggregate Losses</div>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-6);margin-bottom:var(--space-6);">';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--red);">'
                      +  '<div style="' + labelStyle + '">Flood Damage</div>'
                      +  '<div style="' + bigValStyle + 'color:var(--red);">' + fmtGBP(floodLoss) + '</div>'
                      +  '<div style="' + smallStyle + '">Residential ' + fmtGBP(rp.total_damage || 0) + ' + Commercial ' + fmtGBP(cp.total_damage || 0) + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--red);">'
                      +  '<div style="' + labelStyle + '">Wind Damage</div>'
                      +  '<div style="' + bigValStyle + 'color:' + (windLoss ? 'var(--red)' : 'var(--muted-2)') + ';">' + (windLoss ? fmtGBP(windLoss) : '\u2014') + '</div>'
                      +  '<div style="' + smallStyle + '">' + windNote + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--red);">'
                      +  '<div style="' + labelStyle + '">Total Loss (Gross)</div>'
                      +  '<div style="' + bigValStyle + 'color:var(--red);">' + fmtGBP(floodLoss + (windLoss || 0)) + '</div>'
                      + '</div>';
                html += '</div>';

                // Row 3: hedges
                html += '<div style="font-size:var(--size-xs);text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);margin:var(--space-9) 0 var(--space-3) 0;">REIT Hedges</div>';
                html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-6);margin-bottom:var(--space-6);">';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--purple);">'
                      +  '<div style="' + labelStyle + '">Hedges Triggered</div>'
                      +  '<div style="' + bigValStyle + 'color:var(--purple);">' + (reit.num_triggered || 0) + ' <span style="font-size:var(--size-md);color:var(--muted);font-weight:400;">/ ' + numHedges + '</span></div>'
                      +  '<div style="' + smallStyle + '">Notional ' + fmtGBP(reit.total_notional || 0) + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid var(--green-dark);">'
                      +  '<div style="' + labelStyle + '">Hedge Payout to REIT</div>'
                      +  '<div style="' + bigValStyle + 'color:var(--green-dark);">' + fmtGBP(hedgePayout) + '</div>'
                      +  '<div style="' + smallStyle + '">' + (floodLoss > 0 ? 'Covers ' + Math.round(hedgePayout / floodLoss * 100) + '% of the flood loss' : 'Paid when the trigger gauge reaches severe') + '</div>'
                      + '</div>';
                html += '<div style="' + cardStyle + 'border-left:3px solid ' + ((deskNet || 0) >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">'
                      +  '<div style="' + labelStyle + '">Market-Maker Net</div>'
                      +  '<div style="' + bigValStyle + 'color:' + ((deskNet || 0) >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">' + (deskNet == null ? '\u2014' : _hMoney(deskNet)) + '</div>'
                      +  '<div style="' + smallStyle + '">After lay-off and other gauge trades</div>'
                      + '</div>';
                html += '</div>';

                // Net line
                html += '<div style="margin-top:var(--space-9);padding:var(--space-7) var(--space-8);border-radius:var(--radius-lg);background:' + (net >= 0 ? 'var(--ok-bg)' : 'var(--danger-bg-soft)') + ';border-left:4px solid ' + (net >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">';
                html += '<div style="' + labelStyle + '">Net Portfolio P&amp;L (gross loss + hedge payout)</div>';
                html += '<div style="font-size:var(--size-24);font-weight:700;color:' + (net >= 0 ? 'var(--green-dark)' : 'var(--red-dark)') + ';">' + fmtGBP(net) + '</div>';
                html += '</div>';

                container.innerHTML = html;
            }
