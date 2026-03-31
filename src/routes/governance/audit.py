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

"""Audit trail, validation questions, risk rating, and PDF doc serving routes."""

import logging
import os
from datetime import datetime

from flask import jsonify, request, send_file

from . import governance_bp
from ._constants import (
    VALID_VQ_STATUSES,
    VALID_RISK_RATINGS,
    _MODEL_DOC_DIRS,
    _docs_dir,
)
from ._helpers import (
    _find_model,
    _get_model_or_404,
    _load_inventory,
    _save_inventory,
    _load_audit_log,
    _save_audit_log,
    _calculate_risk_rating,
)

logger = logging.getLogger(__name__)


@governance_bp.route("/governance/models/<model_id>/audit", methods=["POST"])
def log_model_usage(model_id):
    """Log a model usage event to the audit trail."""
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response

    data = request.get_json(silent=True) or {}

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": data.get("event_type", "usage"),
        "user": data.get("user", "system"),
        "action": data.get("action", ""),
        "parameters": data.get("parameters", {}),
        "context": data.get("context", ""),
        "source": data.get("source", "api"),
    }

    audit_log = _load_audit_log()
    audit_log.append(entry)

    # Keep last 10000 entries
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]

    if not _save_audit_log(audit_log):
        return jsonify({"status": "error", "message": "Failed to save audit entry"}), 500

    return jsonify({"status": "success", "entry": entry})


@governance_bp.route("/governance/audit-trail", methods=["GET"])
def get_audit_trail():
    """Get audit trail with optional filtering."""
    model_id = request.args.get("model_id")
    event_type = request.args.get("event_type")
    limit = request.args.get("limit", 100, type=int)

    audit_log = _load_audit_log()

    if model_id:
        audit_log = [e for e in audit_log if e.get("model_id") == model_id]

    if event_type:
        audit_log = [e for e in audit_log if e.get("event_type") == event_type]

    # Return most recent entries
    entries = audit_log[-limit:]
    entries.reverse()

    return jsonify({
        "status": "success",
        "entries": entries,
        "total_entries": len(audit_log),
        "returned": len(entries),
    })


# ── Validation Questions & Risk Rating ──

@governance_bp.route(
    "/governance/models/<model_id>/validation-questions/<int:question_id>/update",
    methods=["POST"],
)
def update_validation_question(model_id, question_id):
    """Update a single validation question's response for a model.

    Expects JSON: {status, evidence, reviewed_by}
    """
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    questions = model.get("validation_questions", [])
    question = None
    for q in questions:
        if q["question_id"] == question_id:
            question = q
            break
    if not question:
        return jsonify({"status": "error", "message": f"Question {question_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    evidence = data.get("evidence", "")
    reviewed_by = data.get("reviewed_by", "unknown")

    if not new_status or new_status not in VALID_VQ_STATUSES:
        return jsonify({
            "status": "error",
            "message": f"Invalid status. Must be one of: {VALID_VQ_STATUSES}",
        }), 400

    old_status = question.get("status")
    question["status"] = new_status
    question["evidence"] = evidence
    question["reviewed_by"] = reviewed_by
    question["last_reviewed"] = datetime.now().strftime("%Y-%m-%d")

    # Recalculate risk rating
    calc = _calculate_risk_rating(model)
    rr = model.setdefault("overall_risk_rating", {})
    rr["calculated_rating"] = calc["calculated_rating"]
    rr["calculated_score"] = calc["calculated_score"]
    rr["component_scores"] = calc["component_scores"]
    rr["last_calculated"] = datetime.now().isoformat()
    rr["effective_rating"] = rr.get("mrc_override") or calc["calculated_rating"]

    if not _save_inventory(inventory):
        return jsonify({"status": "error", "message": "Failed to save inventory"}), 500

    # Audit trail
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": "validation_question_update",
        "user": reviewed_by,
        "action": f"Updated validation Q{question_id}: {question['short_label']}",
        "parameters": {
            "question_id": question_id,
            "old_status": old_status,
            "new_status": new_status,
        },
        "context": evidence[:200] if evidence else "",
        "source": "governance_ui",
    }
    audit_log = _load_audit_log()
    audit_log.append(audit_entry)
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]
    _save_audit_log(audit_log)

    logger.info("Model %s: validation Q%d status changed %s -> %s by %s",
                model_id, question_id, old_status, new_status, reviewed_by)

    return jsonify({"status": "success", "model": model, "audit_entry": audit_entry})


@governance_bp.route("/governance/models/<model_id>/risk-rating", methods=["GET"])
def get_risk_rating(model_id):
    """Calculate and return the composite risk rating for a model."""
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    calc = _calculate_risk_rating(model)

    # Persist calculated result
    rr = model.setdefault("overall_risk_rating", {})
    rr["calculated_rating"] = calc["calculated_rating"]
    rr["calculated_score"] = calc["calculated_score"]
    rr["component_scores"] = calc["component_scores"]
    rr["last_calculated"] = datetime.now().isoformat()
    rr["effective_rating"] = rr.get("mrc_override") or calc["calculated_rating"]

    _save_inventory(inventory)

    return jsonify({
        "status": "success",
        "model_id": model_id,
        "risk_rating": rr,
    })


@governance_bp.route("/governance/models/<model_id>/risk-rating/override", methods=["POST"])
def override_risk_rating(model_id):
    """Apply or clear MRC override of risk rating.

    Expects JSON: {rating, reason, user}
    Set rating to null to clear override.
    """
    result = _get_model_or_404(model_id)
    if not isinstance(result[1], dict):
        return result  # error response
    inventory, model = result

    data = request.get_json(silent=True) or {}
    new_rating = data.get("rating")
    reason = data.get("reason", "").strip()
    user = data.get("user", "unknown")

    if new_rating is not None and new_rating not in VALID_RISK_RATINGS:
        return jsonify({
            "status": "error",
            "message": f"Invalid rating. Must be one of: {VALID_RISK_RATINGS} or null to clear",
        }), 400

    if not reason:
        return jsonify({"status": "error", "message": "A reason is required"}), 400

    rr = model.setdefault("overall_risk_rating", {})
    old_override = rr.get("mrc_override")

    rr["mrc_override"] = new_rating
    rr["mrc_override_reason"] = reason if new_rating else None
    rr["mrc_override_date"] = datetime.now().strftime("%Y-%m-%d") if new_rating else None
    rr["mrc_override_by"] = user if new_rating else None
    rr["effective_rating"] = new_rating or rr.get("calculated_rating", "Not Rated")

    if not _save_inventory(inventory):
        return jsonify({"status": "error", "message": "Failed to save inventory"}), 500

    action = f"Cleared MRC override" if new_rating is None else f"MRC override set to {new_rating}"
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": "risk_rating_override",
        "user": user,
        "action": action,
        "parameters": {
            "old_override": old_override,
            "new_override": new_rating,
        },
        "context": reason,
        "source": "governance_ui",
    }
    audit_log = _load_audit_log()
    audit_log.append(audit_entry)
    if len(audit_log) > 10000:
        audit_log = audit_log[-10000:]
    _save_audit_log(audit_log)

    logger.info("Model %s: risk rating override %s -> %s by %s. Reason: %s",
                model_id, old_override, new_rating, user, reason)

    return jsonify({"status": "success", "model": model, "audit_entry": audit_entry})


# ── PDF document serving ──

@governance_bp.route("/governance/models/<model_id>/documentation/pdf", methods=["GET"])
def get_model_documentation_pdf(model_id):
    """Serve per-model documentation PDF."""
    doc_dir = _MODEL_DOC_DIRS.get(model_id)
    if not doc_dir:
        return jsonify({"status": "error", "message": f"No documentation directory for {model_id}"}), 404

    # Model doc PDF matches directory name (e.g. gev_hazard/gev_hazard.pdf)
    pdf_name = doc_dir + ".pdf"
    pdf_path = os.path.join(_docs_dir, doc_dir, pdf_name)
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": f"Documentation PDF not found for {model_id}"}), 404

    return send_file(pdf_path, mimetype="application/pdf")


@governance_bp.route("/governance/models/<model_id>/test-results/pdf", methods=["GET"])
def get_model_test_results_pdf(model_id):
    """Serve per-model test results PDF."""
    doc_dir = _MODEL_DOC_DIRS.get(model_id)
    if not doc_dir:
        return jsonify({"status": "error", "message": f"No documentation directory for {model_id}"}), 404

    pdf_path = os.path.join(_docs_dir, doc_dir, "test_results.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": "Test results PDF not yet generated. Run: python app.py check tests --pdf"}), 404

    return send_file(pdf_path, mimetype="application/pdf")


@governance_bp.route("/governance/models/<model_id>/analysis/pdf", methods=["GET"])
def get_model_analysis_pdf(model_id):
    """Serve per-model analysis PDF (sensitivity analysis, stress testing)."""
    doc_dir = _MODEL_DOC_DIRS.get(model_id)
    if not doc_dir:
        return jsonify({"status": "error", "message": f"No documentation directory for {model_id}"}), 404

    pdf_path = os.path.join(_docs_dir, doc_dir, "analysis.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": "Analysis PDF not yet generated. Run: python -m docs.models.sensitivities.generate_all_analysis"}), 404

    return send_file(pdf_path, mimetype="application/pdf")


@governance_bp.route("/governance/mrc/terms-of-reference/pdf", methods=["GET"])
def get_mrc_tor_pdf():
    """Serve the MRC Terms of Reference PDF."""
    pdf_path = os.path.join(_docs_dir, "mrc_tor", "mrc_terms_of_reference.pdf")
    if not os.path.isfile(pdf_path):
        return jsonify({"status": "error", "message": "MRC ToR PDF not yet generated. Run: python -m docs.models.mrc_tor.generator --pdf"}), 404

    return send_file(pdf_path, mimetype="application/pdf")
