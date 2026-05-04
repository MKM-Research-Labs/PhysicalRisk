# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Startup preloader — popup DOM and per-item status helpers.

JS fragment concatenated into the parent ``startup.get_js()`` IIFE.
``_createStartupPopup`` builds the centred preload modal and per-dataset
rows; ``_startupMarkItem`` flips the spinner to a tick (success) or
dash (failure) and appends a detail label.
"""


def get_js() -> str:
    """Return JS fragment for the startup popup helpers (parent IIFE scope)."""
    return """
            function _createStartupPopup() {
                var popup = document.createElement('div');
                popup.id = 'startup-preloader-popup';
                popup.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'background:white;border:1px solid #ddd;border-radius:10px;' +
                    'box-shadow:0 8px 32px rgba(0,0,0,0.2);z-index:9999;' +
                    'min-width:360px;padding:24px 28px;font-family:Arial,sans-serif;';

                var title = document.createElement('div');
                title.style.cssText =
                    'font-size:15px;font-weight:bold;color:#1565c0;' +
                    'margin-bottom:16px;display:flex;align-items:center;gap:8px;';
                title.innerHTML =
                    '<span style="font-size:20px;">&#9651;</span>' +
                    ' Loading MKM Research Platform…';
                popup.appendChild(title);

                // Overall progress bar
                var barWrap = document.createElement('div');
                barWrap.style.cssText =
                    'background:#f0f0f0;border-radius:4px;height:6px;' +
                    'margin-bottom:16px;overflow:hidden;';
                var bar = document.createElement('div');
                bar.id = 'startup-pre-bar';
                bar.style.cssText =
                    'height:100%;width:0%;background:#1976d2;' +
                    'transition:width 0.3s ease;border-radius:4px;';
                barWrap.appendChild(bar);
                popup.appendChild(barWrap);

                // Dataset rows — two columns
                var grid = document.createElement('div');
                grid.style.cssText =
                    'display:grid;grid-template-columns:1fr 1fr;gap:5px 16px;';

                _startupDatasets.forEach(function(ds) {
                    var row = document.createElement('div');
                    row.id = 'startup-row-' + ds[0];
                    row.style.cssText =
                        'display:flex;align-items:center;gap:8px;font-size:11px;color:#555;';
                    var icon = document.createElement('span');
                    icon.id = 'startup-icon-' + ds[0];
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;' +
                        'border:2px solid #ccc;display:inline-block;flex-shrink:0;' +
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
                        '  0%{border-top-color:#1976d2;transform:rotate(0deg);}' +
                        '  100%{border-top-color:#1976d2;transform:rotate(360deg);}' +
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
                        'align-items:center;justify-content:center;font-size:10px;flex-shrink:0;' +
                        'background:#e8f5e9;color:#2e7d32;border:2px solid #a5d6a7;';
                    icon.textContent = '✓';
                    if (detail) {
                        var row = document.getElementById('startup-row-' + key);
                        if (row) {
                            var det = document.createElement('span');
                            det.style.cssText = 'color:#aaa;font-size:10px;margin-left:auto;';
                            det.textContent = detail;
                            row.appendChild(det);
                        }
                    }
                } else {
                    icon.style.cssText =
                        'width:14px;height:14px;border-radius:50%;display:inline-flex;' +
                        'align-items:center;justify-content:center;font-size:10px;flex-shrink:0;' +
                        'background:#fff3e0;color:#e65100;border:2px solid #ffcc80;';
                    icon.textContent = '–';
                }
            }
"""
