// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
// (see package __init__.py for full license text)
//
// Map control button for the CDM Asset Review workstream — a house icon that
// sits in the top-right control stack (directly below the Pi / Trader's
// Workstation icon) and opens the CDM Asset Review tool. Mirrors the
// Trader's Workstation control (trading/tradingdesk/panel_create.js).

(function () {
    function findMap() {
        var mapKey = Object.keys(window).find(function (k) { return k.startsWith('map_'); });
        return mapKey ? window[mapKey] : null;
    }

    function tryAdd() {
        var map = findMap();
        if (!map) {
            setTimeout(tryAdd, 500);
            return;
        }

        var CdmReviewControl = L.Control.extend({
            options: { position: 'topright' },
            onAdd: function () {
                var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                var btn = L.DomUtil.create('a', '', container);
                btn.href = '#';
                btn.title = 'CDM Asset Review';
                btn.setAttribute('role', 'button');
                // Plain house icon (placeholder).
                btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" ' +
                    'stroke="#333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                    '<path d="M3 10.5L12 3l9 7.5"/>' +
                    '<path d="M5 9.5V21h14V9.5"/>' +
                    '<path d="M9.5 21v-6h5v6"/></svg>';
                btn.style.cssText = 'display:flex;align-items:center;justify-content:center;' +
                    'width:30px;height:30px;cursor:pointer;background:white;';

                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.on(btn, 'click', function (e) {
                    L.DomEvent.preventDefault(e);
                    window.open('/cdm-asset-review', '_blank');
                });
                return container;
            }
        });

        new CdmReviewControl().addTo(map);
    }

    setTimeout(tryAdd, 1000);
})();
