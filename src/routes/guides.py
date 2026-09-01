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

"""Workflow user-guide PDFs.

These six guides — storm control, gauge and property PRS pricing, market
making, the EOD process and stress testing — document *operational* workflows,
not governance. They were served from the governance blueprint only by
accident of history, which coupled a live trading-desk control to a subsystem
being removed: the Control tab's User Guide button opens one of these.

Extracted so the governance blueprint can go without taking the Control tab's
guide with it.
"""

import os

from flask import Blueprint, jsonify, send_file

from config import config

guides_bp = Blueprint("guides", __name__)

_DOCS_DIR = str(config.get_project_root() / "docs" / "models")

# guide key -> (directory under docs/models, PDF filename)
USER_GUIDE_PDFS = {
    "storm-control":        ("storm_control",        "storm_control_guide.pdf"),
    "gauge-prs-pricing":    ("gauge_prs_pricing",    "gauge_prs_pricing_guide.pdf"),
    "property-prs-pricing": ("property_prs_pricing", "property_prs_pricing_guide.pdf"),
    "market-making":        ("market_making",        "market_making_guide.pdf"),
    "eod-process":          ("eod_process",          "eod_process_guide.pdf"),
    "stress-testing":       ("stress_testing",       "stress_testing_guide.pdf"),
}


@guides_bp.route("/guides/<guide_key>/pdf", methods=["GET"])
def get_user_guide_pdf(guide_key):
    """Serve a workflow user guide PDF."""
    entry = USER_GUIDE_PDFS.get(guide_key)
    if entry is None:
        return jsonify({
            "status": "error",
            "message": f"Unknown guide: {guide_key}",
        }), 404

    doc_dir, pdf_name = entry
    pdf_path = os.path.join(_DOCS_DIR, doc_dir, pdf_name)
    if not os.path.isfile(pdf_path):
        return jsonify({
            "status": "error",
            "message": f"Guide PDF not yet generated. "
                       f"Run: make -C docs/models/{doc_dir}/",
        }), 404

    return send_file(pdf_path, mimetype="application/pdf")
