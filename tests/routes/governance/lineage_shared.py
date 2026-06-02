"""Shared sample data and helper functions for lineage tests."""

import json
import os
import time


# ── Sample data ──────────────────────────────────────────────────

SAMPLE_LINEAGE = {
    "steps": {
        "gauges": {"last_run": "2026-03-18T10:00:00", "outputs": ["gauge.json"]},
        "properties": {"last_run": "2026-03-18T10:05:00", "outputs": ["property.json"]},
        "mortgages": {"last_run": None, "outputs": ["loan.json"]},
    },
    "traces": {
        "gauge": {
            "GAUGE-001": [
                {"step": "gauges", "role": "output", "file": "gauge.json"},
                {"step": "hazard", "role": "input", "file": "gaugehc.json"},
            ],
        },
        "property": {
            "PROP-001": [
                {"step": "properties", "role": "output", "file": "property.json"},
            ],
        },
    },
}

SAMPLE_FIELD_LINEAGE = {
    "version": "1.0.0",
    "reports": {
        "flood_risk": {
            "label": "Flood Risk Report",
            "generator": "src/reports/flood.py",
            "sections": {
                "summary": {
                    "fields": {
                        "gauge_id": {
                            "label": "Gauge ID",
                            "source_field": "flood_gauges[].gauge_id",
                            "cdm_path": "gauge.gauge_id",
                            "computation": "direct lookup",
                        },
                        "flood_depth": {
                            "label": "Flood Depth",
                            "source_field": "flood_gauges[].depth",
                            "cdm_path": "gauge.depth",
                            "computation": "interpolated from GEV",
                        },
                    },
                },
                "detail": {
                    "fields": {
                        "return_period": {
                            "label": "Return Period",
                            "source_field": "hazard_curves[].return_period",
                            "cdm_path": None,
                            "computation": "GEV inverse CDF",
                        },
                    },
                },
            },
        },
        "prs_pricing": {
            "label": "PRS Pricing Report",
            "generator": "src/reports/prs.py",
            "sections": {
                "trades": {
                    "fields": {
                        "spread": {
                            "label": "PRS Spread",
                            "source_field": "prs[].spread_bps",
                            "cdm_path": "prs.spread",
                            "computation": "analytical CDS pricer",
                        },
                    },
                },
            },
        },
    },
}


# ── Helpers ──────────────────────────────────────────────────────

def write_lineage(env, data):
    with open(env["lineage_path"], "w") as f:
        json.dump(data, f)


def write_field_lineage(env, data):
    with open(env["field_lineage_path"], "w") as f:
        json.dump(data, f)


def create_fresh_file(tmp_path, relpath):
    """Create a file with current mtime (fresh)."""
    full = tmp_path / relpath
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text("{}")


def create_stale_file(tmp_path, relpath, days_old=5):
    """Create a file with old mtime (stale)."""
    full = tmp_path / relpath
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text("{}")
    old_time = time.time() - days_old * 86400
    os.utime(str(full), (old_time, old_time))
