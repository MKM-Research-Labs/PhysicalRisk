# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from flask import Blueprint, jsonify, send_from_directory

from config import config
from loaders.loader_registry import LoaderRegistry

health_bp = Blueprint("health", __name__)

_STATIC_DIR = config.get_static_dir()


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
    """Root route - redirect to the platform map.

    The active catchment is fixed by the CLI flag at server start
    (``phys.py server --halong``), so there is no selection step: the
    visualization page is the application entry point.
    """
    from flask import redirect
    return redirect('/visualization')


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
