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

            function createControlView() {
                var view = document.createElement('div');
                view.id = 'sp-control-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Top toolbar
                var toolbar = document.createElement('div');
                toolbar.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#f5f7fa;flex-shrink:0;';
                toolbar.innerHTML =
                    '<span style="font-size:12px;font-weight:700;color:#333;">Storm Sequence Control</span>' +
                    '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;background:#fff3e0;' +
                        'color:#c62828;border:1px solid #ef9a9a;border-radius:10px;font-size:9px;font-weight:700;' +
                        'letter-spacing:0.5px;text-transform:uppercase;" title="Changes here affect every storm ' +
                        'calculation across the platform. Admin password required to save or reset.">' +
                        '\ud83d\udd12 Admin Only</span>' +
                    '<span id="sp-ctrl-dirty" style="font-size:10px;color:#e65100;font-weight:600;display:none;">Unsaved changes</span>' +
                    '<span style="flex:1;"></span>' +
                    '<button id="sp-ctrl-guide-btn" style="padding:4px 12px;font-size:11px;font-weight:600;border:1px solid #1565c0;border-radius:3px;background:#e3f2fd;color:#1565c0;cursor:pointer;">User Guide</button>' +
                    '<button id="sp-ctrl-reset-btn" title="Admin password required" style="padding:4px 12px;font-size:11px;font-weight:600;border:1px solid #999;border-radius:3px;background:#f5f5f5;color:#555;cursor:pointer;">Reset Defaults</button>' +
                    '<button id="sp-ctrl-save-btn" title="Admin password required" style="padding:4px 14px;font-size:11px;font-weight:600;border:1px solid #1565c0;border-radius:3px;background:#1565c0;color:white;cursor:pointer;">Save &amp; Apply</button>';
                toolbar.querySelector('#sp-ctrl-guide-btn').onclick = function() { openControlGuide(); };
                toolbar.querySelector('#sp-ctrl-reset-btn').onclick = function() { resetControlData(); };
                toolbar.querySelector('#sp-ctrl-save-btn').onclick = function() { saveControlData(); };
                view.appendChild(toolbar);

                // Scrollable body
                var body = document.createElement('div');
                body.id = 'sp-ctrl-body';
                body.style.cssText = 'flex:1;overflow-y:auto;padding:12px 16px;';

                var sections = [
                    {id: 'storm_generation', title: '1. Storm Generation', desc: 'Event window, intensity sampling, duration, gaps, batch weights'},
                    {id: 'hydrograph_synthesis', title: '2. Hydrograph Synthesis', desc: 'Gamma shape, saturation, infiltration, superposition, depth-damage'},
                    {id: 'gauge_propagation', title: '3. Gauge \u2192 Property Propagation', desc: 'Manning\'s roughness, retention, terrain velocity, bankfull offset'},
                    {id: 'spatial_correlation', title: '4. Spatial Correlation', desc: 'Exponential kernel range, nugget, lognormal sigma'},
                    {id: 'stress_catalogue', title: '5. Stress Catalogue', desc: 'Minimum storms, default duration, peak position'}
                ];

                sections.forEach(function(sec) {
                    var panel = document.createElement('div');
                    panel.style.cssText = 'margin-bottom:10px;border:1px solid #ddd;border-radius:4px;background:white;';

                    var header = document.createElement('div');
                    header.style.cssText = 'padding:8px 12px;background:#f8f9fa;cursor:pointer;display:flex;align-items:center;gap:8px;border-bottom:1px solid #eee;';
                    header.innerHTML =
                        '<span id="sp-ctrl-arrow-' + sec.id + '" style="font-size:10px;color:#666;transition:transform 0.2s;">\u25BC</span>' +
                        '<span style="font-size:11px;font-weight:700;color:#1565c0;">' + sec.title + '</span>' +
                        '<span style="font-size:10px;color:#999;margin-left:4px;">' + sec.desc + '</span>';
                    header.onclick = function() {
                        var content = document.getElementById('sp-ctrl-section-' + sec.id);
                        var arrow = document.getElementById('sp-ctrl-arrow-' + sec.id);
                        if (content.style.display === 'none') {
                            content.style.display = 'block';
                            arrow.style.transform = 'rotate(0deg)';
                        } else {
                            content.style.display = 'none';
                            arrow.style.transform = 'rotate(-90deg)';
                        }
                    };

                    var content = document.createElement('div');
                    content.id = 'sp-ctrl-section-' + sec.id;
                    content.style.cssText = 'padding:10px 12px;';

                    panel.appendChild(header);
                    panel.appendChild(content);
                    body.appendChild(panel);
                });

                // Event delegation: any input change inside the body marks dirty
                body.addEventListener('input', function(e) {
                    if (e.target && e.target.hasAttribute('data-ctrl-key')) ctrlMarkDirty();
                });
                body.addEventListener('change', function(e) {
                    if (e.target && e.target.hasAttribute('data-ctrl-key')) ctrlMarkDirty();
                });

                view.appendChild(body);

                // Status bar
                var statusBar = document.createElement('div');
                statusBar.id = 'sp-ctrl-status';
                statusBar.style.cssText = 'padding:4px 16px;border-top:1px solid #eee;font-size:10px;color:#999;background:#f9f9f9;flex-shrink:0;';
                statusBar.textContent = 'Source: loading...';
                view.appendChild(statusBar);

                return view;
            }

            // ---- Help tooltip builder ----

            var _ctrlTipId = 0;

            function _ctrlHelp(text) {
                var id = 'sp-ctrl-tip-' + (++_ctrlTipId);
                return '<span style="position:relative;display:inline-block;vertical-align:middle;margin-left:4px;">' +
                    '<span ' +
                        'onmouseenter="document.getElementById(\'' + id + '\').style.display=\'block\';" ' +
                        'onmouseleave="document.getElementById(\'' + id + '\').style.display=\'none\';" ' +
                        'style="display:inline-block;width:13px;height:13px;line-height:13px;' +
                        'text-align:center;font-size:9px;font-weight:700;color:#999;' +
                        'border:1px solid #ccc;border-radius:50%;cursor:help;">?</span>' +
                    '<div id="' + id + '" style="display:none;position:absolute;left:20px;top:-8px;z-index:9999;' +
                        'width:280px;padding:8px 10px;background:#333;color:#f0f0f0;font-size:10px;' +
                        'font-weight:400;line-height:1.4;border-radius:4px;' +
                        'box-shadow:0 2px 8px rgba(0,0,0,0.3);pointer-events:none;">' +
                        text.replace(/"/g, '&quot;') +
                    '</div></span>';
            }

            // ---- Field renderers ----

            function _ctrlScalarField(label, key, value, opts) {
                opts = opts || {};
                var step = opts.step || (Number.isInteger(value) ? '1' : '0.01');
                var type = typeof value === 'boolean' ? 'checkbox' : 'number';
                var help = opts.help ? _ctrlHelp(opts.help) : '';
                var html = '<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">' +
                    '<label style="font-size:10px;color:#555;min-width:200px;font-weight:600;">' + label + help + '</label>';
                if (type === 'checkbox') {
                    html += '<input type="checkbox" data-ctrl-key="' + key + '" ' +
                        (value ? 'checked ' : '') +
                        'style="margin:0;">';
                } else {
                    html += '<input type="number" data-ctrl-key="' + key + '" value="' + value + '" ' +
                        'step="' + step + '" ' +
                        '' +
                        'style="width:100px;padding:3px 6px;font-size:11px;border:1px solid #ccc;border-radius:3px;font-family:monospace;">';
                }
                html += '</div>';
                return html;
            }

            function _ctrlDictField(label, key, dictVal, opts) {
                opts = opts || {};
                var help = opts.help ? _ctrlHelp(opts.help) : '';
                var html = '<div style="margin:6px 0;">' +
                    '<div style="font-size:10px;color:#555;font-weight:600;margin-bottom:4px;">' + label + help + '</div>' +
                    '<div style="display:flex;flex-wrap:wrap;gap:6px;">';
                Object.keys(dictVal).forEach(function(k) {
                    var v = dictVal[k];
                    if (Array.isArray(v)) {
                        html += '<div style="border:1px solid #eee;border-radius:3px;padding:4px 6px;background:#fafafa;">' +
                            '<span style="font-size:9px;color:#888;display:block;">' + k + '</span>';
                        v.forEach(function(elem, i) {
                            html += '<input type="number" data-ctrl-key="' + key + '.' + k + '.' + i + '" value="' + elem + '" ' +
                                'step="0.01" ' +
                                'style="width:55px;padding:2px 4px;font-size:10px;border:1px solid #ccc;border-radius:2px;font-family:monospace;margin:1px;">';
                        });
                        html += '</div>';
                    } else {
                        html += '<div style="border:1px solid #eee;border-radius:3px;padding:4px 6px;background:#fafafa;">' +
                            '<span style="font-size:9px;color:#888;display:block;">' + k + '</span>' +
                            '<input type="number" data-ctrl-key="' + key + '.' + k + '" value="' + v + '" ' +
                            'step="0.01" ' +
                            'style="width:65px;padding:2px 4px;font-size:10px;border:1px solid #ccc;border-radius:2px;font-family:monospace;">' +
                            '</div>';
                    }
                });
                html += '</div></div>';
                return html;
            }

            function _ctrlArrayField(label, key, arr, opts) {
                opts = opts || {};
                var help = opts.help ? _ctrlHelp(opts.help) : '';
                var html = '<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">' +
                    '<label style="font-size:10px;color:#555;min-width:200px;font-weight:600;">' + label + help + '</label>' +
                    '<div style="display:flex;gap:4px;">';
                arr.forEach(function(v, i) {
                    html += '<input type="number" data-ctrl-key="' + key + '.' + i + '" value="' + v + '" ' +
                        'step="0.01" ' +
                        'style="width:55px;padding:2px 4px;font-size:10px;border:1px solid #ccc;border-radius:2px;font-family:monospace;">';
                });
                html += '</div></div>';
                return html;
            }

            function openControlGuide() {
                var cfg = window.__BACKEND_CONFIG || {};
                var base = cfg.url || '';
                window.open(base + '/api/v1/governance/storm-control/guide/pdf', '_blank');
            }

            function ctrlMarkDirty() {
                ctrlDirty = true;
                var ind = document.getElementById('sp-ctrl-dirty');
                if (ind) ind.style.display = 'inline';
            }

            function ctrlClearDirty() {
                ctrlDirty = false;
                var ind = document.getElementById('sp-ctrl-dirty');
                if (ind) ind.style.display = 'none';
            }
    
