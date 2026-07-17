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

"""
Flask application for MKM Research Labs PRS Platform.

Usage:
    python server.py

    # Or with Flask CLI
    flask --app server:create_app run
"""

import logging

from flask import Flask
from flask_cors import CORS

from config import config
from database.config_binding import use_configured_backend
from routes import register_blueprints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory."""

    # Bind the data-access backend selected by MKM_REPO_BACKEND (file | pg).
    # Default 'file' = today's JSON tree; 'pg' reads from PostgreSQL (WP2.1).
    use_configured_backend()

    # Create app
    app = Flask(__name__)

    # Session-signing key for the WP5 login flow (set MKM_SECRET_KEY in production).
    from config.auth import SECRET_KEY
    app.secret_key = SECRET_KEY

    # Configure CORS
    CORS(app, **config.get_cors_config())

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Audit logging for mutating requests
    @app.before_request
    def audit_log():
        from flask import request as req
        if req.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            logger.info("AUDIT %s %s from %s", req.method, req.path,
                        req.remote_addr)

    # Register blueprints
    register_blueprints(app)

    # WP5: if MKM_BOOTSTRAP_ADMIN_USER/_PASSWORD are set, ensure that first Admin
    # exists. No-op (and never fatal) otherwise.
    from routes.auth import maybe_bootstrap_admin_from_env
    maybe_bootstrap_admin_from_env()

    logger.info("Application created, routes registered")

    return app


def main():
    """Run the development server."""
    app = create_app()

    logger.info("=" * 60)
    logger.info("  MKM Research Labs - PRS Platform Report Server")
    logger.info("=" * 60)
    logger.info(f"  Server URL:     {config.SERVER_URL}")
    logger.info(f"  Debug mode:     {config.DEBUG}")
    logger.info(f"  Catchment:      {config.CATCHMENT}")
    logger.info(f"  Input dir:      {config.get_input_dir()}")
    logger.info(f"  Reports dir:    {config.get_reports_dir()}")
    logger.info("=" * 60)
    logger.info("  Endpoints:")
    logger.info("  GET  /select-catchment          Catchment selector")
    logger.info("  GET  /                          Health check")
    logger.info("  GET  /health                    Detailed health")
    logger.info("  GET  /api/v1/properties         List properties")
    logger.info("  POST /api/v1/properties/report  Generate report")
    logger.info("  GET  /api/v1/gauges             List gauges")
    logger.info("  POST /api/v1/gauges/report      Generate report")

    app.run(
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()
