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

(function () {
    var PANEL_ID = 'cdm-review-panel';
    var panel = null;
    var iframe = null;
    var expanded = false;

    var DEFAULT_CSS = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
        'width:90vw;max-width:1200px;height:85vh;background:var(--panel);border-radius:var(--radius-lg);' +
        'box-shadow:var(--shadow-modal);z-index:2000;display:none;' +
        'flex-direction:column;font-family:Arial,Helvetica,sans-serif;overflow:hidden;';

    function buildPanel() {
        panel = document.createElement('div');
        panel.id = PANEL_ID;
        panel.style.cssText = DEFAULT_CSS;

        // Header — title + expand/close, matching the other workstream panels.
        var header = document.createElement('div');
        header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;' +
            'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);flex-shrink:0;';

        var title = document.createElement('span');
        title.textContent = 'CDM Asset Review';
        title.style.cssText = 'font-size:var(--size-14);font-weight:700;color:var(--text);';

        var actions = document.createElement('div');
        actions.style.cssText = 'display:flex;align-items:center;gap:var(--space-1);';

        var expandBtn = document.createElement('button');
        expandBtn.innerHTML = '&#x26F6;';
        expandBtn.title = 'Expand';
        expandBtn.style.cssText = 'border:none;background:none;font-size:var(--size-18);cursor:pointer;' +
            'color:var(--text-3);padding:0 var(--space-3);line-height:1;';
        expandBtn.onclick = function () { toggleExpand(expandBtn); };

        var closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Close';
        closeBtn.style.cssText = 'border:none;background:none;font-size:var(--size-24);cursor:pointer;' +
            'color:var(--text-3);padding:0 var(--space-4);line-height:1;';
        closeBtn.onclick = hidePanel;

        actions.appendChild(expandBtn);
        actions.appendChild(closeBtn);
        header.appendChild(title);
        header.appendChild(actions);

        // Body — the CDM Asset Review tool embedded in an iframe.
        var body = document.createElement('div');
        body.style.cssText = 'flex:1;overflow:hidden;';
        iframe = document.createElement('iframe');
        iframe.title = 'CDM Asset Review';
        iframe.style.cssText = 'width:100%;height:100%;border:none;display:block;';
        body.appendChild(iframe);

        panel.appendChild(header);
        panel.appendChild(body);
        document.body.appendChild(panel);
    }

    function showPanel() {
        if (!panel) buildPanel();
        // Lazy-load on first open.
        if (!iframe.getAttribute('src')) iframe.setAttribute('src', '/cdm-asset-review');
        panel.style.display = 'flex';
    }

    function hidePanel() {
        if (panel) panel.style.display = 'none';
    }

    function toggleExpand(btn) {
        expanded = !expanded;
        if (expanded) {
            panel.style.width = 'calc(100vw - 40px)';
            panel.style.maxWidth = 'none';
            panel.style.height = 'calc(100vh - 40px)';
            btn.innerHTML = '&#x2750;';
            btn.title = 'Restore';
        } else {
            panel.style.width = '90vw';
            panel.style.maxWidth = '1200px';
            panel.style.height = '85vh';
            btn.innerHTML = '&#x26F6;';
            btn.title = 'Expand';
        }
    }

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
                    'stroke="' + Theme.value('text') + '" stroke-width="2" ' +
                    'stroke-linecap="round" stroke-linejoin="round">' +
                    '<path d="M3 10.5L12 3l9 7.5"/>' +
                    '<path d="M5 9.5V21h14V9.5"/>' +
                    '<path d="M9.5 21v-6h5v6"/></svg>';
                btn.style.cssText = 'display:flex;align-items:center;justify-content:center;' +
                    'width:30px;height:30px;cursor:pointer;background:var(--panel);';

                L.DomEvent.disableClickPropagation(container);
                L.DomEvent.on(btn, 'click', function (e) {
                    L.DomEvent.preventDefault(e);
                    showPanel();
                });
                return container;
            }
        });

        new CdmReviewControl().addTo(map);
    }

    setTimeout(tryAdd, 1000);
})();
