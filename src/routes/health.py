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

# routes/health.py

import os
from flask import Blueprint, jsonify, send_from_directory

from config import config
from loaders.loader_registry import LoaderRegistry

health_bp = Blueprint("health", __name__)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'static')


def _get_registry() -> LoaderRegistry:
    """Get loader registry with configured data directory."""
    return LoaderRegistry(data_dir=config.get_input_dir())


@health_bp.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_from_directory(_STATIC_DIR, "favicon.ico", mimetype="image/x-icon")


@health_bp.route("/apple-touch-icon.png", methods=["GET"])
def apple_touch_icon():
    return send_from_directory(_STATIC_DIR, "apple-touch-icon.png", mimetype="image/png")


@health_bp.route("/apple-touch-icon-precomposed.png", methods=["GET"])
def apple_touch_icon_precomposed():
    return send_from_directory(_STATIC_DIR, "apple-touch-icon-precomposed.png", mimetype="image/png")


@health_bp.route("/", methods=["GET"])
def root():
    """Root route - redirect to catchment selector."""
    from flask import redirect
    return redirect('/select-catchment')


@health_bp.route("/health", methods=["GET"])
@health_bp.route("/api/v1/health", methods=["GET"])
def health_check():
    """Health check endpoint - server status and endpoint list."""
    return jsonify({
        "status": "ok",
        "service": "MKM Research Labs Report Server",
        "version": "2.0.0",
        "endpoints": {
            "health": "GET /, GET /health",
            "properties": "GET /api/v1/properties, POST /api/v1/properties/report",
            "gauges": "GET /api/v1/gauges, POST /api/v1/gauges/report",
            "legacy": {
                "property_report": "POST /generate_property_report",
                "gauge_report": "POST /generate_gauge_report",
                "list_gauges": "GET /list_gauges",
            },
        },
    })


@health_bp.route("/health/detailed", methods=["GET"])
def detailed_health():
    """Detailed health check with data file status."""
    registry = _get_registry()
    file_status = registry.check_data_files()
    is_healthy = all(file_status.values())

    return jsonify({
        "status": "healthy" if is_healthy else "degraded",
        "files": file_status,
        "config": {
            "input_dir": str(config.get_input_dir()),
            "reports_dir": str(config.get_reports_dir()),
            "debug": config.DEBUG,
        },
    }), (200 if is_healthy else 503)
