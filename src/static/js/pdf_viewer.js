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

            (function() {
                var PANEL_W = '__PANEL_W__';
                var PANEL_H = '__PANEL_H__';
                var pdfPanel = null;

                function createPanel() {
                    if (pdfPanel) return pdfPanel;

                    pdfPanel = document.createElement('div');
                    pdfPanel.id = '__NS__-panel';
                    pdfPanel.style.cssText =
                        'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                        'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                        'background:var(--panel);border:1px solid var(--divider);border-radius:var(--radius-lg);' +
                        'box-shadow:var(--shadow-toast);z-index:2000;' +
                        'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                    var header = document.createElement('div');
                    header.style.cssText =
                        'display:flex;justify-content:space-between;align-items:center;' +
                        'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--wash);' +
                        'border-radius:var(--radius-lg) var(--radius-lg) 0 0;min-height:40px;';

                    var title = document.createElement('span');
                    title.id = '__NS__-title';
                    title.style.cssText = 'font-weight:bold;font-size:var(--size-14);color:var(--text);';
                    title.textContent = '__DEFAULT_TITLE__';

                    var btnGroup = document.createElement('div');
                    btnGroup.style.cssText = 'display:flex;gap:var(--space-4);';

                    var downloadBtn = document.createElement('button');
                    downloadBtn.id = '__NS__-download';
                    downloadBtn.textContent = 'Download';
                    downloadBtn.style.cssText =
                        'padding:var(--space-2) var(--space-6);border:1px solid __BTN_COLOR__;border-radius:var(--radius-4);' +
                        'background:__BTN_COLOR__;color:var(--inverse);cursor:pointer;font-size:var(--size-sm);';
                    downloadBtn.onclick = function() {
                        var iframe = document.getElementById('__NS__-iframe');
                        if (iframe && iframe.src) {
                            var a = document.createElement('a');
                            a.href = iframe.src;
                            a.download = (title.textContent || '__DEFAULT_TITLE__') + '.pdf';
                            a.click();
                        }
                    };

                    var closeBtn = document.createElement('button');
                    closeBtn.textContent = 'Close';
                    closeBtn.style.cssText =
                        'padding:var(--space-2) var(--space-6);border:1px solid var(--red);border-radius:var(--radius-4);' +
                        'background:var(--red);color:var(--inverse);cursor:pointer;font-size:var(--size-sm);';
                    closeBtn.onclick = function() { hidePanel(); };

                    btnGroup.appendChild(downloadBtn);
                    btnGroup.appendChild(closeBtn);
                    header.appendChild(title);
                    header.appendChild(btnGroup);

                    var container = document.createElement('div');
                    container.id = '__NS__-container';
                    container.style.cssText = 'flex:1;overflow:hidden;border-radius:0 0 var(--radius-lg) var(--radius-lg);';

                    var iframe = document.createElement('iframe');
                    iframe.id = '__NS__-iframe';
                    iframe.style.cssText = 'width:100%;height:100%;border:none;';
                    container.appendChild(iframe);

                    pdfPanel.appendChild(header);
                    pdfPanel.appendChild(container);
                    document.body.appendChild(pdfPanel);

                    document.addEventListener('keydown', function(e) {
                        if (e.key === 'Escape' && pdfPanel.style.display !== 'none') {
                            hidePanel();
                        }
                    });

                    return pdfPanel;
                }

                function showPanel(entityId, pdfBase64) {
                    var panel = createPanel();
                    var title = document.getElementById('__NS__-title');
                    var displayLabel = __DISPLAY_LABEL__;
                    title.textContent = '__DEFAULT_TITLE__: ' + (displayLabel || entityId);

                    var iframe = document.getElementById('__NS__-iframe');
                    iframe.src = 'data:application/pdf;base64,' + pdfBase64;

                    panel.style.display = 'flex';
                }

                function hidePanel() {
                    if (pdfPanel) {
                        pdfPanel.style.display = 'none';
                        var iframe = document.getElementById('__NS__-iframe');
                        if (iframe) iframe.src = '';
                    }
                }

                window.__API_NAME__ = {
                    show: showPanel,
                    hide: hidePanel
                };
                __EVENT_LISTENER__
            })();
