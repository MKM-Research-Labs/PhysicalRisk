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
                        'background:white;border:1px solid #ccc;border-radius:8px;' +
                        'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                        'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                    var header = document.createElement('div');
                    header.style.cssText =
                        'display:flex;justify-content:space-between;align-items:center;' +
                        'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                        'border-radius:8px 8px 0 0;min-height:40px;';

                    var title = document.createElement('span');
                    title.id = '__NS__-title';
                    title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';
                    title.textContent = '__DEFAULT_TITLE__';

                    var btnGroup = document.createElement('div');
                    btnGroup.style.cssText = 'display:flex;gap:8px;';

                    var downloadBtn = document.createElement('button');
                    downloadBtn.id = '__NS__-download';
                    downloadBtn.textContent = 'Download';
                    downloadBtn.style.cssText =
                        'padding:4px 12px;border:1px solid __BTN_COLOR__;border-radius:4px;' +
                        'background:__BTN_COLOR__;color:white;cursor:pointer;font-size:12px;';
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
                        'padding:4px 12px;border:1px solid #dc3545;border-radius:4px;' +
                        'background:#dc3545;color:white;cursor:pointer;font-size:12px;';
                    closeBtn.onclick = function() { hidePanel(); };

                    btnGroup.appendChild(downloadBtn);
                    btnGroup.appendChild(closeBtn);
                    header.appendChild(title);
                    header.appendChild(btnGroup);

                    var container = document.createElement('div');
                    container.id = '__NS__-container';
                    container.style.cssText = 'flex:1;overflow:hidden;border-radius:0 0 8px 8px;';

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
