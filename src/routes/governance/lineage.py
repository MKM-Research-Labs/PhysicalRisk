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
    """Trace a data_type/data_id through the pipeline.

    Returns a list of provenance steps showing where the ID appears.
    """
    if not lineage:
        return []

    trace_results = []
    traces = lineage.get("traces", {})
    type_traces = traces.get(data_type, {})
    id_trace = type_traces.get(data_id, [])

    if id_trace:
        return id_trace

    # Fallback: scan steps for references to the ID
    for step_name, step_data in lineage.get("steps", {}).items():
        outputs = step_data.get("outputs", [])
        for output in outputs:
            if data_id in str(output):
                trace_results.append({
                    "step": step_name,
                    "role": "output",
                    "file": output if isinstance(output, str) else str(output),
                })
        inputs = step_data.get("inputs", [])
        for inp in inputs:
            if data_id in str(inp):
                trace_results.append({
                    "step": step_name,
                    "role": "input",
                    "file": inp if isinstance(inp, str) else str(inp),
                })

    return trace_results


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
