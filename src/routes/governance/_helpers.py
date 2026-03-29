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

import hashlib
import json
import logging
import os
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


def _find_model(inventory, model_id):
    """Find a model by ID in the inventory. Returns the model dict or None."""
    for m in inventory.get("models", []):
        if m["model_id"] == model_id:
            return m
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


def _stable_id(path):
    """Generate a short stable ID from a file path."""
    return hashlib.md5(path.encode()).hexdigest()[:8]


def _pdf_entry(filepath, description, source):
    """Build a document-style dict for a discovered PDF."""
    filename = os.path.basename(filepath)
    try:
        size = os.path.getsize(filepath)
    except OSError:
        size = 0
    return {
        "id": _stable_id(filepath),
        "filename": filename,
        "description": description,
        "size": size,
        "source": source,
    }


_AUDIT_LABELS = {
    "full_audit_report.pdf": "Full Audit Report",
    "test_report.pdf": "Test Results Report",
    "code_duplication_report.pdf": "Code Duplication Report",
    "hardcoding_report.pdf": "Hard-Coding Parameter Audit",
    "data_lineage_report.pdf": "Data Lineage Report (BCBS 239)",
    "large_file_report.pdf": "Code Modularisation Analysis",
    "model_risk_report.pdf": "Model Risk Report",
}


def _discover_audit_docs():
    """Scan data/output/audit/ for generated PDF reports."""
    audit_dir = _constants.AUDIT_REPORTS_DIR
    if not os.path.isdir(audit_dir):
        return []
    results = []
    for entry in sorted(os.scandir(audit_dir), key=lambda e: e.name):
        if entry.is_file() and entry.name.endswith(".pdf"):
            label = _AUDIT_LABELS.get(entry.name, entry.name.replace("_", " ").replace(".pdf", "").title())
            results.append(_pdf_entry(entry.path, label, "audit"))
    return results


_MODEL_PDF_LABELS = {
    "test_results.pdf": "Test Results",
    "analysis.pdf": "Model Analysis",
}


def _discover_model_docs():
    """Scan docs/models/ for per-model documentation PDFs."""
    docs_dir = str(_constants._docs_dir)
    if not os.path.isdir(docs_dir):
        return []

    # Build reverse lookup: directory name → model ID
    dir_to_id = {v: k for k, v in _constants._MODEL_DOC_DIRS.items()}

    results = []
    for model_dir in sorted(os.scandir(docs_dir), key=lambda e: e.name):
        if not model_dir.is_dir():
            continue
        model_id = dir_to_id.get(model_dir.name, model_dir.name)
        model_label = model_dir.name.replace("_", " ").title()
        for entry in sorted(os.scandir(model_dir.path), key=lambda e: e.name):
            if entry.is_file() and entry.name.endswith(".pdf"):
                kind = _MODEL_PDF_LABELS.get(entry.name, "Documentation")
                desc = f"{model_label} — {kind}" if entry.name in _MODEL_PDF_LABELS else f"{model_label} — {entry.name.replace('.pdf', '').replace('_', ' ').title()}"
                results.append(_pdf_entry(entry.path, desc, "model"))
    return results


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
