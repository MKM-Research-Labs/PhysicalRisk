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

"""Property hazard curve — Hazard Curve tab (event count summary)."""


def get_js():
    """Return JS fragment for hazard curve tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // Tab 0: Hazard Curve — Event Count Summary
            // ================================================================
            function renderHazardCurve() {
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                var severe = (phcData.depth_thresholds || {}).severe || {};
                var annualProb = severe.annual_probability || 0;
                var returnPeriod = severe.return_period_yrs;
                var floodCount = phcData.flood_count || 0;
                var summary = phcData.summary || {};
                var zone = phcData.flood_zone || '';
                var spreadBps = ((phcData.term_structure || {}).severe || {}).prs_spread_bps;
                var spread = spreadBps ? spreadBps[0] : 0;

                var rpStr = returnPeriod ? (returnPeriod.toFixed(0) + ' yr') : '\\u221E';

                var container = document.getElementById('phc-chart-container');
                container.innerHTML =
                    '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:20px;padding:30px;">' +
                    '<div style="text-align:center;">' +
                    '<p style="font-size:14px;color:#888;margin-bottom:4px;">Monte Carlo Event Count</p>' +
                    '<p style="font-size:48px;font-weight:bold;color:#1976D2;margin:0;">' + spread.toFixed(1) + ' <span style="font-size:20px;">bp</span></p>' +
                    '<p style="font-size:13px;color:#666;margin-top:4px;">' + floodCount + ' severe floods / 20,000 scenarios</p>' +
                    '</div>' +
                    '<div style="display:flex;gap:40px;font-size:13px;">' +
                    '<div style="text-align:center;"><span style="color:#888;">Zone</span><br><b style="font-size:16px;">' + zone + '</b></div>' +
                    '<div style="text-align:center;"><span style="color:#888;">Annual Prob</span><br><b style="font-size:16px;">' + (annualProb * 100).toFixed(3) + '%</b></div>' +
                    '<div style="text-align:center;"><span style="color:#888;">Return Period</span><br><b style="font-size:16px;">' + rpStr + '</b></div>' +
                    '<div style="text-align:center;"><span style="color:#888;">Max Depth</span><br><b style="font-size:16px;">' + (summary.max_depth_m || 0).toFixed(2) + 'm</b></div>' +
                    '<div style="text-align:center;"><span style="color:#888;">Mean Depth</span><br><b style="font-size:16px;">' + (summary.mean_depth_m || 0).toFixed(2) + 'm</b></div>' +
                    '<div style="text-align:center;"><span style="color:#888;">Transmission</span><br><b style="font-size:16px;">' + ((summary.flood_transmission_rate || 0) * 100).toFixed(1) + '%</b></div>' +
                    '</div>' +
                    '</div>';

                var bar = document.getElementById('phc-stats-bar');
                bar.innerHTML = [
                    '<span style="color:#1976D2;font-weight:bold;">Event Count</span>',
                    '<span><b>Zone:</b> ' + zone + '</span>',
                    '<span><b>Floods:</b> ' + floodCount + '</span>',
                    '<span><b>Spread:</b> <span style="color:#1976D2;">' + spread.toFixed(1) + ' bp</span></span>'
                ].join('');
            }
"""
