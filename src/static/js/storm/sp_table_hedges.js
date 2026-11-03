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

            // Two sub-tabs on the REIT's gauge hedges with the market-maker:
            //  * Hedges — the hedge book itself (what the REIT bought, on
            //    which gauge, at what spread) and the desk's lay-off trades.
            //  * Hedge Payout — what those hedges pay in this storm, set
            //    against each asset's flood damage, and the market-maker's
            //    side (paid to the REIT, received on its lay-off and other
            //    gauge trades). A hedge pays when its gauge reaches severe.
            // Both read the same /hedges report, which lists every trade.
            var spHedgeData = null;  // last /hedges response (has storm_id)

            // Fetch the hedge report for a storm; reuses the cached one.
            function fetchHedgeData(sid) {
                if (spHedgeData && spHedgeData.storm_id === sid) {
                    return Promise.resolve(spHedgeData);
                }
                return fetch(getBaseUrl() + '/api/v1/propertyts/' + sid + '/hedges', {mode:'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.status === 'success') spHedgeData = d;
                        return d;
                    });
            }

            // Commercial flood impact for the storm (shared with Summary).
            function _fetchCommercialImpact(sid) {
                if (spCommercialImpact && spCommercialImpact._storm_id === sid) {
                    return Promise.resolve(spCommercialImpact);
                }
                return fetch(getBaseUrl() + '/api/v1/commercial/' + sid + '/portfolio-impact', {mode:'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.status === 'success') { d._storm_id = sid; spCommercialImpact = d; }
                        return d;
                    })
                    .catch(function() { return null; });
            }

            function loadHedgeBook() {
                var sid = (document.getElementById('sp-storm-select') || {}).value || '';
                var container = document.getElementById('sp-table-container');
                if (!sid) {
                    _renderHedgesEmpty('Select a storm to view the hedge book.');
                    return;
                }
                container.innerHTML = '<div style="padding:var(--space-10);text-align:center;color:var(--muted-2);">Loading hedge book…</div>';
                fetchHedgeData(sid)
                    .then(function(d) {
                        if (spTableSubTab !== 'hedges') return;  // user moved on
                        if (!d || d.status !== 'success') {
                            _renderHedgesEmpty((d && d.message) || 'Hedge book unavailable.');
                            return;
                        }
                        _renderHedgeBook(d);
                    })
                    .catch(function(err) {
                        console.error('Hedge book error:', err);
                        _renderHedgesEmpty('Failed to load the hedge book.');
                    });
            }

            function loadHedgePayout() {
                var sid = (document.getElementById('sp-storm-select') || {}).value || '';
                var container = document.getElementById('sp-table-container');
                if (!sid) {
                    _renderHedgesEmpty('Select a storm to view hedge payouts.');
                    return;
                }
                container.innerHTML = '<div style="padding:var(--space-10);text-align:center;color:var(--muted-2);">Loading hedge payouts…</div>';
                Promise.all([fetchHedgeData(sid), _fetchCommercialImpact(sid)])
                    .then(function(res) {
                        var d = res[0];
                        if (spTableSubTab !== 'payout') return;  // user moved on
                        if (!d || d.status !== 'success') {
                            _renderHedgesEmpty((d && d.message) || 'Hedge payouts unavailable.');
                            return;
                        }
                        _renderHedges(d);
                    })
                    .catch(function(err) {
                        console.error('Hedge payouts error:', err);
                        _renderHedgesEmpty('Failed to load hedge payouts.');
                    });
            }

            function _renderHedgesEmpty(msg) {
                document.getElementById('sp-summary').innerHTML = '';
                document.getElementById('sp-table-container').innerHTML =
                    '<div style="padding:48px 24px;text-align:center;color:var(--muted);font-size:var(--size-md);">' + _hEsc(msg) + '</div>';
            }

            function _hEsc(v) {
                return String(v == null ? '' : v).replace(/[&<>"]/g, function(c) {
                    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
                });
            }

            // Flood damage by asset id from the residential and commercial
            // impact responses already loaded for this storm.
            function _hedgeDamageByAsset() {
                var out = {};
                ((spData && spData.properties) || []).forEach(function(p) {
                    out[p.property_id] = p.damage_amount || 0;
                });
                ((spCommercialImpact && spCommercialImpact.assets) || []).forEach(function(a) {
                    out[a.property_id] = a.damage_amount || 0;
                });
                return out;
            }

            function _hMoney(v) {
                if (!v) return '—';
                var s = fmtGBP(Math.abs(v));
                return v < 0 ? '−' + s : s;
            }

            function _hSigned(v) {
                var colour = v > 0 ? 'var(--green-dark)' : (v < 0 ? 'var(--red-dark)' : 'var(--muted)');
                return '<span style="color:' + colour + ';font-weight:600;">' + (v ? (v > 0 ? '+' : '') + _hMoney(v) : '—') + '</span>';
            }

            function _hTable(cols, rows) {
                var th = 'padding:var(--space-3) var(--space-4);border-bottom:2px solid var(--line-strong);background:var(--raised);white-space:nowrap;font-size:var(--size-xxs);color:var(--text-2);position:sticky;top:0;';
                var html = '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);"><thead><tr>';
                cols.forEach(function(c) { html += '<th style="' + th + 'text-align:' + c.align + ';">' + c.label + '</th>'; });
                html += '</tr></thead><tbody>';
                rows.forEach(function(r, i) {
                    var bg = r._hit ? 'var(--ok-bg)' : (i % 2 ? 'var(--sunken)' : 'transparent');
                    html += '<tr style="background:' + bg + ';">';
                    cols.forEach(function(c) {
                        html += '<td style="padding:var(--space-3) var(--space-4);border-bottom:1px solid var(--line-soft);text-align:' + c.align + ';white-space:nowrap;">' + c.cell(r) + '</td>';
                    });
                    html += '</tr>';
                });
                return html + '</tbody></table>';
            }

            function _hSection(title, note) {
                return '<div style="padding:var(--space-6) var(--space-8) var(--space-3);font-size:var(--size-xs);text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);">' + title +
                    (note ? ' <span style="text-transform:none;letter-spacing:0;color:var(--muted-2);">— ' + note + '</span>' : '') + '</div>';
            }

            function _cards(cards) {
                var summary = document.getElementById('sp-summary');
                summary.innerHTML = '';
                cards.forEach(function(card) {
                    var div = document.createElement('div');
                    div.style.cssText = 'flex:1;min-width:120px;padding:var(--space-4) var(--space-6);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + card.color + ';';
                    div.innerHTML = '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;">' + card.label + '</div>' +
                        '<div style="font-size:var(--size-lg);font-weight:700;color:' + card.color + ';margin-top:var(--space-1);">' + card.value + '</div>' +
                        (card.note ? '<div style="font-size:var(--size-xxs);color:var(--text-2);margin-top:var(--space-1);">' + card.note + '</div>' : '');
                    summary.appendChild(div);
                });
            }

            function _bps(v) { return v == null ? '—' : (+v).toFixed(0) + ' bps'; }
            function _premium(r) { return (r.notional || 0) * (r.spread_bps || 0) / 10000; }

            // The hedge book: the REIT's protection bought from the
            // market-maker, and the desk's lay-off of it. Nothing here
            // depends on the storm; payouts are on the Hedge Payout tab.
            function _renderHedgeBook(d) {
                var reit = d.reit || {}, desk = d.desk || {};
                var hedges = (reit.hedges || []).slice().sort(function(a, b) { return b.notional - a.notional; });
                var layoffs = (desk.trades || []).filter(function(t) { return t.role === 'layoff'; })
                    .sort(function(a, b) { return b.notional - a.notional; });

                var notional = hedges.reduce(function(a, h) { return a + h.notional; }, 0);
                var value = hedges.reduce(function(a, h) { return a + (h.asset_value || 0); }, 0);
                var premium = hedges.reduce(function(a, h) { return a + _premium(h); }, 0);
                var mtm = hedges.reduce(function(a, h) { return a + (h.npv || 0); }, 0);
                var layoffNotional = layoffs.reduce(function(a, t) { return a + t.notional; }, 0);
                var nCom = hedges.filter(function(h) { return h.asset_class === 'commercial'; }).length;
                var reitName = hedges.length ? hedges[0].counterparty : 'REIT';

                _cards([
                    { label: 'REIT Hedges', value: hedges.length, color: 'var(--purple)',
                      note: (hedges.length - nCom) + ' residential / ' + nCom + ' commercial' },
                    { label: 'Hedged Notional', value: _hMoney(notional), color: 'var(--accent)',
                      note: value ? Math.round(notional / value * 100) + '% of ' + fmtGBP(value) + ' asset value' : '' },
                    { label: 'Annual Premium (REIT pays)', value: _hMoney(premium), color: 'var(--amber)',
                      note: notional ? _bps(premium / notional * 10000) + ' average' : '' },
                    { label: 'Pre-storm MTM (to REIT)', value: _hSigned(mtm), color: mtm >= 0 ? 'var(--green-dark)' : 'var(--red-dark)',
                      note: 'Model value today, before any storm' },
                    { label: 'Market-Maker Lay-off', value: _hMoney(layoffNotional), color: 'var(--teal, var(--accent))',
                      note: layoffs.length + ' trades, ' + (notional ? Math.round(layoffNotional / notional * 100) : 0) + '% of REIT notional' },
                ]);

                var html = _hSection('REIT hedge book', _hEsc(reitName) + ' buys flood protection from the market-maker; each hedge pays its notional when its gauge reaches severe');
                html += hedges.length ? _hTable([
                    { label: 'Trade', align: 'left', cell: function(r) { return _hEsc(r.swap_id); } },
                    { label: 'Asset', align: 'left', cell: function(r) { return _hEsc(r.asset_id); } },
                    { label: 'Class', align: 'left', cell: function(r) { return r.asset_class === 'commercial' ? 'Commercial' : 'Residential'; } },
                    { label: 'Address', align: 'left', cell: function(r) { return _hEsc(r.address) || '—'; } },
                    { label: 'Asset Value', align: 'right', cell: function(r) { return _hMoney(r.asset_value); } },
                    { label: 'Trigger Gauge', align: 'left', cell: function(r) { return _hEsc(r.gauge_name || r.gauge_id); } },
                    { label: 'Notional', align: 'right', cell: function(r) { return _hMoney(r.notional); } },
                    { label: 'Cover', align: 'right', cell: function(r) { return r.asset_value ? Math.round(r.notional / r.asset_value * 100) + '%' : '—'; } },
                    { label: 'Spread', align: 'right', cell: function(r) { return _bps(r.spread_bps); } },
                    { label: 'Annual Premium', align: 'right', cell: function(r) { return _hMoney(_premium(r)); } },
                    { label: 'MTM (to REIT)', align: 'right', cell: function(r) { return _hSigned(r.npv || 0); } },
                    { label: 'Maturity', align: 'left', cell: function(r) { return _hEsc(r.end_date) || '—'; } },
                ], hedges) : '<div style="padding:var(--space-6) var(--space-8);color:var(--muted-2);">The REIT has no hedges in this book.</div>';

                html += _hSection('Market-maker lay-off', 'the desk buys back part of the REIT risk on each gauge from other counterparties');
                html += layoffs.length ? _hTable([
                    { label: 'Trade', align: 'left', cell: function(r) { return _hEsc(r.swap_id); } },
                    { label: 'Counterparty', align: 'left', cell: function(r) { return _hEsc(r.counterparty); } },
                    { label: 'Gauge', align: 'left', cell: function(r) { return _hEsc(r.gauge_name || r.gauge_id); } },
                    { label: 'Desk Side', align: 'left', cell: function(r) { return r.payer ? 'Bought protection' : 'Sold protection'; } },
                    { label: 'Notional', align: 'right', cell: function(r) { return _hMoney(r.notional); } },
                    { label: 'Spread', align: 'right', cell: function(r) { return _bps(r.spread_bps); } },
                    { label: 'Maturity', align: 'left', cell: function(r) { return _hEsc(r.end_date) || '—'; } },
                ], layoffs) : '<div style="padding:var(--space-6) var(--space-8);color:var(--muted-2);">No lay-off trades in the book.</div>';

                document.getElementById('sp-table-container').innerHTML = html;
            }

            function _renderHedges(d) {
                var reit = d.reit || {}, desk = d.desk || {};
                var damage = _hedgeDamageByAsset();
                var hedges = (reit.hedges || []).map(function(h) {
                    var dmg = damage[h.asset_id] || 0;
                    return Object.assign({}, h, {damage: dmg, net: h.payout - dmg, _hit: h.triggered});
                });
                var hedgedDamage = hedges.reduce(function(a, h) { return a + h.damage; }, 0);
                var reitNet = (reit.total_payout || 0) - hedgedDamage;

                // Cards
                var cards = [
                    { label: 'Hedges Triggered', value: (reit.num_triggered || 0) + ' / ' + (reit.num_hedges || 0), color: 'var(--purple)' },
                    { label: 'REIT Payout', value: _hMoney(reit.total_payout || 0), color: 'var(--green-dark)' },
                    { label: 'Damage on Hedged Assets', value: _hMoney(hedgedDamage), color: 'var(--red)' },
                    { label: 'REIT Net (payout − damage)', value: _hSigned(reitNet), color: reitNet >= 0 ? 'var(--green-dark)' : 'var(--red-dark)' },
                    { label: 'Market-Maker Net', value: _hSigned(desk.net || 0), color: (desk.net || 0) >= 0 ? 'var(--green-dark)' : 'var(--red-dark)' },
                ];
                _cards(cards);

                var tick = function(r) { return r.triggered ? '<span style="color:var(--green-dark);font-weight:700;">✓ Severe</span>' : '<span style="color:var(--muted-2);">No</span>'; };
                var peak = function(r) { return r.gauge_peak_m == null ? '—' : r.gauge_peak_m.toFixed(2) + ' m'; };

                var html = _hSection('REIT hedges', 'bought from the market-maker; each pays its notional when its gauge reaches severe');
                html += hedges.length ? _hTable([
                    { label: 'Asset', align: 'left', cell: function(r) { return _hEsc(r.asset_id); } },
                    { label: 'Class', align: 'left', cell: function(r) { return r.asset_class === 'commercial' ? 'Commercial' : 'Residential'; } },
                    { label: 'Address', align: 'left', cell: function(r) { return _hEsc(r.address) || '—'; } },
                    { label: 'Trigger Gauge', align: 'left', cell: function(r) { return _hEsc(r.gauge_name || r.gauge_id); } },
                    { label: 'Gauge Peak', align: 'right', cell: peak },
                    { label: 'Triggered', align: 'left', cell: tick },
                    { label: 'Notional', align: 'right', cell: function(r) { return _hMoney(r.notional); } },
                    { label: 'Flood Damage', align: 'right', cell: function(r) { return _hMoney(r.damage); } },
                    { label: 'Payout', align: 'right', cell: function(r) { return _hSigned(r.payout); } },
                    { label: 'Net', align: 'right', cell: function(r) { return _hSigned(r.net); } },
                ], hedges) : '<div style="padding:var(--space-6) var(--space-8);color:var(--muted-2);">The REIT has no hedges in this book.</div>';

                var deskRows = (desk.trades || []).filter(function(t) { return t.role === 'layoff' || t.triggered; })
                    .map(function(t) { return Object.assign({}, t, {_hit: t.triggered && t.cash > 0}); });
                html += _hSection('Market-maker', 'pays the REIT, then recovers through its lay-off and other gauge trades');
                html += '<div style="display:flex;gap:var(--space-8);flex-wrap:wrap;padding:0 var(--space-8) var(--space-4);font-size:var(--size-xs);color:var(--text-2);">' +
                    '<span>Paid to REIT: <b>' + _hSigned(desk.paid_to_reit || 0) + '</b></span>' +
                    '<span>Lay-off trades: <b>' + _hSigned(desk.layoff_cash || 0) + '</b></span>' +
                    '<span>Other gauge trades: <b>' + _hSigned(desk.book_cash || 0) + '</b></span>' +
                    '<span>Net: <b>' + _hSigned(desk.net || 0) + '</b></span></div>';
                html += deskRows.length ? _hTable([
                    { label: 'Trade', align: 'left', cell: function(r) { return _hEsc(r.swap_id); } },
                    { label: 'Role', align: 'left', cell: function(r) { return r.role === 'layoff' ? 'Lay-off of REIT risk' : 'Gauge book'; } },
                    { label: 'Counterparty', align: 'left', cell: function(r) { return _hEsc(r.counterparty); } },
                    { label: 'Gauge', align: 'left', cell: function(r) { return _hEsc(r.gauge_name || r.gauge_id); } },
                    { label: 'Desk Side', align: 'left', cell: function(r) { return r.payer ? 'Bought protection' : 'Sold protection'; } },
                    { label: 'Gauge Peak', align: 'right', cell: peak },
                    { label: 'Triggered', align: 'left', cell: tick },
                    { label: 'Notional', align: 'right', cell: function(r) { return _hMoney(r.notional); } },
                    { label: 'Cash to Desk', align: 'right', cell: function(r) { return _hSigned(r.cash); } },
                ], deskRows) : '<div style="padding:var(--space-6) var(--space-8);color:var(--muted-2);">No market-maker trades triggered.</div>';

                var container = document.getElementById('sp-table-container');
                container.innerHTML = html;
            }
