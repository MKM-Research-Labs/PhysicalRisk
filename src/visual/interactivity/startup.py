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
Global page-load startup preloader.

Runs on DOMContentLoaded and pre-fetches ALL data needed across every panel:
storms, trader data, governance documents, gauge locations.  Shows a centered
progress popup with a spinner-to-tick row per dataset.

Panels consume the pre-fetched data via window._pre* cache variables so that
opening any panel for the first time is instant (no waiting for a fetch).

Datasets pre-fetched:
  _tdPreBlotter      — /api/v1/trading/blotter
  _tdPreMarket       — /api/v1/trading/market-state       (label: Hazard curves)
  _tdPreGauges       — /api/v1/gauges
  _tdPreStressStorms — /api/v1/trading/stress/storms
  _tdPrePortStorms   — /api/v1/trading/stress/portfolio-storms
  _tdPreEodHistory   — /api/v1/trading/eod/history
  _tdPreYieldCurve   — /api/v1/trading/yield-curve
  _tdPreGovDocs      — /api/v1/governance/documents
  _preStorms         — /api/v1/propertyts/storms
  _preGovAudit       — /api/v1/governance/audit-trail?limit=200
  _preGovBib         — /api/v1/governance/bibliography
  _prePropertyTS     — /api/v1/propertyts/summary
  _preGaugeHist      — /api/v1/gauges/history/summary
"""


class StartupPreloader:
    """Adds the global page-load preloader to a Folium map."""

    def add_to_map(self, folium_map) -> None:
        import folium as _folium
        folium_map.get_root().html.add_child(_folium.Element(
            f"<script>\n(function(){{\n{_get_preloader_js()}\n}})();\n</script>"
        ))


def _get_preloader_js() -> str:
    """Return the JS body for the global startup preloader (no wrapping IIFE)."""
    return get_js()


def get_js() -> str:
    """Return JS fragment for the global startup preloader."""
    return """
            // ==============================================================
            // Global startup preloader — runs on DOMContentLoaded
            // Pre-fetches all panel data so every panel opens instantly
            // ==============================================================

            // Cache variables — shared with trading/preloader.py
            // (if the trading desk preloader runs first it will find these)
            window._tdPreBlotter      = null;
            window._tdPreMarket       = null;
            window._tdPreGauges       = null;
            window._tdPreStressStorms = null;
            window._tdPrePortStorms   = null;
            window._tdPreEodHistory   = null;
            window._tdPreYieldCurve   = null;
            window._tdPreGovDocs      = null;
            window._preStorms         = null;
            window._preGovAudit       = null;
            window._preGovBib         = null;
            window._prePropertyTS     = null;
            window._preGaugeHist      = null;
            window._preMortgages      = null;

            // Flag read by trading/preloader.py — on window so it is accessible
            // from any IIFE scope (var declaration would be local to this IIFE)
            window._tdPreloadDone = false;

            // All datasets: [cacheKey, displayLabel, endpoint]
            var _startupDatasets = [
                ['_tdPreBlotter',      'Blotter trades',       '/api/v1/trading/blotter'],
                ['_tdPreMarket',       'Hazard curves',        '/api/v1/trading/market-state'],
                ['_tdPreGauges',       'Gauge locations',      '/api/v1/gauges'],
                ['_tdPreStressStorms', 'Stress scenarios',     '/api/v1/trading/stress/storms'],
                ['_tdPrePortStorms',   'Portfolio storms',     '/api/v1/trading/stress/portfolio-storms'],
                ['_tdPreEodHistory',   'EOD history',          '/api/v1/trading/eod/history'],
                ['_tdPreYieldCurve',   'Yield curve',          '/api/v1/trading/yield-curve'],
                ['_tdPreGovDocs',      'Regulatory documents', '/api/v1/governance/documents'],
                ['_preStorms',         'Storm scenarios',      '/api/v1/propertyts/storms'],
                ['_preGovAudit',       'Audit trail',          '/api/v1/governance/audit-trail?limit=200'],
                ['_preGovBib',         'Bibliography',         '/api/v1/governance/bibliography'],
                ['_prePropertyTS',     'Property flood TS',    '/api/v1/propertyts/summary'],
                ['_preGaugeHist',      'Gauge history',        '/api/v1/gauges/history/summary'],
                ['_preMortgages',      'Mortgages',            '/api/v1/mortgages'],
            ];

            function _startupDetail(key, data) {
                if (!data) return null;
                if (key === '_tdPreBlotter'      && data.trades)       return data.trades.length + ' trades';
                if (key === '_tdPreMarket'        && data.gauges)       return Object.keys(data.gauges).length + ' gauges';
                if (key === '_tdPreGauges'        && data.gauges)       return data.gauges.length + ' gauges';
                if (key === '_tdPreStressStorms'  && data.storms)       return data.storms.length + ' scenarios';
                if (key === '_tdPrePortStorms'    && data.storms)       return data.storms.length + ' storms';
                if (key === '_tdPreEodHistory'    && data.history)      return data.history.length + ' snapshots';
                if (key === '_tdPreYieldCurve'    && data.yield_curve)  return Object.keys(data.yield_curve).length + ' tenors';
                if (key === '_tdPreGovDocs'       && data.documents)    return data.documents.length + ' docs';
                if (key === '_preStorms'          && data.storms)       return data.storms.length + ' storms';
                if (key === '_preGovAudit'        && data.events)       return data.events.length + ' events';
                if (key === '_preGovBib'          && data.references)   return data.references.length + ' refs';
                if (key === '_prePropertyTS'      && data.data && data.data.summary) return data.data.summary.total_properties + ' properties';
                if (key === '_preGaugeHist'       && data.count != null) return data.count + ' gauges';
                if (key === '_preMortgages'       && data.mortgages)     return data.mortgages.length + ' mortgages';
                return null;
            }

            function _createStartupPopup() {
                var popup = document.createElement('div');
                popup.id = 'startup-preloader-popup';
                popup.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'background:white;border:1px solid #ddd;border-radius:10px;' +
                    'box-shadow:0 8px 32px rgba(0,0,0,0.2);z-index:9999;' +
                    'min-width:360px;padding:24px 28px;font-family:Arial,sans-serif;';

                var title = document.createElement('div');
                title.style.cssText =
                    'font-size:15px;font-weight:bold;color:#1565c0;' +
                    'margin-bottom:16px;display:flex;align-items:center;gap:8px;';
                title.innerHTML =
                    '<span style="font-size:20px;">&#9651;</span>' +
                    ' Loading MKM Research Platform\u2026';
                popup.appendChild(title);

                // Overall progress bar
                var barWrap = document.createElement('div');
                barWrap.style.cssText =
                    'background:#f0f0f0;border-radius:4px;height:6px;' +
                    'margin-bottom:16px;overflow:hidden;';
                var bar = document.createElement('div');
                bar.id = 'startup-pre-bar';
                bar.style.cssText =
                    'height:100%;width:0%;background:#1976d2;' +
                    'transition:width 0.3s ease;border-radius:4px;';
                barWrap.appendChild(bar);
                popup.appendChild(barWrap);

                // Dataset rows — two columns
                var grid = document.createElement('div');
                grid.style.cssText =
                    'display:grid;grid-template-columns:1fr 1fr;gap:5px 16px;';

                _startupDatasets.forEach(function(ds) {
                    var row = document.createElement('div');
                    row.id = 'startup-row-' + ds[0];
                    row.style.cssText =
                        'display:flex;align-items:center;gap:8px;font-size:11px;color:#555;';
                    var icon = document.createElement('span');
                    icon.id = 'startup-icon-' + ds[0];
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;' +
                        'border:2px solid #ccc;display:inline-block;flex-shrink:0;' +
                        'animation:startup-spin 0.8s linear infinite;';
                    var label = document.createElement('span');
                    label.textContent = ds[1];
                    row.appendChild(icon);
                    row.appendChild(label);
                    grid.appendChild(row);
                });
                popup.appendChild(grid);

                // Spinner keyframes
                if (!document.getElementById('startup-pre-style')) {
                    var style = document.createElement('style');
                    style.id = 'startup-pre-style';
                    style.textContent =
                        '@keyframes startup-spin {' +
                        '  0%{border-top-color:#1976d2;transform:rotate(0deg);}' +
                        '  100%{border-top-color:#1976d2;transform:rotate(360deg);}' +
                        '}';
                    document.head.appendChild(style);
                }

                document.body.appendChild(popup);
                return popup;
            }

            function _startupMarkItem(key, ok, detail) {
                var icon = document.getElementById('startup-icon-' + key);
                if (!icon) return;
                icon.style.animation = 'none';
                if (ok) {
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;display:inline-flex;' +
                        'align-items:center;justify-content:center;font-size:10px;flex-shrink:0;' +
                        'background:#e8f5e9;color:#2e7d32;border:2px solid #a5d6a7;';
                    icon.textContent = '\u2713';
                    if (detail) {
                        var row = document.getElementById('startup-row-' + key);
                        if (row) {
                            var det = document.createElement('span');
                            det.style.cssText = 'color:#aaa;font-size:10px;margin-left:auto;';
                            det.textContent = detail;
                            row.appendChild(det);
                        }
                    }
                } else {
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;display:inline-flex;' +
                        'align-items:center;justify-content:center;font-size:10px;flex-shrink:0;' +
                        'background:#fff3e0;color:#e65100;border:2px solid #ffcc80;';
                    icon.textContent = '\u2013';
                }
            }

            function _runStartupPreload() {
                var baseUrl = (window.__BACKEND_CONFIG || {}).url || '';
                var popup = _createStartupPopup();
                var settled = 0;
                var total = _startupDatasets.length;

                _startupDatasets.forEach(function(ds) {
                    var key = ds[0], endpoint = ds[2];
                    fetch(baseUrl + endpoint, {mode: 'cors'})
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            window[key] = data;
                            _startupMarkItem(key, true, _startupDetail(key, data));
                        })
                        .catch(function() {
                            _startupMarkItem(key, false, null);
                        })
                        .finally(function() {
                            settled++;
                            var bar = document.getElementById('startup-pre-bar');
                            if (bar) bar.style.width = Math.round(100 * settled / total) + '%';
                            if (settled === total) {
                                // Mark trading desk preload as done — it uses the same cache vars
                                window._tdPreloadDone = true;
                                setTimeout(function() { popup.remove(); }, 600);
                            }
                        });
                });
            }

            // Fire on DOMContentLoaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', _runStartupPreload);
            } else {
                // Already loaded (script injected late)
                _runStartupPreload();
            }
"""
