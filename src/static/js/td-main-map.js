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

(function() {
    var fs01Layer = null;
    var fs01StyleAdded = false;

    function findMainMap() {
        var mapKey = Object.keys(window).find(function(k) { return k.startsWith('map_'); });
        return mapKey ? window[mapKey] : null;
    }

    function getBaseUrl() {
        var cfg = window.__BACKEND_CONFIG || {};
        return cfg.url || '';
    }

    function fmtGBP(v) {
        if (v == null || v === 0) return '\u2014';
        var sign = v < 0 ? '-' : '';
        var abs = Math.abs(v);
        var cc = (window.__BACKEND_CONFIG || {}).currency || 'GBP';
        var sym = {GBP: '\u00a3', USD: '$', EUR: '\u20ac'}[cc] || (cc + ' ');
        return sign + sym + abs.toLocaleString('en-GB', {minimumFractionDigits: 0, maximumFractionDigits: 0});
    }

    function extractArea(name) {
        if (!name) return '';
        return name;
    }

    function addFS01Style() {
        if (fs01StyleAdded) return;
        fs01StyleAdded = true;
        var style = document.createElement('style');
        style.textContent =
            '.fs01-main-label { ' +
            'background: transparent !important; ' +
            'border: none !important; ' +
            'box-shadow: none !important; ' +
            'font-size: 10px !important; ' +
            'font-weight: 600 !important; ' +
            'color: #333 !important; ' +
            'padding: 0 !important; ' +
            '}' +
            '.fs01-main-label::before { display: none !important; }';
        document.head.appendChild(style);
    }

    function loadFS01Circles() {
        var map = findMainMap();
        if (!map) return;

        var url = getBaseUrl();
        if (!url) return;

        fetch(url + '/api/v1/trading/trade-map', {mode: 'cors'})
            .then(function(r) { return r.json(); })
            .then(function(result) {
                if (result.status !== 'success') return;
                renderFS01Circles(map, result.gauges || []);
            })
            .catch(function(err) {
                console.log('[FS01 Main] No trading data available');
            });
    }

    function renderFS01Circles(map, gauges) {
        // Remove previous layer
        if (fs01Layer) {
            map.removeLayer(fs01Layer);
            fs01Layer = null;
        }

        if (gauges.length === 0) return;

        addFS01Style();
        fs01Layer = L.layerGroup();

        // First pass: find max |FS01| for area-proportional scaling
        var maxAbsFs01 = 0;
        for (var mi = 0; mi < gauges.length; mi++) {
            var av = Math.abs(gauges[mi].net_fs01 || 0);
            if (av > maxAbsFs01) maxAbsFs01 = av;
        }

        for (var i = 0; i < gauges.length; i++) {
            var g = gauges[i];
            if (!g.lat || !g.lon) continue;

            var fs01 = g.net_fs01 || 0;
            var color = fs01 >= 0 ? '#1565c0' : '#c62828';
            var absFs01 = Math.abs(fs01);
            var radius = maxAbsFs01 > 0
                ? Math.max(6, Math.sqrt(absFs01 / maxAbsFs01) * 30)
                : 6;
            var areaName = extractArea(g.gauge_name || g.gauge_id);

            // FS01-by-tenor breakdown
            var tenorRows = '';
            if (g.fs01_by_tenor) {
                var tenorKeys = Object.keys(g.fs01_by_tenor);
                for (var ti = 0; ti < tenorKeys.length; ti++) {
                    var tv = g.fs01_by_tenor[tenorKeys[ti]];
                    var tc = tv >= 0 ? '#1565c0' : '#c62828';
                    tenorRows += '<tr><td style="padding:1px 4px;color:#666;">' + tenorKeys[ti] + '</td>' +
                        '<td style="padding:1px 4px;text-align:right;color:' + tc + ';font-weight:600;">' + fmtGBP(tv) + '</td></tr>';
                }
            }

            var dailyPnl = g.daily_pnl || 0;
            var dColor = dailyPnl >= 0 ? '#2e7d32' : '#c62828';

            var popup =
                '<div style="font-size:11px;min-width:180px;">' +
                    '<b style="font-size:12px;">' + areaName + '</b><br>' +
                    '<span style="color:#888;font-size:10px;">' + g.gauge_id + '</span><br>' +
                    '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                    '<div style="display:flex;justify-content:space-between;"><span>Trades:</span><b>' + g.num_trades + '</b></div>' +
                    '<div style="display:flex;justify-content:space-between;"><span>Notional:</span><b>' + fmtGBP(g.total_notional) + '</b></div>' +
                    '<div style="display:flex;justify-content:space-between;"><span>Net FS01:</span><span style="color:' + color + ';font-weight:bold;">' + fmtGBP(fs01) + '</span></div>' +
                    (tenorRows ? '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;"><div style="font-size:10px;font-weight:600;color:#555;margin-bottom:2px;">FS01 by Tenor</div><table style="width:100%;font-size:10px;">' + tenorRows + '</table>' : '') +
                    '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                    '<div style="display:flex;justify-content:space-between;"><span>Daily P&amp;L:</span><span style="color:' + dColor + ';font-weight:600;">' + fmtGBP(dailyPnl) + '</span></div>' +
                    '<hr style="margin:4px 0;border:0;border-top:1px solid #eee;">' +
                    '<a href="#" onclick="event.preventDefault();window.showGaugeBlotter&&window.showGaugeBlotter(\'' + g.gauge_id + '\',\'' + (g.gauge_name || '').replace(/\'/g, "\\\'") + '\')" ' +
                        'style="color:#1565c0;font-size:10px;">View Gauge Blotter \u2192</a>' +
                '</div>';

            var circle = L.circleMarker([g.lat, g.lon], {
                radius: radius,
                fillColor: color,
                color: color,
                weight: 3,
                fillOpacity: 0.15
            }).bindPopup(popup);

            circle.bindTooltip(areaName, {
                permanent: true,
                direction: 'top',
                offset: [0, -radius - 2],
                className: 'fs01-main-label'
            });

            fs01Layer.addLayer(circle);
        }

        fs01Layer.addTo(map);
    }

    // Expose refresh function globally
    window.refreshMainMapFS01 = loadFS01Circles;

    // Listen for gauge layer toggle — hide/show FS01 circles to match
    function watchGaugeLayer(map) {
        map.on('overlayremove', function(e) {
            if (e.name === 'Flood Gauges' && fs01Layer && map.hasLayer(fs01Layer)) {
                map.removeLayer(fs01Layer);
            }
        });
        map.on('overlayadd', function(e) {
            if (e.name === 'Flood Gauges' && fs01Layer && !map.hasLayer(fs01Layer)) {
                fs01Layer.addTo(map);
            }
        });
    }

    // Load circles after a delay (server needs to be ready)
    function tryLoad() {
        var map = findMainMap();
        var url = getBaseUrl();
        if (map && url) {
            watchGaugeLayer(map);
            loadFS01Circles();
        } else {
            setTimeout(tryLoad, 2000);
        }
    }
    setTimeout(tryLoad, 3000);
})();
