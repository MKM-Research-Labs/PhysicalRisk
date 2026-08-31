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

            function _createStartupPopup() {
                var popup = document.createElement('div');
                popup.id = 'startup-preloader-popup';
                popup.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'background:var(--panel);border:1px solid var(--line-strong);border-radius:var(--radius-xl);' +
                    'box-shadow:var(--shadow-modal);z-index:9999;' +
                    'min-width:360px;padding:24px 28px;font-family:Arial,sans-serif;';

                var title = document.createElement('div');
                title.style.cssText =
                    'font-size:var(--size-lg);font-weight:bold;color:var(--accent-mid);' +
                    'margin-bottom:var(--space-8);display:flex;align-items:center;gap:var(--space-4);';
                title.innerHTML =
                    '<span style="font-size:var(--size-xl);">&#9651;</span>' +
                    ' Loading MKM Research Platform…';
                popup.appendChild(title);

                // Overall progress bar
                var barWrap = document.createElement('div');
                barWrap.style.cssText =
                    'background:var(--code);border-radius:var(--radius-4);height:6px;' +
                    'margin-bottom:var(--space-8);overflow:hidden;';
                var bar = document.createElement('div');
                bar.id = 'startup-pre-bar';
                bar.style.cssText =
                    'height:100%;width:0%;background:var(--accent);' +
                    'transition:width 0.3s ease;border-radius:var(--radius-4);';
                barWrap.appendChild(bar);
                popup.appendChild(barWrap);

                // Dataset rows — two columns
                var grid = document.createElement('div');
                grid.style.cssText =
                    'display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3) var(--space-8);';

                _startupDatasets.forEach(function(ds) {
                    var row = document.createElement('div');
                    row.id = 'startup-row-' + ds[0];
                    row.style.cssText =
                        'display:flex;align-items:center;gap:var(--space-4);font-size:var(--size-xs);color:var(--text-2);';
                    var icon = document.createElement('span');
                    icon.id = 'startup-icon-' + ds[0];
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;' +
                        'border:2px solid var(--divider);display:inline-block;flex-shrink:0;' +
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
                        '  0%{border-top-color:var(--accent);transform:rotate(0deg);}' +
                        '  100%{border-top-color:var(--accent);transform:rotate(360deg);}' +
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
                        'align-items:center;justify-content:center;font-size:var(--size-xxs);flex-shrink:0;' +
                        'background:var(--ok-bg);color:var(--green-dark);border:2px solid var(--green-pale);';
                    icon.textContent = '✓';
                    if (detail) {
                        var row = document.getElementById('startup-row-' + key);
                        if (row) {
                            var det = document.createElement('span');
                            det.style.cssText = 'color:var(--disabled);font-size:var(--size-xxs);margin-left:auto;';
                            det.textContent = detail;
                            row.appendChild(det);
                        }
                    }
                } else {
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;display:inline-flex;' +
                        'align-items:center;justify-content:center;font-size:var(--size-xxs);flex-shrink:0;' +
                        'background:var(--warn-bg-warm);color:var(--amber-deep);border:2px solid var(--warn-line-pale-2);';
                    icon.textContent = '–';
                }
            }
