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

"""
Trading Desk startup preloader.

When the Pi button is clicked, shows a progress popup listing all datasets
being fetched in parallel.  Each row gets a tick (✓) when its fetch
resolves.  Once all fetches settle, the popup closes and the main panel
opens with pre-populated data.

Datasets preloaded (stored on window._td* variables):
  _tdPreBlotter      — /api/v1/trading/blotter
  _tdPreMarket       — /api/v1/trading/market-state
  _tdPreGauges       — /api/v1/gauges
  _tdPreStressStorms — /api/v1/trading/stress/storms
  _tdPrePortStorms   — /api/v1/trading/stress/portfolio-storms
  _tdPreEodHistory   — /api/v1/trading/eod/history
  _tdPreYieldCurve   — /api/v1/trading/yield-curve
  _tdPreGovDocs      — /api/v1/governance/documents
"""


def get_js() -> str:
    """Return the JS fragment for the preloader popup and prefetch logic."""
    return """
            // ==============================================================
            // Trading desk preloader — fallback if global startup not done
            // ==============================================================
            // Cache vars and _tdPreloadDone are declared by the global startup
            // preloader (startup.py) which runs on DOMContentLoaded.
            // This block only runs if the user opens the Pi panel before the
            // page-load preloader finishes (extremely rare race condition).

            // Dataset definitions: [key, label, endpoint]
            var _tdDatasets = [
                ['_tdPreBlotter',      'Blotter trades',         '/api/v1/trading/blotter'],
                ['_tdPreMarket',       'Market state',           '/api/v1/trading/market-state'],
                ['_tdPreGauges',       'Gauge locations',        '/api/v1/gauges'],
                ['_tdPreStressStorms', 'Stress scenarios',       '/api/v1/trading/stress/storms'],
                ['_tdPrePortStorms',   'Portfolio storms',       '/api/v1/trading/stress/portfolio-storms'],
                ['_tdPreEodHistory',   'EOD history',            '/api/v1/trading/eod/history'],
                ['_tdPreYieldCurve',   'Yield curve',            '/api/v1/trading/yield-curve'],
                ['_tdPreGovDocs',      'Regulatory documents',   '/api/v1/governance/documents']
            ];

            function _tdCreatePreloaderPopup() {
                var existing = document.getElementById('td-preloader-popup');
                if (existing) existing.remove();

                var popup = document.createElement('div');
                popup.id = 'td-preloader-popup';
                popup.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'background:white;border:1px solid #ddd;border-radius:10px;' +
                    'box-shadow:0 8px 32px rgba(0,0,0,0.2);z-index:3000;' +
                    'min-width:340px;padding:24px 28px;font-family:Arial,sans-serif;';

                var title = document.createElement('div');
                title.style.cssText = 'font-size:15px;font-weight:bold;color:#1565c0;' +
                    'margin-bottom:16px;display:flex;align-items:center;gap:8px;';
                title.innerHTML =
                    '<span style="font-size:20px;font-family:serif;">&Pi;</span>' +
                    ' Loading Trading Desk\u2026';
                popup.appendChild(title);

                // Progress bar
                var barWrap = document.createElement('div');
                barWrap.style.cssText =
                    'background:#f0f0f0;border-radius:4px;height:6px;' +
                    'margin-bottom:16px;overflow:hidden;';
                var bar = document.createElement('div');
                bar.id = 'td-pre-bar';
                bar.style.cssText =
                    'height:100%;width:0%;background:#1976d2;' +
                    'transition:width 0.3s ease;border-radius:4px;';
                barWrap.appendChild(bar);
                popup.appendChild(barWrap);

                // Dataset rows
                var list = document.createElement('div');
                list.id = 'td-pre-list';
                list.style.cssText = 'display:flex;flex-direction:column;gap:6px;';
                _tdDatasets.forEach(function(ds) {
                    var row = document.createElement('div');
                    row.id = 'td-pre-row-' + ds[0];
                    row.style.cssText =
                        'display:flex;align-items:center;gap:10px;' +
                        'font-size:12px;color:#555;';
                    var icon = document.createElement('span');
                    icon.id = 'td-pre-icon-' + ds[0];
                    icon.style.cssText =
                        'width:16px;height:16px;border-radius:50%;' +
                        'border:2px solid #ccc;display:inline-block;flex-shrink:0;' +
                        'animation:td-spin 0.8s linear infinite;';
                    var label = document.createElement('span');
                    label.textContent = ds[1];
                    row.appendChild(icon);
                    row.appendChild(label);
                    list.appendChild(row);
                });
                popup.appendChild(list);

                // Spinner keyframes (injected once)
                if (!document.getElementById('td-pre-style')) {
                    var style = document.createElement('style');
                    style.id = 'td-pre-style';
                    style.textContent =
                        '@keyframes td-spin {' +
                        '  0%{border-top-color:#1976d2;transform:rotate(0deg);}' +
                        '  100%{border-top-color:#1976d2;transform:rotate(360deg);}' +
                        '}';
                    document.head.appendChild(style);
                }

                document.body.appendChild(popup);
                return popup;
            }

            function _tdMarkPreloadItem(key, ok, detail) {
                var icon = document.getElementById('td-pre-icon-' + key);
                if (!icon) return;
                icon.style.animation = 'none';
                if (ok) {
                    icon.style.cssText =
                        'width:16px;height:16px;border-radius:50%;display:inline-flex;' +
                        'align-items:center;justify-content:center;font-size:11px;flex-shrink:0;' +
                        'background:#e8f5e9;color:#2e7d32;border:2px solid #a5d6a7;';
                    icon.textContent = '\u2713';
                    // Append detail count next to label
                    if (detail) {
                        var row = document.getElementById('td-pre-row-' + key);
                        if (row) {
                            var det = document.createElement('span');
                            det.style.cssText = 'color:#999;font-size:11px;margin-left:auto;';
                            det.textContent = detail;
                            row.appendChild(det);
                        }
                    }
                } else {
                    icon.style.cssText =
                        'width:16px;height:16px;border-radius:50%;display:inline-flex;' +
                        'align-items:center;justify-content:center;font-size:11px;flex-shrink:0;' +
                        'background:#ffebee;color:#c62828;border:2px solid #ef9a9a;';
                    icon.textContent = '\u2717';
                }
            }

            function _tdUpdatePreloadBar(done, total) {
                var bar = document.getElementById('td-pre-bar');
                if (bar) bar.style.width = Math.round(100 * done / total) + '%';
            }

            function _tdRunPreload(onDone) {
                var baseUrl = getBaseUrl();
                var popup = _tdCreatePreloaderPopup();
                var settled = 0;
                var total = _tdDatasets.length;

                function _detail(key, data) {
                    if (key === '_tdPreBlotter' && data && data.trades)
                        return data.trades.length + ' trades';
                    if (key === '_tdPreStressStorms' && data && data.storms)
                        return data.storms.length + ' scenarios';
                    if (key === '_tdPrePortStorms' && data && data.storms)
                        return data.storms.length + ' storms';
                    if (key === '_tdPreGauges' && data && data.gauges)
                        return data.gauges.length + ' gauges';
                    if (key === '_tdPreGovDocs' && data && data.documents)
                        return data.documents.length + ' docs';
                    return null;
                }

                _tdDatasets.forEach(function(ds) {
                    var key = ds[0], endpoint = ds[2];
                    fetch(baseUrl + endpoint, {mode: 'cors'})
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            window[key] = data;
                            _tdMarkPreloadItem(key, true, _detail(key, data));
                        })
                        .catch(function() {
                            _tdMarkPreloadItem(key, false, null);
                        })
                        .finally(function() {
                            settled++;
                            _tdUpdatePreloadBar(settled, total);
                            if (settled === total) {
                                window._tdPreloadDone = true;
                                setTimeout(function() {
                                    popup.remove();
                                    onDone();
                                }, 400);
                            }
                        });
                });
            }
"""
