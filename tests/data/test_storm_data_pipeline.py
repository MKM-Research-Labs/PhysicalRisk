# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data availability tests — Storm scenarios (pipeline completeness).

Verifies that all files required by the stress test module are present
on disk and structurally correct.  These tests use the real production
data files, not fixtures.

Run `python app.py port --gaugets` to (re)generate stress_storms.json.
Run `python app.py port --stressm`  to retrain GBM flood classifiers.
"""

import json
import pathlib
import pytest

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))
from config import PortfolioConfig

config = PortfolioConfig()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

STRESS_STORMS_DIR   = pathlib.Path(config.get_input_dir()) / "stress_storms"
STRESS_STORMS_INDEX = STRESS_STORMS_DIR / "_index.json"
# Legacy single-file fallback
STRESS_STORMS_PATH  = pathlib.Path(config.get_input_dir()) / "stress_storms.json"
GAUGETS_DIR         = pathlib.Path(config.get_gaugets_dir())
STRESS_MODEL_DIR    = pathlib.Path(config.get_stressm_dir())
TRAINING_SUMMARY    = STRESS_MODEL_DIR / "training_summary.json"
GAUGEHC_PATH        = pathlib.Path(config.get_input_dir()) / "gaugehc.json"

PROPERTYTS_DIR       = pathlib.Path(config.get_input_dir()) / "propertyts"

STORM_REQUIRED_FIELDS = {
    "storm_id", "name", "intensity_category", "duration_hours",
    "peak_position", "trigger_summary", "gauge_responses",
}
TRIGGER_SUMMARY_FIELDS = {
    "gauges_alert", "gauges_warning", "gauges_severe", "gauges_impacted", "max_trigger",
}
GAUGE_RESPONSE_FIELDS = {
    "gauge_id", "peak_level_m",
    "exceeded_alert", "exceeded_warning", "exceeded_severe",
}
MIN_STORM_COUNT = 100
MIN_AUC = 0.90
MIN_CLASSIFIERS = 40


# ---------------------------------------------------------------------------
# Pipeline output completeness (catches sequencing bugs)
# ---------------------------------------------------------------------------

GAUGE_JSON = pathlib.Path(config.get_input_dir()) / "gauge.json"
GAUGEHC_JSON = pathlib.Path(config.get_input_dir()) / "gaugehc.json"
PROPERTYHC_JSON = pathlib.Path(config.get_input_dir()) / "propertyhc.json"
PROPERTY_JSON = pathlib.Path(config.get_input_dir()) / "property.json"
PRS_DIR = pathlib.Path(config.get_reports_dir('prs')) if hasattr(config, 'get_reports_dir') else None


class TestPipelineCompleteness:
    """Verify that pipeline outputs are complete — not partial from stale data.

    These tests catch the recurring bug where step N reads stale output from
    step M, producing fewer records than expected.
    """

    def test_hazard_curves_match_gauge_count(self):
        """gaugehc.json must have one curve per gauge in gauge.json.

        If this fails, gaugehc.json was built from stale gaugets data.
        Fix: python app.py port --hazard
        """
        if not GAUGE_JSON.exists() or not GAUGEHC_JSON.exists():
            pytest.skip("gauge.json or gaugehc.json missing")

        with open(GAUGE_JSON) as f:
            n_gauges = len(json.load(f).get("flood_gauges", []))
        with open(GAUGEHC_JSON) as f:
            n_curves = len(json.load(f).get("hazard_curves", {}))

        assert n_curves == n_gauges, (
            f"gaugehc.json has {n_curves} curves but gauge.json has {n_gauges} gauges. "
            "Run `python app.py port --hazard` to rebuild."
        )

    def test_property_hazard_curves_match_property_count(self):
        """propertyhc.json must have one curve per property in property.json.

        Fix: python app.py port --propertyhc
        """
        if not PROPERTY_JSON.exists() or not PROPERTYHC_JSON.exists():
            pytest.skip("property.json or propertyhc.json missing")

        with open(PROPERTY_JSON) as f:
            n_props = len(json.load(f).get("properties", []))
        with open(PROPERTYHC_JSON) as f:
            n_curves = len(json.load(f).get("property_hazard_curves", {}))

        assert n_curves == n_props, (
            f"propertyhc.json has {n_curves} curves but property.json has {n_props} properties. "
            "Run `python app.py port --propertyhc` to rebuild."
        )

    def test_trade_gauges_exist_in_gauge_json(self):
        """Every gauge referenced by PRS trades must exist in gauge.json.

        If this fails, the blotter was generated from a previous gauge.json
        with different IDs. Fix: python app.py port --blotter
        """
        if not GAUGE_JSON.exists():
            pytest.skip("gauge.json missing")

        prs_dir = pathlib.Path(config.get_reports_dir('prs')) if hasattr(config, 'get_reports_dir') else None
        if prs_dir is None or not prs_dir.exists():
            pytest.skip("PRS directory not configured")

        with open(GAUGE_JSON) as f:
            gauge_ids = {
                g.get('FloodGauge', {}).get('Header', {}).get('GaugeID', '')
                for g in json.load(f).get('flood_gauges', [])
            }

        trade_gauge_ids = set()
        for tf in prs_dir.glob('PRS-*.json'):
            try:
                with open(tf) as f:
                    td = json.load(f)
                for g in td.get('PhysicalSwap', {}).get('GaugeSet', {}).get('GaugeBasket', []):
                    gid = g.get('GaugeID', '')
                    if gid:
                        trade_gauge_ids.add(gid)
            except Exception:
                continue

        if not trade_gauge_ids:
            pytest.skip("No trades with gauge IDs found")

        missing = trade_gauge_ids - gauge_ids
        assert not missing, (
            f"{len(missing)} trade gauge IDs not in gauge.json: {sorted(missing)[:5]}. "
            "Trades reference gauges from a previous generation. "
            "Run `python app.py port --blotter` to regenerate."
        )

    def test_gaugets_match_gauge_count(self):
        """gaugets/ must have one file per gauge in gauge.json.

        Fix: python app.py port --stressm
        """
        if not GAUGE_JSON.exists():
            pytest.skip("gauge.json missing")

        gaugets_dir = pathlib.Path(config.get_gaugets_dir())
        if not gaugets_dir.exists():
            pytest.skip("gaugets/ directory missing")

        with open(GAUGE_JSON) as f:
            n_gauges = len(json.load(f).get("flood_gauges", []))

        n_files = len(list(gaugets_dir.glob("GAUGE-*.json")))
        assert n_files == n_gauges, (
            f"gaugets/ has {n_files} files but gauge.json has {n_gauges} gauges. "
            "Run `python app.py port --stressm` to rebuild."
        )
