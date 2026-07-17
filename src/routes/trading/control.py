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
Storm Sequence Control — GET/POST endpoints for storm_control.json.

Allows the Control tab in the trading desk to read and write the
centralised storm stress workflow parameters.
"""

from flask import jsonify, request

from config.auth import FUNC_TRADE_PRS, WRITE
from config.storm_control import (
    apply_storm_control,
    get_defaults,
    load_storm_control,
    save_storm_control,
)

from .._rbac import require
from .blueprint import trading_bp


@trading_bp.route("/trading/control/params", methods=["GET"])
def get_control_params():
    """Return current storm control parameters (from JSON or defaults)."""
    data = load_storm_control()
    if not data:
        data = get_defaults()
        source = "defaults"
    else:
        source = "json"
    return jsonify({"status": "success", "params": data, "source": source})


@trading_bp.route("/trading/control/params", methods=["POST"])
@require(FUNC_TRADE_PRS, WRITE)
def save_control_params():
    """Save updated storm control parameters and hot-reload.

    Admin-only: requires ``X-Admin-Password`` header matching the shared
    port/admin credential. Changes here affect every storm calculation
    across the platform, so gating prevents accidental writes.
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "No JSON body"}), 400

    # Basic structural validation
    if "sections" not in body and "version" not in body:
        return jsonify({"status": "error", "message": "Missing sections"}), 400

    save_storm_control(body)
    apply_storm_control()
    return jsonify({"status": "success", "message": "Parameters saved and applied"})


@trading_bp.route("/trading/control/reset", methods=["POST"])
@require(FUNC_TRADE_PRS, WRITE)
def reset_control_params():
    """Reset storm control parameters to Python defaults.

    Admin-only: see ``save_control_params`` for rationale.
    """
    defaults = get_defaults()
    save_storm_control(defaults)
    apply_storm_control()
    return jsonify({"status": "success", "params": defaults})
