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
Inline gauge PDF viewer panel.

Displays generated gauge PDF reports inside an overlay panel
using an embedded iframe with base64-encoded PDF data.
"""

from typing import Any, Dict

import folium


class GaugePDFPanel:
    """Handler for inline gauge PDF display."""

    def __init__(self,
                 panel_width: str = "850px",
                 panel_height: str = "90vh"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge PDF viewer panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var pdfPanel = null;

            function createPanel() {{
                if (pdfPanel) return pdfPanel;

                pdfPanel = document.createElement('div');
                pdfPanel.id = 'gauge-pdf-panel';
                pdfPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;min-height:40px;';

                var title = document.createElement('span');
                title.id = 'gauge-pdf-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';
                title.textContent = 'Gauge Report';

                var btnGroup = document.createElement('div');
                btnGroup.style.cssText = 'display:flex;gap:8px;';

                var downloadBtn = document.createElement('button');
                downloadBtn.id = 'gauge-pdf-download';
                downloadBtn.textContent = 'Download';
                downloadBtn.style.cssText =
                    'padding:4px 12px;border:1px solid #007bff;border-radius:4px;' +
                    'background:#007bff;color:white;cursor:pointer;font-size:12px;';
                downloadBtn.onclick = function() {{
                    var iframe = document.getElementById('gauge-pdf-iframe');
                    if (iframe && iframe.src) {{
                        var a = document.createElement('a');
                        a.href = iframe.src;
                        a.download = (title.textContent || 'gauge_report') + '.pdf';
                        a.click();
                    }}
                }};

                var closeBtn = document.createElement('button');
                closeBtn.textContent = 'Close';
                closeBtn.style.cssText =
                    'padding:4px 12px;border:1px solid #dc3545;border-radius:4px;' +
                    'background:#dc3545;color:white;cursor:pointer;font-size:12px;';
                closeBtn.onclick = function() {{ hidePanel(); }};

                btnGroup.appendChild(downloadBtn);
                btnGroup.appendChild(closeBtn);
                header.appendChild(title);
                header.appendChild(btnGroup);

                // PDF container
                var container = document.createElement('div');
                container.id = 'gauge-pdf-container';
                container.style.cssText = 'flex:1;overflow:hidden;border-radius:0 0 8px 8px;';

                var iframe = document.createElement('iframe');
                iframe.id = 'gauge-pdf-iframe';
                iframe.style.cssText = 'width:100%;height:100%;border:none;';
                container.appendChild(iframe);

                pdfPanel.appendChild(header);
                pdfPanel.appendChild(container);
                document.body.appendChild(pdfPanel);

                // ESC to close
                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Escape' && pdfPanel.style.display !== 'none') {{
                        hidePanel();
                    }}
                }});

                return pdfPanel;
            }}

            function showPanel(gaugeId, pdfBase64) {{
                var panel = createPanel();
                var title = document.getElementById('gauge-pdf-title');
                title.textContent = 'Gauge Report: ' + gaugeId;

                var iframe = document.getElementById('gauge-pdf-iframe');
                iframe.src = 'data:application/pdf;base64,' + pdfBase64;

                panel.style.display = 'flex';
            }}

            function hidePanel() {{
                if (pdfPanel) {{
                    pdfPanel.style.display = 'none';
                    var iframe = document.getElementById('gauge-pdf-iframe');
                    if (iframe) iframe.src = '';
                }}
            }}

            // Public API
            window.GaugePDFPanel = {{
                show: showPanel,
                hide: hidePanel
            }};

            // Listen for generateGaugeReport results
            document.addEventListener('gaugePdfReady', function(e) {{
                if (e.detail && e.detail.gaugeId && e.detail.pdfBase64) {{
                    showPanel(e.detail.gaugeId, e.detail.pdfBase64);
                }}
            }});
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add PDF viewer panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height
        }
