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

"""Port Stress — Severity breakdown sub-tab."""


def get_js() -> str:
    """Return JavaScript fragment for the Severity sub-tab."""
    return """
            // ---- Port Stress: Severity Sub-Tab ----
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
                        bg: '#ffebee',
                        headerBg: '#c62828',
                        dotColor: '#c62828',
                        emptyMsg: 'No gauges at severe level'
                    },
                    {
                        label: 'WARNING',
                        gauges: warningGauges,
                        bg: '#fff3e0',
                        headerBg: '#e65100',
                        dotColor: '#e65100',
                        emptyMsg: 'No gauges at warning level'
                    },
                    {
                        label: 'ALERT',
                        gauges: alertGauges,
                        bg: '#fffde7',
                        headerBg: '#f9a825',
                        dotColor: '#f9a825',
                        emptyMsg: 'No gauges at alert level'
                    },
                    {
                        label: 'CLEAN',
                        gauges: cleanGauges,
                        bg: '#f5f5f5',
                        headerBg: '#757575',
                        dotColor: '#bdbdbd',
                        emptyMsg: 'No trades at clean gauges'
                    }
                ];

                var html = '<div style="overflow-y:auto;height:100%;padding:12px 16px;">';

                sections.forEach(function(section) {
                    var count = section.gauges.length;
                    if (count === 0) return;  // skip empty sections entirely

                    html +=
                        '<div style="margin-bottom:16px;">' +
                        '<div style="display:flex;align-items:center;gap:8px;padding:6px 12px;' +
                        'background:' + section.headerBg + ';color:white;border-radius:4px 4px 0 0;">' +
                        '<span style="font-size:12px;font-weight:700;">' + section.label + '</span>' +
                        '<span style="font-size:11px;opacity:0.85;">\u2014 ' + count + ' gauge' + (count !== 1 ? 's' : '') + '</span>' +
                        '</div>' +
                        '<div style="border:1px solid #ddd;border-top:none;border-radius:0 0 4px 4px;background:' + section.bg + ';overflow:hidden;">';

                    {
                        section.gauges.forEach(function(g) {
                            var pnlColor = g.stress_pnl >= 0 ? '#2e7d32' : '#c62828';
                            html +=
                                '<div style="display:flex;align-items:center;gap:10px;padding:7px 14px;border-bottom:1px solid rgba(0,0,0,0.06);">' +
                                '<span style="width:10px;height:10px;border-radius:50%;background:' + section.dotColor + ';display:inline-block;flex-shrink:0;"></span>' +
                                '<span style="font-size:11px;font-weight:600;color:#333;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' +
                                g.gauge_name + '</span>' +
                                '<span style="font-size:10px;color:#555;white-space:nowrap;min-width:80px;text-align:right;">' +
                                'P(flood): <b>' + g.p_flood_pct.toFixed(1) + '%</b>' +
                                '</span>' +
                                '<span style="font-size:10px;color:#555;white-space:nowrap;min-width:60px;text-align:right;">' +
                                g.num_trades + ' trade' + (g.num_trades !== 1 ? 's' : '') +
                                '</span>' +
                                '<span style="font-size:10px;font-weight:700;color:' + pnlColor + ';white-space:nowrap;min-width:80px;text-align:right;">' +
                                fmtGBP(g.stress_pnl) + '</span>' +
                                (g.num_trades > 0 ?
                                    '<button data-gaugeid="' + g.gauge_id + '" class="ps-sev-gauge-btn" style="padding:2px 8px;font-size:9px;background:#1976d2;color:white;border:none;border-radius:3px;cursor:pointer;white-space:nowrap;">' +
                                    '\u2192 Gauge P&amp;L</button>'
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
"""
