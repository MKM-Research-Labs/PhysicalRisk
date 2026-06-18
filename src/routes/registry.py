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

"""Blueprint registration for the MKM Research Labs PRS Platform."""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints with the Flask application."""
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
