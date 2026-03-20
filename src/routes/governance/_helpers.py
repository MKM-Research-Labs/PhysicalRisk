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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Shared I/O helpers for governance routes."""

import json
import logging
from datetime import datetime

from flask import jsonify

from . import _constants

logger = logging.getLogger(__name__)


# ── Inventory ──

def _load_inventory():
    """Load model inventory from JSON file."""
    try:
        with open(_constants.INVENTORY_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load model inventory: %s", e)
        return None


def _save_inventory(data):
    """Save model inventory to JSON file."""
    try:
        with open(_constants.INVENTORY_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save model inventory: %s", e)
        return False


# ── Audit log ──

def _load_audit_log():
    """Load audit log from JSON file."""
    try:
        with open(_constants.AUDIT_LOG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logger.error("Failed to load audit log: %s", e)
        return []


def _save_audit_log(entries):
    """Save audit log to JSON file."""
    try:
        with open(_constants.AUDIT_LOG_PATH, "w") as f:
            json.dump(entries, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save audit log: %s", e)
        return False


# ── MRC meetings ──

def _load_meetings():
    """Load MRC meetings from JSON file."""
    try:
        with open(_constants.MRC_MEETINGS_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_meetings(meetings):
    """Save MRC meetings to JSON file."""
    try:
        with open(_constants.MRC_MEETINGS_PATH, "w") as f:
            json.dump(meetings, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save MRC meetings: %s", e)
        return False


def _find_meeting(meeting_id):
    """Load meetings and find one by ID. Returns (meetings_list, meeting, error_response)."""
    meetings = _load_meetings()
    meeting = next((m for m in meetings if m["id"] == meeting_id), None)
    if not meeting:
        return meetings, None, jsonify({"status": "error", "message": f"Meeting {meeting_id} not found"})
    return meetings, meeting, None


def _save_and_respond(meetings, meeting):
    """Save meetings list and return the updated meeting."""
    meeting["updated_at"] = datetime.now().isoformat()
    if not _save_meetings(meetings):
        return jsonify({"status": "error", "message": "Failed to save meeting"}), 500
    return jsonify({"status": "success", "meeting": meeting})


# ── BCBS 239 ──

def _load_bcbs239():
    """Load BCBS 239 assessment from JSON file."""
    try:
        with open(_constants.BCBS239_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_bcbs239(data):
    """Save BCBS 239 assessment to JSON file."""
    try:
        with open(_constants.BCBS239_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save BCBS 239 assessment: %s", e)
        return False


# ── RACI ──

def _load_raci():
    """Load RACI matrix from JSON file."""
    try:
        with open(_constants.RACI_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_raci(data):
    """Save RACI matrix to JSON file."""
    try:
        with open(_constants.RACI_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save RACI matrix: %s", e)
        return False


# ── Governance documents ──

def _load_gov_documents():
    """Load governance documents metadata."""
    try:
        with open(_constants.GOV_DOCUMENTS_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_gov_documents(docs):
    """Save governance documents metadata."""
    try:
        with open(_constants.GOV_DOCUMENTS_PATH, "w") as f:
            json.dump(docs, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save governance documents: %s", e)
        return False


# ── Bibliography ──

def _load_bibliography():
    """Load bibliography from JSON file."""
    try:
        with open(_constants.BIBLIOGRAPHY_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"references": [], "categories": []}


def _save_bibliography(data):
    """Save bibliography to JSON file."""
    try:
        with open(_constants.BIBLIOGRAPHY_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as e:
        logger.error("Failed to save bibliography: %s", e)
        return False


# ── Risk rating calculation ──

# ── Data lineage ──

def _load_lineage():
    """Load data lineage manifest from JSON file."""
    try:
        with open(_constants.LINEAGE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _load_field_lineage():
    """Load field-level lineage registry from JSON file."""
    try:
        with open(_constants.FIELD_LINEAGE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _calculate_risk_rating(model):
    """Calculate composite risk rating from 5 weighted factors.

    Returns dict with calculated_rating, calculated_score, and component_scores.
    """
    vq = model.get("validation_questions", [])

    # 1. validation_coverage (30%): fraction of questions fully Addressed
    addressed = sum(1 for q in vq if q.get("status") == "Addressed")
    applicable = sum(1 for q in vq if q.get("status") != "Not Applicable")
    coverage = addressed / max(applicable, 1)

    # 2. remediation_health (25%): penalise open and overdue items
    today = datetime.now().strftime("%Y-%m-%d")
    rem = model.get("remediation_steps", [])
    open_count = sum(1 for r in rem if r.get("status") == "Open")
    overdue_count = sum(
        1 for r in rem
        if r.get("status") == "Open" and r.get("due_date") and r["due_date"] < today
    )
    rem_score = max(0.0, min(1.0, 1.0 - 0.15 * open_count - 0.25 * overdue_count))

    # 3. review_currency (20%): is the review schedule current
    next_review = model.get("next_review_date")
    if next_review:
        days_to = (datetime.strptime(next_review, "%Y-%m-%d") - datetime.now()).days
        if days_to < 0:
            review_score = 0.0
        elif days_to <= 30:
            review_score = 0.5
        else:
            review_score = 1.0
    else:
        review_score = 0.0

    # 4. assumption_risk (15%): high-impact assumptions
    assumptions = model.get("assumptions", [])
    high_assumptions = sum(1 for a in assumptions if a.get("impact") == "High")
    assumption_score = max(0.0, min(1.0, 1.0 - 0.2 * high_assumptions))

    # 5. limitation_risk (10%): high-impact limitations
    limitations = model.get("limitations", [])
    high_limitations = sum(1 for lim in limitations if lim.get("impact") == "High")
    limitation_score = max(0.0, min(1.0, 1.0 - 0.2 * high_limitations))

    # Weighted composite
    composite = (
        coverage * 0.30
        + rem_score * 0.25
        + review_score * 0.20
        + assumption_score * 0.15
        + limitation_score * 0.10
    )

    if composite >= 0.75:
        rating = "Acceptable"
    elif composite >= 0.45:
        rating = "Conditional"
    else:
        rating = "Unacceptable"

    return {
        "calculated_rating": rating,
        "calculated_score": round(composite, 3),
        "component_scores": {
            "validation_coverage": round(coverage, 3),
            "remediation_health": round(rem_score, 3),
            "review_currency": round(review_score, 3),
            "assumption_risk": round(assumption_score, 3),
            "limitation_risk": round(limitation_score, 3),
        },
    }


def _vq_summary(model):
    """Return validation question coverage string like '3/9'."""
    vq = model.get("validation_questions", [])
    addressed = sum(1 for q in vq if q.get("status") == "Addressed")
    applicable = sum(1 for q in vq if q.get("status") != "Not Applicable")
    return f"{addressed}/{applicable}"
