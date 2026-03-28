# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage query functions — provenance tracing, file/step lineage.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_manifest(steps: dict) -> dict:
    """Helper to build a manifest dict for testing."""
    return {"runs": {}, "steps": steps}


# ---------------------------------------------------------------------------
# query.py tests
# ---------------------------------------------------------------------------

class TestOutputToStep:
    """_output_to_step: reverse mapping."""

    def test_known_outputs(self):
        from lineage.query import _output_to_step
        m = _output_to_step()
        # synthetic_gauges is the last writer of gauge.json in STEP_IO order
        assert m["gauge.json"] == "synthetic_gauges"
        assert m["property.json"] == "properties"
        assert m["gaugehd/"] == "gaugehd"


class TestInputToStep:
    """_input_to_step: reverse mapping of consumers."""

    def test_known_inputs(self):
        from lineage.query import _input_to_step
        m = _input_to_step()
        assert "properties" in m["gauge.json"]
        assert "gaugehd" in m["gauge.json"]


class TestWalkUpstream:
    """_walk_upstream: DFS dependency resolution."""

    def test_root_has_no_upstream(self):
        from lineage.query import _walk_upstream
        result = _walk_upstream("gauges")
        assert result == ["gauges"]

    def test_mid_chain(self):
        from lineage.query import _walk_upstream
        result = _walk_upstream("properties")
        assert "gauges" in result
        assert result.index("gauges") < result.index("properties")

    def test_deep_chain(self):
        from lineage.query import _walk_upstream
        result = _walk_upstream("propertyhc")
        # propertyhc depends on propertyts, hazard, which depend on gauges, stressm, etc.
        assert "gauges" in result
        assert "propertyhc" in result

    def test_cycle_safety(self):
        """_walk_upstream should not infinite loop on revisited nodes."""
        from lineage.query import _walk_upstream
        # stressm depends on gauges,gaugehd; hazard depends on gauges,stressm
        result = _walk_upstream("hazard")
        # gauges should appear only once
        assert result.count("gauges") == 1


class TestTraceDataPoint:
    """trace_data_point: provenance chain for data IDs."""

    def test_gauge_id_chain(self):
        from lineage.query import trace_data_point
        manifest = _make_manifest({
            "gauges": {"run_id": "r1", "timestamp": "t1", "status": "success"},
            "stressm": {"run_id": "r1", "timestamp": "t1", "status": "success"},
        })
        with patch("lineage.query.load_manifest", return_value=manifest):
            chain = trace_data_point("gauge_id", "GAUGE-abc123")
        assert len(chain) == 4  # gauges, gaugehd, stressm, hazard
        assert chain[0]["step"] == "gauges"
        assert chain[0]["recorded"] is True
        assert chain[0]["data_id"] == "GAUGE-abc123"
        # gaugehd not in manifest → recorded=False
        assert chain[1]["step"] == "gaugehd"
        assert chain[1]["recorded"] is False

    def test_property_id_chain(self):
        from lineage.query import trace_data_point
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            chain = trace_data_point("property_id", "PROP-001")
        # properties, propertyts, propertytsd, propertytse, propertyhc, propertyshd, propertyshe
        assert len(chain) == 7
        assert all(c["recorded"] is False for c in chain)

    def test_unknown_data_type(self):
        from lineage.query import trace_data_point
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            chain = trace_data_point("unknown_type", "X-001")
        assert chain == []


class TestGetFileLineage:
    """get_file_lineage: producer/consumer lookup."""

    def test_known_file(self):
        from lineage.query import get_file_lineage
        manifest = _make_manifest({
            "gauges": {"run_id": "r1", "timestamp": "t1"},
            "synthetic_gauges": {"run_id": "r2", "timestamp": "t2"},
        })
        with patch("lineage.query.load_manifest", return_value=manifest):
            result = get_file_lineage("gauge.json")
        # synthetic_gauges is the last writer of gauge.json in STEP_IO order
        assert result["produced_by"] == "synthetic_gauges"
        assert result["producer_run_id"] == "r2"
        assert "properties" in result["consumed_by"]

    def test_unknown_file(self):
        from lineage.query import get_file_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_file_lineage("nonexistent.json")
        assert result["produced_by"] is None
        assert result["producer_run_id"] is None
        assert result["consumed_by"] == []

    def test_file_with_no_producer_entry(self):
        """Producer step exists in STEP_IO but not in manifest."""
        from lineage.query import get_file_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_file_lineage("gauge.json")
        # synthetic_gauges is the last writer of gauge.json in topo order
        assert result["produced_by"] == "synthetic_gauges"
        assert result["producer_run_id"] is None  # not in manifest


class TestGetStepLineage:
    """get_step_lineage: upstream/downstream tree."""

    def test_root_step(self):
        from lineage.query import get_step_lineage
        manifest = _make_manifest({
            "gauges": {"run_id": "r1", "timestamp": "t1"},
        })
        with patch("lineage.query.load_manifest", return_value=manifest):
            result = get_step_lineage("gauges")
        assert result["upstream"] == []
        assert "properties" in result["downstream"]
        assert result["last_run"] == "r1"
        assert result["inputs"] == []
        assert "gauge.json" in result["outputs"]

    def test_mid_step(self):
        from lineage.query import get_step_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_step_lineage("properties")
        assert "gauges" in result["upstream"]
        assert "mortgages" in result["downstream"]
        assert result["last_run"] is None

    def test_step_not_in_manifest(self):
        from lineage.query import get_step_lineage
        with patch("lineage.query.load_manifest", return_value=_make_manifest({})):
            result = get_step_lineage("gauges")
        assert result["last_run"] is None
        assert result["last_timestamp"] is None
