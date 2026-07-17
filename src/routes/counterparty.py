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
Counterparty API routes.

Provides endpoints for counterparty data used in PRS trading.
"""

from flask import Blueprint, jsonify

from config import config
import database

counterparty_bp = Blueprint("counterparty", __name__)


def _counterparties() -> list:
    """All counterparty records for the active catchment (via the database pkg)."""
    return database.list_counterparties(config.catchment_id)


@counterparty_bp.route("/counterparties", methods=["GET"])
def list_counterparties():
    """List all counterparties (summary for dropdowns)."""
    try:
        counterparties = _counterparties()

        summary = []
        for ctpy in counterparties:
            cs = ctpy.get("CounterpartySet", {})
            party = cs.get("Party", {})
            platform = cs.get("_platform", {})

            summary.append({
                "counterparty_id": party.get("PartyID"),
                "name": party.get("PartyName"),
                "short_name": platform.get("ShortName", ""),
                "type": platform.get("PartyType", ""),
                "status": platform.get("Status", "Active"),
                "credit_rating": platform.get("CreditRating", "NR"),
                "max_notional": platform.get("MaxNotional"),
                "max_tenor": platform.get("MaxTenor"),
            })

        return jsonify({
            "status": "success",
            "counterparties": summary,
            "count": len(summary),
        })

    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@counterparty_bp.route("/counterparties/<ctpy_id>", methods=["GET"])
def get_counterparty(ctpy_id: str):
    """Get full counterparty details."""
    try:
        for ctpy in _counterparties():
            party = ctpy.get("CounterpartySet", {}).get("Party", {})
            if party.get("PartyID") == ctpy_id:
                return jsonify({"status": "success", "counterparty": ctpy})

        return jsonify({"status": "error", "message": f"Counterparty {ctpy_id} not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
