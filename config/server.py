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
Server settings mixin for MKM Research Labs PRS Platform.

ServerMixin holds all host/port/CORS/endpoint configuration that was
previously duplicated between Config and PortfolioConfig.
"""

import os


def _validated_port() -> int:
    port = int(os.getenv('MKM_SERVER_PORT', '5013'))
    if not 1 <= port <= 65535:
        raise ValueError(f"MKM_SERVER_PORT={port} outside valid range 1-65535")
    return port


class ServerMixin:
    """Shared server settings inherited by both Config and PortfolioConfig."""

    SERVER_HOST: str = os.getenv('MKM_SERVER_HOST', '127.0.0.1')
    SERVER_PORT: int = _validated_port()
    DEBUG: bool = os.getenv('MKM_DEBUG', 'false').lower() == 'true'
    # CATCHMENT is supplied by CatchmentMixin's @property — do not redeclare
    # here as a class attribute, or it will shadow the property in MRO and
    # `config.catchment_id = 'halong'` will silently fail to propagate to
    # `config.CATCHMENT`.

    CORS_ORIGINS: list = [
        "http://localhost:*",
        "http://127.0.0.1:*",
    ]

    # Unified API endpoint map (superset of what was in Config + PortfolioConfig).
    # health_check normalised to /api/v1/health; export_data to /api/v1/export.
    ENDPOINTS: dict = {
        'health_check':      '/api/v1/health',
        'properties':        '/api/v1/properties',
        'gauges':            '/api/v1/gauges',
        'property_report':   '/api/v1/properties/report',
        'gauge_report':      '/api/v1/gauges/report',
        'rloan_report':      '/api/v1/properties/rloan-report',
        'commercial_report': '/api/v1/commercial/report',
        'commercial_loan_report': '/api/v1/commercial/loan-report',
        'gauge_history':     '/api/v1/gauges/{gauge_id}/history',
        'export_data':       '/api/v1/export',
    }

    @property
    def SERVER_URL(self) -> str:
        """Full base URL for the running server."""
        return f"http://{self.SERVER_HOST}:{self.SERVER_PORT}"

    def get_cors_config(self) -> dict:
        """Return CORS configuration dict for Flask-CORS."""
        return {
            'origins': self.CORS_ORIGINS,
            'methods': ['GET', 'POST', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization'],
            'supports_credentials': True,
        }
