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

            function _psRenderSeverityTab(result) {
                var content = document.getElementById('ps-content');
                if (!content) return;

                var gauges = result.gauges || [];

                var severeGauges  = gauges.filter(function(g) { return g.threshold === 'severe' && g.num_trades > 0; });
                var warningGauges = gauges.filter(function(g) { return g.threshold === 'warning' && g.num_trades > 0; });
                var alertGauges   = gauges.filter(function(g) { return g.threshold === 'alert' && g.num_trades > 0; });
                var cleanGauges   = gauges.filter(function(g) {
                    return g.threshold === 'clean' && g.num_trades > 0;
                });

                var sections = [
                    {
                        label: 'SEVERE',
                        gauges: severeGauges,
                        bg: 'var(--danger-bg-soft)',
                        headerBg: 'var(--red-dark)',
                        dotColor: 'var(--red-dark)',
                        emptyMsg: 'No gauges at severe level'
                    },
                    {
                        label: 'WARNING',
                        gauges: warningGauges,
                        bg: 'var(--warn-bg-warm)',
                        headerBg: 'var(--amber-deep)',
                        dotColor: 'var(--amber-deep)',
                        emptyMsg: 'No gauges at warning level'
                    },
                    {
                        label: 'ALERT',
                        gauges: alertGauges,
                        bg: 'var(--warn-bg)',
                        headerBg: 'var(--gold-deep)',
                        dotColor: 'var(--gold-deep)',
                        emptyMsg: 'No gauges at alert level'
                    },
                    {
                        label: 'CLEAN',
                        gauges: cleanGauges,
                        bg: 'var(--sunken)',
                        headerBg: 'var(--text-4)',
                        dotColor: 'var(--faint)',
                        emptyMsg: 'No trades at clean gauges'
                    }
                ];

                var html = '<div style="overflow-y:auto;height:100%;padding:var(--space-6) var(--space-8);">';

                sections.forEach(function(section) {
                    var count = section.gauges.length;
                    if (count === 0) return;  // skip empty sections entirely

                    html +=
                        '<div style="margin-bottom:var(--space-8);">' +
                        '<div style="display:flex;align-items:center;gap:var(--space-4);padding:var(--space-3) var(--space-6);' +
                        'background:' + section.headerBg + ';color:var(--inverse);border-radius:var(--radius-4) var(--radius-4) 0 0;">' +
                        '<span style="font-size:var(--size-sm);font-weight:700;">' + section.label + '</span>' +
                        '<span style="font-size:var(--size-xs);opacity:0.85;">— ' + count + ' gauge' + (count !== 1 ? 's' : '') + '</span>' +
                        '</div>' +
                        '<div style="border:1px solid var(--line-strong);border-top:none;border-radius:0 0 var(--radius-4) var(--radius-4);background:' + section.bg + ';overflow:hidden;">';

                    {
                        section.gauges.forEach(function(g) {
                            var pnlColor = g.stress_pnl >= 0 ? 'var(--green-dark)' : 'var(--red-dark)';
                            html +=
                                '<div style="display:flex;align-items:center;gap:var(--space-5);padding:var(--space-4) var(--space-7);border-bottom:1px solid var(--grid-line);">' +
                                '<span style="width:10px;height:10px;border-radius:50%;background:' + section.dotColor + ';display:inline-block;flex-shrink:0;"></span>' +
                                '<span style="font-size:var(--size-xs);font-weight:600;color:var(--text);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' +
                                g.gauge_name + '</span>' +
                                '<span style="font-size:var(--size-xxs);color:var(--text-2);white-space:nowrap;min-width:80px;text-align:right;">' +
                                'P(flood): <b>' + g.p_flood_pct.toFixed(1) + '%</b>' +
                                '</span>' +
                                '<span style="font-size:var(--size-xxs);color:var(--text-2);white-space:nowrap;min-width:60px;text-align:right;">' +
                                g.num_trades + ' trade' + (g.num_trades !== 1 ? 's' : '') +
                                '</span>' +
                                '<span style="font-size:var(--size-xxs);font-weight:700;color:' + pnlColor + ';white-space:nowrap;min-width:80px;text-align:right;">' +
                                fmtGBP(g.stress_pnl) + '</span>' +
                                (g.num_trades > 0 ?
                                    '<button data-gaugeid="' + g.gauge_id + '" class="ps-sev-gauge-btn" style="padding:var(--space-1) var(--space-4);font-size:var(--size-xxs);background:var(--accent);color:var(--inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;white-space:nowrap;">' +
                                    '→ Gauge P&amp;L</button>'
                                    : '<span style="min-width:72px;"></span>') +
                                '</div>';
                        });
                    }

                    html += '</div></div>';
                });

                html += '</div>';
                content.innerHTML = html;

                // Bind severity "Gauge P&L" buttons via event delegation
                content.querySelectorAll('.ps-sev-gauge-btn').forEach(function(btn) {
                    btn.addEventListener('click', function() {
                        psSelectedGaugeId = this.getAttribute('data-gaugeid');
                        psSwitchSubTab('gaugepnl');
                    });
                });
            }
