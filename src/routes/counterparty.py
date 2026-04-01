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

"""
Counterparty API routes.

Provides endpoints for counterparty data used in PRS trading.
"""

import json

from flask import Blueprint, jsonify

from config import config
from jsonfiles import JSONFileConfig

counterparty_bp = Blueprint("counterparty", __name__)


def _load_counterparty_data() -> dict:
    """Load counterparty data from JSON file."""
    ctpy_path = config.get_input_dir() / JSONFileConfig.COUNTERPARTY_PORTFOLIO
    if not ctpy_path.exists():
        return {"counterparties": []}
    with open(ctpy_path, 'r') as f:
        return json.load(f)


@counterparty_bp.route("/counterparties", methods=["GET"])
def list_counterparties():
    """List all counterparties (summary for dropdowns)."""
    try:
        data = _load_counterparty_data()
        counterparties = data.get("counterparties", [])

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
        data = _load_counterparty_data()
        for ctpy in data.get("counterparties", []):
            party = ctpy.get("CounterpartySet", {}).get("Party", {})
            if party.get("PartyID") == ctpy_id:
                return jsonify({"status": "success", "counterparty": ctpy})

        return jsonify({"status": "error", "message": f"Counterparty {ctpy_id} not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
