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

"""Entry point for the CDM Asset Review workstream.

The CDM Asset Review tool currently runs as a standalone Flask app
(``tools/cdm_property_editor/app.py``) on its own port. This route gives the
main application a clean, same-origin launch URL (``/cdm-asset-review``) that
the map's house icon opens; it redirects to the standalone tool so the tool's
location lives in one place (overridable via ``CDM_REVIEW_URL`` /
``CDM_REVIEW_PORT``).

When the tool is later mounted into this app as a blueprint, only this redirect
target changes — the icon and its URL stay the same.
"""

import os

from flask import Blueprint, redirect, request

cdm_review_bp = Blueprint("cdm_review", __name__)

# Default location of the standalone CDM Asset Review server.
CDM_REVIEW_PORT = os.environ.get("CDM_REVIEW_PORT", "5057")


@cdm_review_bp.route("/cdm-asset-review")
def cdm_asset_review():
    """Redirect to the CDM Asset Review workstream."""
    target = os.environ.get("CDM_REVIEW_URL")
    if not target:
        host = request.host.split(":")[0]
        target = f"{request.scheme}://{host}:{CDM_REVIEW_PORT}/"
    return redirect(target)
