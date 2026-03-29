# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Leaflet map control button for opening the portfolio panel."""


def get_js() -> str:
    """Return JS for the Leaflet control button."""
    return """
            // ==============================================================
            // Map control button
            // ==============================================================
            function addMapControl() {
                function findMap() {
                    var mapKey = Object.keys(window).find(function(k) { return k.startsWith('map_'); });
                    if (mapKey) return window[mapKey];
                    return null;
                }

                function tryAdd() {
                    var map = findMap();
                    if (!map) {
                        setTimeout(tryAdd, 500);
                        return;
                    }

                    var PortfolioControl = L.Control.extend({
                        options: { position: 'topright' },
                        onAdd: function() {
                            var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                            var btn = L.DomUtil.create('a', '', container);
                            btn.href = '#';
                            btn.title = 'Portfolio Storm Impact';
                            btn.setAttribute('role', 'button');
                            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2"><path d="M2 12c1-3 3-5 5-5s3 2 5 2 3-2 5-2 4 2 5 5"/><path d="M2 17c1-3 3-5 5-5s3 2 5 2 3-2 5-2 4 2 5 5"/></svg>';
                            btn.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;cursor:pointer;background:white;';

                            L.DomEvent.disableClickPropagation(container);
                            L.DomEvent.on(btn, 'click', function(e) {
                                L.DomEvent.preventDefault(e);
                                showPanel();
                            });
                            return container;
                        }
                    });

                    new PortfolioControl().addTo(map);
                }

                setTimeout(tryAdd, 1000);
            }

            // Add map control button on load
            addMapControl();
"""
