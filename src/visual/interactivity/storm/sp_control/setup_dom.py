# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Control tab — DOM construction for the storm control view."""


def get_js() -> str:
    """Return JavaScript for createControlView() DOM builder."""
    return r"""
            function createControlView() {
                var view = document.createElement('div');
                view.id = 'sp-control-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Top toolbar
                var toolbar = document.createElement('div');
                toolbar.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#f5f7fa;flex-shrink:0;';
                toolbar.innerHTML =
                    '<span style="font-size:12px;font-weight:700;color:#333;">Storm Sequence Control</span>' +
                    '<span id="sp-ctrl-dirty" style="font-size:10px;color:#e65100;font-weight:600;display:none;">Unsaved changes</span>' +
                    '<span style="flex:1;"></span>' +
                    '<button id="sp-ctrl-reset-btn" onclick="resetControlData()" style="padding:4px 12px;font-size:11px;font-weight:600;border:1px solid #999;border-radius:3px;background:#f5f5f5;color:#555;cursor:pointer;">Reset Defaults</button>' +
                    '<button id="sp-ctrl-save-btn" onclick="saveControlData()" style="padding:4px 14px;font-size:11px;font-weight:600;border:1px solid #1565c0;border-radius:3px;background:#1565c0;color:white;cursor:pointer;">Save &amp; Apply</button>';
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

            function _ctrlHelp(text) {
                return '<span title="' + text.replace(/"/g, '&quot;') + '" ' +
                    'style="display:inline-block;width:13px;height:13px;line-height:13px;' +
                    'text-align:center;font-size:9px;font-weight:700;color:#999;' +
                    'border:1px solid #ccc;border-radius:50%;cursor:help;margin-left:4px;' +
                    'vertical-align:middle;">?</span>';
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
                        'onchange="ctrlMarkDirty()" style="margin:0;">';
                } else {
                    html += '<input type="number" data-ctrl-key="' + key + '" value="' + value + '" ' +
                        'step="' + step + '" ' +
                        'oninput="ctrlMarkDirty()" ' +
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
                                'step="0.01" oninput="ctrlMarkDirty()" ' +
                                'style="width:55px;padding:2px 4px;font-size:10px;border:1px solid #ccc;border-radius:2px;font-family:monospace;margin:1px;">';
                        });
                        html += '</div>';
                    } else {
                        html += '<div style="border:1px solid #eee;border-radius:3px;padding:4px 6px;background:#fafafa;">' +
                            '<span style="font-size:9px;color:#888;display:block;">' + k + '</span>' +
                            '<input type="number" data-ctrl-key="' + key + '.' + k + '" value="' + v + '" ' +
                            'step="0.01" oninput="ctrlMarkDirty()" ' +
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
                        'step="0.01" oninput="ctrlMarkDirty()" ' +
                        'style="width:55px;padding:2px 4px;font-size:10px;border:1px solid #ccc;border-radius:2px;font-family:monospace;">';
                });
                html += '</div></div>';
                return html;
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
    """
