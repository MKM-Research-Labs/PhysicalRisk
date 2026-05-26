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
// Context menu functionality for interactive map markers.

(function(root) {
    'use strict';

    function createContextMenuHandler(config) {
        config = config || {};
        var MENUS = {
            property: config.property || [],
            gauge: config.gauge || []
        };

        var currentId = null;
        var currentType = null;
        var currentDisplayName = null;
        var gaugesWithTrades = null; // null = not yet loaded; {} = loaded (may be empty)

        function createMenu(menuId, items, displayName) {
            var doc = root.document;
            var menu = doc.getElementById(menuId);
            if (menu) menu.remove();

            menu = doc.createElement('div');
            menu.id = menuId;
            menu.className = 'ctx-menu';

            // Header row with display name
            if (displayName) {
                var header = doc.createElement('div');
                header.className = 'ctx-menu-header';
                header.textContent = displayName;
                menu.appendChild(header);
            }

            items.forEach(function(item) {
                var el = doc.createElement('div');
                // Disable "Gauge Blotter" item when the current gauge has no open trades
                var isDisabled = item.id === 'gauge_blotter'
                    && gaugesWithTrades !== null
                    && !gaugesWithTrades[currentId];
                el.className = isDisabled
                    ? 'ctx-menu-item ctx-menu-item-disabled'
                    : 'ctx-menu-item';
                el.innerHTML = item.label;
                if (!isDisabled) {
                    el.onclick = function() {
                        if (item.action && root[item.action]) {
                            root[item.action](currentId, currentDisplayName);
                        }
                        hideMenu(menuId);
                    };
                }
                menu.appendChild(el);
            });

            doc.body.appendChild(menu);
            return menu;
        }

        function showMenu(e, id, type, displayName) {
            e.preventDefault();
            e.stopPropagation();

            currentId = id;
            currentType = type;
            currentDisplayName = displayName || null;

            var menuId = type + '-context-menu';
            var items = MENUS[type] || [];

            // Always recreate so header updates with current name
            var menu = createMenu(menuId, items, displayName);

            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            menu.style.display = 'block';
        }

        function hideMenu(menuId) {
            var menu = root.document.getElementById(menuId);
            if (menu) menu.style.display = 'none';
        }

        function hideAllMenus() {
            hideMenu('property-context-menu');
            hideMenu('gauge-context-menu');
            hideMenu('commercial-context-menu');
        }

        // Hide all menus on document click
        root.document.addEventListener('click', hideAllMenus);

        function extractId(content, pattern) {
            if (!content) return null;
            var str = typeof content === 'string' ? content :
                     (content.innerHTML || content.textContent || content.toString());
            var match = str.match(pattern);
            return match ? match[1].trim() : null;
        }

        function extractShortName(content, type) {
            // Extract a short display name from marker tooltip/popup content.
            // The shape of the tooltip differs per asset class, so we branch
            // on the resolved type — passing the wrong patterns at a tooltip
            // can otherwise capture stray hex chars and present them as
            // titles.
            if (!content) return null;
            var str = typeof content === 'string' ? content :
                     (content.innerHTML || content.textContent || content.toString());
            // Strip HTML tags
            str = str.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

            if (type === 'commercial') {
                // Commercial tooltip format:
                //   "{commercial_name} ({CommercialType})[ | Loan]"
                // We surface the name part as the menu title — fall back to
                // the CommercialType if no name is present.
                var commMatch = str.match(/^(.+?)\s*\(([^)]+)\)/);
                if (commMatch) {
                    var name = commMatch[1].trim();
                    if (name && !name.startsWith('CPROP-')) return name;
                    return commMatch[2].trim();  // fall back to CommercialType
                }
                return null;
            }

            // Property tooltip format: "Property: PROP-xxxxxxxx | Floods: ..."
            var propMatch = str.match(/Property:\s*(PROP-[a-f0-9]+)/);
            if (propMatch) return propMatch[1];

            // Gauge tooltip: text before "GAUGE-xxx" (Thames-prefixed area
            // names with _Point_N suffix).
            var gaugeMatch = str.match(/([A-Za-z][A-Za-z\s_]+?)(?:\s*[\|,]|\s+GAUGE-)/);
            if (gaugeMatch) {
                var gname = gaugeMatch[1].trim();
                var pi = gname.indexOf('_Point');
                if (pi > 0) gname = gname.substring(0, pi);
                gname = gname.replace(/^Thames\s+/i, '');
                if (gname.length > 0) return gname;
            }
            return null;
        }

        function initializeMenus() {
            var mapKey = Object.keys(root).find(function(k) { return k.startsWith('map_'); });
            var map = mapKey ? root[mapKey] : (typeof root.mapInstance !== 'undefined' ? root.mapInstance : null);

            if (!map) {
                console.log('Map not ready, retrying...');
                setTimeout(initializeMenus, 500);
                return;
            }

            var propCount = 0, gaugeCount = 0;

            function addMenusToMarkers() {
                map.eachLayer(function(layer) {
                    if (!(layer instanceof L.Marker) || layer._hasContextMenu) return;

                    var tooltip = layer.getTooltip && layer.getTooltip();
                    var popup = layer.getPopup && layer.getPopup();
                    var content = (tooltip && tooltip.getContent()) || (popup && popup.getContent()) || '';

                    var id = null, type = null;

                    // Order matters: CPROP- ids would substring-match the
                    // PROP- regex, so check commercial first.
                    id = extractId(content, /(CPROP-[a-f0-9]+)/);
                    if (id) type = 'commercial';

                    if (!id) {
                        id = extractId(content, /Property:\s*([^|<]+)/) || extractId(content, /(PROP-[a-f0-9]+)/);
                        if (id) type = 'property';
                    }

                    if (!id) {
                        id = extractId(content, /(GAUGE-[a-f0-9]+)/) || extractId(content, /Gauge:\s*([^|<]+)/);
                        if (id) type = 'gauge';
                    }

                    if (id && type) {
                        var name = extractShortName(content, type);
                        (function(boundId, boundType, boundName) {
                            layer.on('contextmenu', function(e) { showMenu(e.originalEvent, boundId, boundType, boundName); });
                        })(id, type, name);
                        layer._hasContextMenu = true;
                        layer._markerId = id;
                        layer._markerType = type;

                        if (type === 'property') propCount++;
                        else if (type === 'commercial') propCount++;
                        else gaugeCount++;
                    }
                });
            }

            addMenusToMarkers();
            map.on('layeradd', function() { setTimeout(addMenusToMarkers, 100); });

            // Pre-fetch which gauges have open trades so we can disable empty blotter items
            if (root.fetch) {
                root.fetch('/api/v1/trading/blotter/active-gauges')
                    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
                    .then(function(data) {
                        gaugesWithTrades = {};
                        var ids = (data && data.gauge_ids) ? data.gauge_ids : [];
                        ids.forEach(function(gid) { gaugesWithTrades[gid] = true; });
                    })
                    .catch(function() {
                        // On any error, leave gaugesWithTrades = null so all items stay enabled
                        gaugesWithTrades = null;
                    });
            }

            console.log('Context menus: ' + propCount + ' properties, ' + gaugeCount + ' gauges');
        }

        function getCurrentId() { return currentId; }
        function getCurrentType() { return currentType; }

        function setActiveGauges(gaugeIds) {
            gaugesWithTrades = {};
            (gaugeIds || []).forEach(function(gid) { gaugesWithTrades[gid] = true; });
        }

        return {
            createMenu: createMenu,
            showMenu: showMenu,
            hideMenu: hideMenu,
            hideAllMenus: hideAllMenus,
            extractId: extractId,
            extractShortName: extractShortName,
            initializeMenus: initializeMenus,
            getCurrentId: getCurrentId,
            getCurrentType: getCurrentType,
            setActiveGauges: setActiveGauges
        };
    }

    // Node.js / Jest export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { createContextMenuHandler: createContextMenuHandler };
    }

    // Browser auto-init
    if (typeof root !== 'undefined' && root.document && root.__MENU_CONFIG) {
        var api = createContextMenuHandler(root.__MENU_CONFIG);

        if (root.document.readyState === 'loading') {
            root.document.addEventListener('DOMContentLoaded', function() { setTimeout(api.initializeMenus, 1000); });
        } else {
            setTimeout(api.initializeMenus, 1000);
        }
        root.setActiveGauges = api.setActiveGauges;
        if (root.console) root.console.log('Context menus initialized');
    }

})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
