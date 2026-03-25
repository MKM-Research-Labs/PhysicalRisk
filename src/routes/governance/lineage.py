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

"""Data lineage routes: manifest, trace, and staleness check."""

import logging
import os
from datetime import datetime, timedelta

from flask import jsonify, request

from . import governance_bp
from ._helpers import _load_field_lineage, _load_lineage

logger = logging.getLogger(__name__)

# Pipeline steps in execution order with expected output files
_PIPELINE_STEPS = [
    {"step": "gauges", "generator": "port (step 1)", "output": "gauge.json"},
    {"step": "properties", "generator": "port (step 2)", "output": "property.json"},
    {"step": "mortgages", "generator": "port (step 3)", "output": "mortgage.json"},
    {"step": "gaugehd", "generator": "port (step 4)", "output": "gaugehd/"},
    {"step": "stressm", "generator": "port (step 5)", "output": "gaugets/"},
    {"step": "hazard", "generator": "port (step 6)", "output": "gaugehc.json"},
    {"step": "propertyts", "generator": "port (step 7)", "output": "propertyts/"},
    {"step": "propertyhc", "generator": "port (step 8)", "output": "propertyhc.json"},
    {"step": "counterparties", "generator": "port (step 9)", "output": "counterparty.json"},
    {"step": "blotter", "generator": "port (step 10)", "output": "prs/"},
]

# Staleness threshold — centralised in config/port.py
from config.port import LINEAGE_STALE_HOURS as _STALE_HOURS


def _check_staleness(lineage):
    """Check each pipeline step for freshness. Returns list of step statuses."""
    from config import config

    input_dir = str(config.get_input_dir())
    now = datetime.now()
    results = []

    for step_def in _PIPELINE_STEPS:
        path = os.path.join(input_dir, step_def["output"])
        step_info = {
            "step": step_def["step"],
            "generator": step_def["generator"],
            "path": step_def["output"],
            "last_run": None,
            "status": "missing",
            "issues": [],
        }

        # Check if lineage manifest has a recorded run
        if lineage:
            manifest_steps = lineage.get("steps", {})
            manifest_entry = manifest_steps.get(step_def["step"], {})
            if manifest_entry.get("last_run"):
                step_info["last_run"] = manifest_entry["last_run"]

        # Check filesystem
        try:
            if os.path.isdir(path):
                # For directories, check most recent file
                mtime = max(
                    os.path.getmtime(os.path.join(path, f))
                    for f in os.listdir(path) if not f.startswith(".")
                ) if os.listdir(path) else 0
            elif os.path.isfile(path):
                mtime = os.path.getmtime(path)
            else:
                mtime = 0
        except (OSError, ValueError):
            mtime = 0

        if mtime > 0:
            last_modified = datetime.fromtimestamp(mtime)
            if not step_info["last_run"]:
                step_info["last_run"] = last_modified.isoformat()
            age = now - last_modified
            if age > timedelta(hours=_STALE_HOURS):
                step_info["status"] = "stale"
                step_info["issues"].append(
                    f"Last modified {age.days}d {age.seconds // 3600}h ago"
                )
            else:
                step_info["status"] = "fresh"
        else:
            step_info["status"] = "missing"
            step_info["issues"].append("Output not found on disk")

        results.append(step_info)

    return results


def _trace_data(lineage, data_type, data_id):
    """Trace a data_type/data_id through the pipeline by searching data files.

    Scans actual JSON files and directories for the entity ID, returning
    a list of provenance steps with file locations and context.
    Supports: Gauge, Property, Trade (PRS), Counterparty.
    """
    from pathlib import Path
    import json as _json

    from config import config

    input_dir = Path(config.get_input_dir())
    classifiers_dir = Path(config.get_classifiers_dir())
    blotter_dir = Path(config.get_trading_dir())

    trace = []

    def _add(step, file_path, role, context=""):
        """Append a trace entry."""
        # Make path relative to input_dir for display
        try:
            rel = str(Path(file_path).relative_to(input_dir.parent.parent))
        except ValueError:
            rel = str(file_path)
        trace.append({
            "step": step,
            "file": rel,
            "role": role,
            "context": context,
        })

    def _search_json(path, entity_id):
        """Check if entity_id appears anywhere in a JSON file."""
        try:
            text = path.read_text(errors="ignore")
            return entity_id in text
        except Exception:
            return False

    def _search_dir_files(dir_path, entity_id):
        """Check if entity_id appears as a filename stem or in file contents."""
        if not dir_path.is_dir():
            return []
        hits = []
        for f in dir_path.iterdir():
            if entity_id in f.stem:
                hits.append(f)
            elif f.suffix == ".json" and f.stat().st_size < 50_000_000:
                if _search_json(f, entity_id):
                    hits.append(f)
        return hits

    # ── Gauge trace ──────────────────────────────────────────────────
    if data_type.lower() == "gauge":
        # Step 1: gauge.json (master data)
        gauge_path = input_dir / "gauge.json"
        if gauge_path.exists() and _search_json(gauge_path, data_id):
            _add("gauges", gauge_path, "origin",
                 "Master gauge record (CDM FloodGauge)")

        # Step 4: gaugehd/ (historical daily)
        hd_dir = input_dir / "gaugehd"
        if hd_dir.is_dir():
            for f in hd_dir.glob(f"*{data_id}*"):
                _add("gaugehd", f, "derived",
                     "Historical daily observations")
                break

        # Step 5: gaugets/ (time series)
        ts_file = input_dir / "gaugets" / f"{data_id}.json"
        if ts_file.exists():
            _add("stressm", ts_file, "derived",
                 "168h storm simulation time series")

        # Step 5: stressm/ (storm sequences — split per-gauge directory)
        sg_dir = input_dir / "sequence_gauge"
        sg_legacy = input_dir / "sequence_gauge_summary.json"
        if sg_dir.is_dir():
            # Search per-gauge file matching data_id
            sg_file = sg_dir / f"{data_id}.json"
            if sg_file.exists():
                _add("stressm", sg_file, "derived",
                     "Per-sequence peak water levels & flood flags")
            elif (sg_dir / "_index.json").exists() and _search_json(
                    sg_dir / "_index.json", data_id):
                _add("stressm", sg_dir / "_index.json", "derived",
                     "Per-sequence peak water levels & flood flags")
        elif sg_legacy.exists() and _search_json(sg_legacy, data_id):
            _add("stressm", sg_legacy, "derived",
                 "Per-sequence peak water levels & flood flags")

        # Step 6: gaugehc.json (hazard curves)
        hc_path = input_dir / "gaugehc.json"
        if hc_path.exists() and _search_json(hc_path, data_id):
            _add("hazard", hc_path, "derived",
                 "GEV hazard curve (return periods & probabilities)")

        # Classifiers
        clf_path = classifiers_dir / f"{data_id}.joblib"
        if clf_path.exists():
            _add("classifiers", clf_path, "derived",
                 "Trained GBM flood classifier")
        summary_path = classifiers_dir / "training_summary.json"
        if summary_path.exists() and _search_json(summary_path, data_id):
            _add("classifiers", summary_path, "derived",
                 "Classifier metrics (AUC, accuracy, thresholds)")

        # Blotter: market state
        ms_path = blotter_dir / "market_state.json"
        if ms_path.exists() and _search_json(ms_path, data_id):
            _add("blotter", ms_path, "consumed",
                 "Hazard term structure (yield curve per trigger)")

        # PRS trades referencing this gauge
        prs_dir = input_dir / "prs"
        if prs_dir.is_dir():
            trade_hits = _search_dir_files(prs_dir, data_id)
            for th in trade_hits[:5]:  # cap at 5
                _add("blotter", th, "consumed",
                     f"PRS trade referencing gauge in basket")

    # ── Property trace ───────────────────────────────────────────────
    elif data_type.lower() == "property":
        prop_path = input_dir / "property.json"
        if prop_path.exists() and _search_json(prop_path, data_id):
            _add("properties", prop_path, "origin",
                 "Master property record (CDM PropertyHeader)")

        # Mortgage
        mtg_path = input_dir / "mortgage.json"
        if mtg_path.exists() and _search_json(mtg_path, data_id):
            _add("mortgages", mtg_path, "derived",
                 "Linked mortgage (LTV, amortisation, terms)")

        # propertyts/
        pts_file = input_dir / "propertyts" / f"{data_id}.json"
        if pts_file.exists():
            _add("propertyts", pts_file, "derived",
                 "Flood event time series (storm impacts)")

        # propertyhc.json
        phc_path = input_dir / "propertyhc.json"
        if phc_path.exists() and _search_json(phc_path, data_id):
            _add("propertyhc", phc_path, "derived",
                 "Property hazard curve (interpolated from gauges)")

    # ── Trade trace ──────────────────────────────────────────────────
    elif data_type.lower() in ("trade", "prs"):
        prs_file = input_dir / "prs" / f"{data_id}.json"
        if prs_file.exists():
            _add("blotter", prs_file, "origin",
                 "PRS trade confirmation (CDM PhysicalSwap)")

        # Trade marks
        marks_path = blotter_dir / "trade_marks.json"
        if marks_path.exists() and _search_json(marks_path, data_id):
            _add("blotter", marks_path, "consumed",
                 "Trade close-out mark / settlement")

        # EOD snapshots
        eod_dir = blotter_dir / "eod"
        if eod_dir.is_dir():
            eod_hits = _search_dir_files(eod_dir, data_id)
            for eh in eod_hits[:3]:
                _add("blotter", eh, "consumed",
                     "EOD snapshot (P&L, position)")

    # ── Counterparty trace ───────────────────────────────────────────
    elif data_type.lower() == "counterparty":
        ctpy_path = input_dir / "counterparty.json"
        if ctpy_path.exists() and _search_json(ctpy_path, data_id):
            _add("counterparties", ctpy_path, "origin",
                 "Counterparty master record (CDM Party)")

        # PRS trades referencing this counterparty
        prs_dir = input_dir / "prs"
        if prs_dir.is_dir():
            trade_hits = _search_dir_files(prs_dir, data_id)
            for th in trade_hits[:5]:
                _add("blotter", th, "consumed",
                     "PRS trade with this counterparty")

    # ── Generic fallback ─────────────────────────────────────────────
    else:
        # Scan all JSON files in input_dir (non-recursive, capped)
        for f in sorted(input_dir.glob("*.json"))[:20]:
            if _search_json(f, data_id):
                _add("unknown", f, "found",
                     f"ID found in {f.name}")

    return trace


@governance_bp.route("/governance/data-lineage", methods=["GET"])
def get_data_lineage():
    """Return pipeline manifest with live staleness check."""
    lineage = _load_lineage()

    try:
        step_statuses = _check_staleness(lineage)
    except Exception as e:
        logger.error("Staleness check failed: %s", e)
        step_statuses = []

    fresh = sum(1 for s in step_statuses if s["status"] == "fresh")
    stale = sum(1 for s in step_statuses if s["status"] == "stale")
    missing = sum(1 for s in step_statuses if s["status"] == "missing")

    return jsonify({
        "status": "success",
        "pipeline_steps": step_statuses,
        "summary": {
            "total": len(step_statuses),
            "fresh": fresh,
            "stale": stale,
            "missing": missing,
            "health": "healthy" if missing == 0 and stale == 0
                      else "degraded" if missing == 0
                      else "unhealthy",
        },
        "manifest": lineage,
        "as_of": datetime.now().isoformat(),
    })


@governance_bp.route("/governance/data-lineage/trace", methods=["GET"])
def trace_data_lineage():
    """Trace a data_type/data_id through the pipeline."""
    data_type = request.args.get("data_type", "").strip()
    data_id = request.args.get("data_id", "").strip()

    if not data_type or not data_id:
        return jsonify({
            "status": "error",
            "message": "Both data_type and data_id query params are required",
        }), 400

    lineage = _load_lineage()

    try:
        trace = _trace_data(lineage, data_type, data_id)
    except Exception as e:
        logger.error("Trace failed for %s/%s: %s", data_type, data_id, e)
        return jsonify({
            "status": "error",
            "message": f"Trace failed: {e}",
        }), 500

    return jsonify({
        "status": "success",
        "data_type": data_type,
        "data_id": data_id,
        "trace": trace,
        "found": len(trace) > 0,
    })


@governance_bp.route("/governance/data-lineage/staleness", methods=["GET"])
def check_staleness():
    """Pipeline health check — returns per-step staleness."""
    lineage = _load_lineage()

    try:
        step_statuses = _check_staleness(lineage)
    except Exception as e:
        logger.error("Staleness check failed: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    fresh = sum(1 for s in step_statuses if s["status"] == "fresh")
    total = len(step_statuses)

    return jsonify({
        "status": "success",
        "steps": step_statuses,
        "health_pct": round(100 * fresh / max(total, 1), 1),
        "as_of": datetime.now().isoformat(),
    })


# ── Field-level lineage ────────────────────────────────────────────


@governance_bp.route("/governance/field-lineage", methods=["GET"])
def get_field_lineage():
    """Return the full field-level lineage registry.

    Optional query param: ?report=<report_key> to filter to one report.
    """
    registry = _load_field_lineage()
    if not registry:
        return jsonify({
            "status": "error",
            "message": "Field lineage registry not found. Run the pipeline first.",
        }), 404

    report_filter = request.args.get("report", "").strip()

    if report_filter:
        reports = registry.get("reports", {})
        if report_filter not in reports:
            return jsonify({
                "status": "error",
                "message": f"Report '{report_filter}' not found in registry",
                "available_reports": list(reports.keys()),
            }), 404
        filtered = {report_filter: reports[report_filter]}
    else:
        filtered = registry.get("reports", {})

    # Build summary
    total_fields = 0
    report_summaries = []
    for rkey, rdata in filtered.items():
        field_count = 0
        for section in rdata.get("sections", {}).values():
            field_count += len(section.get("fields", {}))
        total_fields += field_count
        report_summaries.append({
            "report": rkey,
            "label": rdata.get("label", rkey),
            "generator": rdata.get("generator", ""),
            "section_count": len(rdata.get("sections", {})),
            "field_count": field_count,
        })

    return jsonify({
        "status": "success",
        "version": registry.get("version", "unknown"),
        "reports": filtered,
        "summary": report_summaries,
        "total_fields": total_fields,
        "total_reports": len(filtered),
    })


@governance_bp.route("/governance/field-lineage/lookup", methods=["GET"])
def field_lineage_lookup():
    """Look up lineage for a specific field.

    Query params: ?report=<key>&section=<key>&field=<key>
    Or: ?search=<text> for fuzzy search across all fields.
    """
    registry = _load_field_lineage()
    if not registry:
        return jsonify({"status": "error", "message": "Registry not found"}), 404

    search = request.args.get("search", "").strip().lower()
    report_key = request.args.get("report", "").strip()
    section_key = request.args.get("section", "").strip()
    field_key = request.args.get("field", "").strip()

    reports = registry.get("reports", {})

    # Exact lookup
    if report_key and section_key and field_key:
        report = reports.get(report_key, {})
        section = report.get("sections", {}).get(section_key, {})
        field = section.get("fields", {}).get(field_key)
        if not field:
            return jsonify({
                "status": "error",
                "message": f"Field not found: {report_key}.{section_key}.{field_key}",
            }), 404
        return jsonify({
            "status": "success",
            "report": report_key,
            "section": section_key,
            "field": field_key,
            "lineage": field,
        })

    # Search across all fields
    if search:
        results = []
        for rkey, rdata in reports.items():
            for skey, sdata in rdata.get("sections", {}).items():
                for fkey, fdata in sdata.get("fields", {}).items():
                    searchable = " ".join([
                        fkey, fdata.get("label", ""),
                        fdata.get("source_field", ""),
                        fdata.get("cdm_path", "") or "",
                        fdata.get("computation", ""),
                    ]).lower()
                    if search in searchable:
                        results.append({
                            "report": rkey,
                            "report_label": rdata.get("label", rkey),
                            "section": skey,
                            "field": fkey,
                            "lineage": fdata,
                        })
        return jsonify({
            "status": "success",
            "query": search,
            "results": results,
            "count": len(results),
        })

    return jsonify({
        "status": "error",
        "message": "Provide ?search=<text> or ?report=&section=&field= params",
    }), 400
