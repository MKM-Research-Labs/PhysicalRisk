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

"""Blueprint registration for the MKM Research Labs PRS Platform."""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints with the Flask application."""
    from .admin import admin_bp
    from .auth import auth_bp
    from .catchment import catchment_bp
    from .cdm_review import cdm_review_bp
    from .commercial import commercial_bp
    from .counterparty import counterparty_bp
    from .gauges import gauges_bp
    from .governance import governance_bp
    from .health import health_bp
    from .perils import perils_bp
    from .properties import properties_bp
    from .propertyhc import propertyhc_bp
    from .propertyts import propertyts_bp
    from .prs import prs_bp
    from .trading import trading_bp
    from .visualization import visualization_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)  # /auth/* — login/logout/me (top-level, no prefix)
    app.register_blueprint(admin_bp)  # /admin + /admin/api/* — RBAC admin grid
    app.register_blueprint(catchment_bp)
    app.register_blueprint(cdm_review_bp)
    app.register_blueprint(visualization_bp)
    app.register_blueprint(properties_bp, url_prefix="/api/v1")
    app.register_blueprint(commercial_bp, url_prefix="/api/v1")
    app.register_blueprint(gauges_bp, url_prefix="/api/v1")
    app.register_blueprint(propertyts_bp, url_prefix="/api/v1")
    app.register_blueprint(propertyhc_bp, url_prefix="/api/v1")
    app.register_blueprint(counterparty_bp, url_prefix="/api/v1")
    app.register_blueprint(prs_bp, url_prefix="/api/v1")
    app.register_blueprint(trading_bp, url_prefix="/api/v1")
    app.register_blueprint(governance_bp, url_prefix="/api/v1")
    app.register_blueprint(perils_bp, url_prefix="/api/v1")
