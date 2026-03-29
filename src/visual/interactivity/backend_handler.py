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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Backend communication handler for interactive map functionality.

Handles API calls between the frontend map and backend services
for report generation and data export.
"""

import json
from typing import Any, Dict

import folium

from config import config


class BackendHandler:
    """Handler for backend API communication."""

    def __init__(self, server_url: str = None, endpoints: Dict[str, str] = None):
        """
        Initialize backend handler.

        Args:
            server_url: Backend server URL (defaults to config.SERVER_URL)
            endpoints: API endpoint mappings (defaults to config.ENDPOINTS)
        """
        self.server_url = server_url or config.SERVER_URL
        self.endpoints = endpoints.copy() if endpoints else config.ENDPOINTS.copy()

    def get_js(self) -> str:
        """Generate JavaScript for backend communication."""
        from pathlib import Path
        js_path = Path(__file__).parent.parent.parent / 'static' / 'js' / 'backend-handler.js'
        js_code = js_path.read_text()
        # Use empty string for url so all API calls use relative paths.
        # The visualization HTML is always served by Flask, so
        # fetch('/api/v1/...') hits the correct server on any port.
        # An absolute URL (e.g. http://127.0.0.1:5013) gets baked into
        # the cached HTML and breaks when the port changes.
        backend_config = json.dumps({
            'url': '',
            'endpoints': self.endpoints,
            'timeout': 30000
        })
        return f"<script>window.__BACKEND_CONFIG = {backend_config};\n{js_code}</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add backend communication to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def configure(self, server_url: str = None, endpoints: Dict[str, str] = None) -> None:
        """Update configuration."""
        if server_url:
            self.server_url = server_url
        if endpoints:
            self.endpoints.update(endpoints)

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        return {
            'server_url': self.server_url,
            'total_endpoints': len(self.endpoints),
            'endpoints': list(self.endpoints.keys())
        }
