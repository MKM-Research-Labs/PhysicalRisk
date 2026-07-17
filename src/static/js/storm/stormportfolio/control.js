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
