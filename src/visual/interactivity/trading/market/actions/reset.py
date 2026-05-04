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

"""Market tab — yield and hazard curve reset handlers."""


def get_js() -> str:
    """Return JS fragment for tdResetCurve and tdResetGauge."""
    return """
            window.tdResetCurve = function() {
                if (tdCurveMode === 'yield') {
                    var url = getBaseUrl() + '/api/v1/trading/yield-curve/reset?_=' + Date.now();
                    window.__mkmAdminFetch(url, {method: 'POST', body: '{}', mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status === 'success') {
                            tdYieldCurve = result.yield_curve || {};
                            tdYieldDirty = false;
                            renderCurveChart();
                            if (window.showInfo) window.showInfo('Yield curve reset');
                        }
                    });
                } else {
                    var url = getBaseUrl() + '/api/v1/trading/hazard-term-structure/reset?_=' + Date.now();
                    var body = tdSelectedGauge ? {gauge_id: tdSelectedGauge} : {};
                    window.__mkmAdminFetch(url, {method: 'POST', body: JSON.stringify(body), mode: 'cors', cache: 'no-store'})
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        if (result.status === 'success') {
                            tdHazardDirtyKeys = {};
                            loadMarketData();
                            if (window.showInfo) window.showInfo(result.message);
                        }
                    });
                }
            };

            window.tdResetGauge = function(gaugeId) {
                var url = getBaseUrl() + '/api/v1/trading/market-state/reset?_=' + Date.now();
                window.__mkmAdminFetch(url, {method: 'POST', body: JSON.stringify({gauge_id: gaugeId}), mode: 'cors', cache: 'no-store'})
                .then(function(r) { return r.json(); })
                .then(function(result) {
                    if (result.status === 'success') {
                        if (window.showInfo) window.showInfo('Reset ' + gaugeId);
                        loadMarketData();
                    }
                });
            };
"""
