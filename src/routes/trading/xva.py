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

"""XVA endpoints (MKM-XV-001, WP4): run the book, read the latest run, quote.

ILLUSTRATIVE: every response carries the model's status line. KVA is shown
beside the booked XVA, never inside it (D-16).
"""

import logging

from flask import jsonify, request

import database
from config import config
from config.auth import FUNC_TRADE_PRS, READ, WRITE

from .._rbac import require
from . import trading_bp

logger = logging.getLogger(__name__)


def xva_inputs():
    """(enriched open trades, counterparties by PartyID, market state, hazard lookup)."""
    from models.xva import service
    return service.book_inputs()


def run_and_save(n_paths=None):
    """Run XVA on the open book and store it as the latest run."""
    from models.xva import service
    return service.run_and_save(n_paths)


@trading_bp.route("/trading/xva/run", methods=["POST"])
@require(FUNC_TRADE_PRS, WRITE)
def post_xva_run():
    try:
        data = request.get_json(silent=True) or {}
        result = run_and_save(data.get("n_paths"))
        return jsonify({"status": "success", **result})
    except Exception as e:
        logger.error("XVA run error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/xva", methods=["GET"])
def get_xva():
    run = database.get_xva_run(config.catchment_id)
    if not run:
        return jsonify({"status": "empty", "message": "No XVA run yet"})
    return jsonify({"status": "success", **run})


@trading_bp.route("/trading/xva/quote", methods=["POST"])
@require(FUNC_TRADE_PRS, READ)
def post_xva_quote():
    """Incremental XVA and KVA of a proposed trade; nothing is stored."""
    from config.xva import XvaConfig
    from models.xva import desk

    data = request.get_json(silent=True) or {}
    required = ("gauge_id", "notional", "trade_spread_bps", "is_payer", "maturity")
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"status": "error", "message": f"missing fields: {', '.join(missing)}"}), 400
    try:
        enriched, counterparties, state, hazard_for = xva_inputs()
        out = desk.quote(data, enriched, counterparties, state, hazard_for,
                         desk.with_paths(XvaConfig(), data.get("n_paths")))
        return jsonify({"status": "success", **out})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error("XVA quote error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
