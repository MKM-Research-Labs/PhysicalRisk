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
