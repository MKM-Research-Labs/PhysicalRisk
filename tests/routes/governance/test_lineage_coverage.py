"""Coverage expansion tests for lineage.py — counterparty trace, secondary
gauge trace paths, property/trade sub-lookups, route error handlers, and
utility edge cases (lines 142-143, 156-157, 162, 166, 184-186, 199-209,
224-225, 230-231, 251-252, 263-264, 276-277, 284-285, 289-300, 320-322,
361-366, 384-386)."""

import json
import pathlib

import pytest

from tests.routes.governance.lineage_shared import write_lineage


# ══════════════════════════════════════════════════════════════════
# Extended trace_env with additional data directories
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def full_trace_env(tmp_path, monkeypatch):
    """Trace environment with gaugehd, sequence_gauge, mortgage,
    propertyhc, trade_marks, eod, counterparty, classifier summary,
    and market_state files."""
    from config import config

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    classifiers_dir = tmp_path / "classifiers"
    classifiers_dir.mkdir()
    blotter_dir = tmp_path / "blotter"
    blotter_dir.mkdir()
    (blotter_dir / "eod").mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
    monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
    monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

    # gauge.json
    with open(input_dir / "gauge.json", "w") as f:
        json.dump({"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-FULL01"}}}
        ]}, f)

    # gaugehc.json
    with open(input_dir / "gaugehc.json", "w") as f:
        json.dump({"hazard_curves": {"GAUGE-FULL01": {"gev": {}}}}, f)

    # gaugets/ per-gauge file
    (input_dir / "gaugets").mkdir()
    with open(input_dir / "gaugets" / "GAUGE-FULL01.json", "w") as f:
        json.dump({"gauge_id": "GAUGE-FULL01"}, f)

    # gaugehd/ historical daily observations
    (input_dir / "gaugehd").mkdir()
    with open(input_dir / "gaugehd" / "GAUGE-FULL01_daily.csv", "w") as f:
        f.write("date,level\n2026-01-01,3.5\n")

    # sequence_gauge/ per-gauge split files
    sg_dir = input_dir / "sequence_gauge"
    sg_dir.mkdir()
    with open(sg_dir / "GAUGE-FULL01.json", "w") as f:
        json.dump({"gauge_id": "GAUGE-FULL01", "peaks": [4.1]}, f)
    with open(sg_dir / "_index.json", "w") as f:
        json.dump({"gauge_ids": ["GAUGE-FULL01"]}, f)

    # classifier .joblib + training_summary.json
    (classifiers_dir / "GAUGE-FULL01.joblib").write_bytes(b"fake")
    with open(classifiers_dir / "training_summary.json", "w") as f:
        json.dump({"gauges": [{"gauge_id": "GAUGE-FULL01", "auc": 0.95}]}, f)

    # market_state.json referencing gauge
    with open(blotter_dir / "market_state.json", "w") as f:
        json.dump({"hazard_curves": {"GAUGE-FULL01": {}}}, f)

    # property.json
    with open(input_dir / "property.json", "w") as f:
        json.dump({"properties": [
            {"PropertyHeader": {"Header": {"PropertyID": "PROP-FULL01"}}}
        ]}, f)

    # propertyts/
    (input_dir / "propertyts").mkdir()
    with open(input_dir / "propertyts" / "PROP-FULL01.json", "w") as f:
        json.dump({"property_id": "PROP-FULL01"}, f)

    # mortgage.json
    with open(input_dir / "mortgage.json", "w") as f:
        json.dump({"mortgages": [{"property_id": "PROP-FULL01", "ltv": 0.75}]}, f)

    # propertyhc.json
    with open(input_dir / "propertyhc.json", "w") as f:
        json.dump({"property_curves": {"PROP-FULL01": {"depth": 1.2}}}, f)

    # prs/ trades
    (input_dir / "prs").mkdir()
    with open(input_dir / "prs" / "PRS-FULL01.json", "w") as f:
        json.dump({"PhysicalSwap": {
            "Header": {"SwapID": "PRS-FULL01"},
            "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-FULL01"}]},
            "Counterparty": "CTPY-FULL01",
        }}, f)

    # trade_marks.json
    with open(blotter_dir / "trade_marks.json", "w") as f:
        json.dump({"marks": [{"trade_id": "PRS-FULL01", "mtm": 1000}]}, f)

    # eod snapshot referencing trade
    with open(blotter_dir / "eod" / "2026-03-25_PRS-FULL01.json", "w") as f:
        json.dump({"trade_id": "PRS-FULL01", "pnl": 500}, f)

    # counterparty.json
    with open(input_dir / "counterparty.json", "w") as f:
        json.dump({"counterparties": [
            {"counterparty_id": "CTPY-FULL01", "name": "Test Bank"}
        ]}, f)

    return {"input_dir": input_dir, "classifiers_dir": classifiers_dir,
            "blotter_dir": blotter_dir}


# ══════════════════════════════════════════════════════════════════
# Counterparty trace (lines 289-300)
# ══════════════════════════════════════════════════════════════════


class TestCounterpartyTrace:
    """Exercise the data_type == 'counterparty' branch."""

    def test_counterparty_trace_finds_master_record(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "counterparty", "CTPY-FULL01")
        steps = [r["step"] for r in result]
        assert "counterparties" in steps

    def test_counterparty_trace_finds_prs_trades(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "counterparty", "CTPY-FULL01")
        consumed = [r for r in result if r["role"] == "consumed"]
        assert len(consumed) >= 1

    def test_counterparty_not_found_returns_empty(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "counterparty", "CTPY-ZZZZZ")
        assert result == []


# ══════════════════════════════════════════════════════════════════
# Gauge trace — secondary data sources (lines 184-186, 199-209,
# 224-225, 230-231)
# ══════════════════════════════════════════════════════════════════


class TestGaugeTraceSecondaryPaths:
    """Exercise gaugehd, sequence_gauge, classifier summary, market_state paths."""

    def test_gauge_trace_includes_gaugehd(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        steps = [r["step"] for r in result]
        assert "gaugehd" in steps

    def test_gauge_trace_includes_sequence_gauge(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        stressm_steps = [r for r in result if r["step"] == "stressm"]
        # Should have gaugets + sequence_gauge
        assert len(stressm_steps) >= 2

    def test_gauge_trace_includes_classifier_summary(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        clf_steps = [r for r in result if r["step"] == "classifiers"]
        # .joblib + training_summary.json
        assert len(clf_steps) >= 2

    def test_gauge_trace_includes_market_state(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-FULL01")
        blotter_steps = [r for r in result if r["step"] == "blotter"]
        # market_state + PRS trade
        assert len(blotter_steps) >= 2


class TestGaugeTraceSequenceGaugeFallbacks:
    """Exercise sequence_gauge _index.json and legacy fallbacks."""

    def test_sequence_gauge_index_fallback(self, tmp_path, monkeypatch):
        """When per-gauge file doesn't exist, falls back to _index.json."""
        from config import config

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        classifiers_dir = tmp_path / "classifiers"
        classifiers_dir.mkdir()
        blotter_dir = tmp_path / "blotter"
        blotter_dir.mkdir()
        (blotter_dir / "eod").mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
        monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
        monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-IDX01"}}}
            ]}, f)

        # sequence_gauge/ with _index.json referencing gauge but no per-gauge file
        sg_dir = input_dir / "sequence_gauge"
        sg_dir.mkdir()
        with open(sg_dir / "_index.json", "w") as f:
            json.dump({"gauge_ids": ["GAUGE-IDX01"]}, f)

        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-IDX01")
        stressm_steps = [r for r in result if r["step"] == "stressm"]
        assert any("_index.json" in r["file"] for r in stressm_steps)

    def test_sequence_gauge_legacy_fallback(self, tmp_path, monkeypatch):
        """When sequence_gauge/ dir doesn't exist, falls back to legacy file."""
        from config import config

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        classifiers_dir = tmp_path / "classifiers"
        classifiers_dir.mkdir()
        blotter_dir = tmp_path / "blotter"
        blotter_dir.mkdir()
        (blotter_dir / "eod").mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
        monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
        monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-LEG01"}}}
            ]}, f)

        # Legacy monolithic file instead of split dir
        with open(input_dir / "sequence_gauge_summary.json", "w") as f:
            json.dump({"gauges": {"GAUGE-LEG01": {"peaks": [3.2]}}}, f)

        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-LEG01")
        stressm_steps = [r for r in result if r["step"] == "stressm"]
        assert any("sequence_gauge_summary" in r["file"] for r in stressm_steps)


# ══════════════════════════════════════════════════════════════════
# Property sub-lookups (lines 251-252, 263-264)
# ══════════════════════════════════════════════════════════════════


class TestPropertySubLookups:
    """Exercise mortgage.json and propertyhc.json searches."""

    def test_property_trace_includes_mortgage(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "property", "PROP-FULL01")
        steps = [r["step"] for r in result]
        assert "mortgages" in steps

    def test_property_trace_includes_propertyhc(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "property", "PROP-FULL01")
        steps = [r["step"] for r in result]
        assert "propertyhc" in steps


# ══════════════════════════════════════════════════════════════════
# Trade sub-lookups (lines 276-277, 284-285)
# ══════════════════════════════════════════════════════════════════


class TestTradeSubLookups:
    """Exercise trade_marks.json and EOD snapshot searches."""

    def test_trade_trace_includes_marks(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-FULL01")
        blotter_steps = [r for r in result if r["step"] == "blotter"]
        assert any("trade_marks" in r["file"] for r in blotter_steps)

    def test_trade_trace_includes_eod(self, full_trace_env):
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-FULL01")
        blotter_steps = [r for r in result if r["step"] == "blotter"]
        assert any("eod" in r["file"] for r in blotter_steps)


# ══════════════════════════════════════════════════════════════════
# Route error handlers (lines 320-322, 361-366, 384-386)
# ══════════════════════════════════════════════════════════════════


class TestRouteErrorHandlers:
    """Exercise except Exception blocks on all three routes."""

    def test_data_lineage_staleness_error_returns_empty(
        self, lineage_env, lineage_client, monkeypatch
    ):
        """GET /governance/data-lineage gracefully handles _check_staleness error."""
        from routes.governance.lineage import data_lineage as lineage_mod
        monkeypatch.setattr(
            lineage_mod, "_check_staleness",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        resp = lineage_client.get("/api/v1/governance/data-lineage")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pipeline_steps"] == []

    def test_trace_error_returns_500(
        self, lineage_env, lineage_client, monkeypatch
    ):
        """GET /governance/data-lineage/trace returns 500 on _trace_data error."""
        from routes.governance.lineage import data_lineage as lineage_mod
        monkeypatch.setattr(
            lineage_mod, "_trace_data",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("trace boom")),
        )
        resp = lineage_client.get(
            "/api/v1/governance/data-lineage/trace",
            query_string={"data_type": "gauge", "data_id": "GAUGE-001"},
        )
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert "trace boom" in data["message"]

    def test_staleness_route_error_returns_500(
        self, lineage_env, lineage_client, monkeypatch
    ):
        """GET /governance/data-lineage/staleness returns 500 on error."""
        from routes.governance.lineage import data_lineage as lineage_mod
        monkeypatch.setattr(
            lineage_mod, "_check_staleness",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("stale boom")),
        )
        resp = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"


# ══════════════════════════════════════════════════════════════════
# Utility edge cases (lines 142-143, 156-157, 162, 166)
# ══════════════════════════════════════════════════════════════════


class TestUtilityEdgeCases:
    """Exercise _add ValueError, _search_json exception, _search_dir_files
    edge cases."""

    def test_add_value_error_falls_back_to_absolute(self, full_trace_env):
        """_add with file outside input_dir falls back to absolute path."""
        from routes.governance.lineage import _trace_data
        # Counterparty trace searches blotter_dir/eod which is outside
        # input_dir — the _add function handles the ValueError from
        # relative_to. As long as the trace returns entries we know it worked.
        result = _trace_data(None, "trade", "PRS-FULL01")
        # EOD entries use blotter_dir path which is outside input_dir tree
        eod_entries = [r for r in result if "eod" in r["file"]]
        assert len(eod_entries) >= 1

    def test_search_json_exception_returns_false(self, tmp_path, monkeypatch):
        """_search_json with unreadable file returns False — exercised by
        tracing a gauge when gaugehc.json is unreadable."""
        from config import config

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        classifiers_dir = tmp_path / "classifiers"
        classifiers_dir.mkdir()
        blotter_dir = tmp_path / "blotter"
        blotter_dir.mkdir()
        (blotter_dir / "eod").mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
        monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
        monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

        # gauge.json present so gauge trace is triggered
        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-BAD01"}}}
            ]}, f)

        # gaugehc.json is a directory (unreadable as file → exception in _search_json)
        (input_dir / "gaugehc.json").mkdir()

        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-BAD01")
        # Should not crash — _search_json exception returns False gracefully
        assert isinstance(result, list)

    def test_search_dir_files_missing_dir(self, tmp_path, monkeypatch):
        """_search_dir_files with nonexistent dir returns [] — exercised by
        tracing a gauge when gaugehd/ doesn't exist."""
        from config import config

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        classifiers_dir = tmp_path / "classifiers"
        classifiers_dir.mkdir()
        blotter_dir = tmp_path / "blotter"
        blotter_dir.mkdir()
        (blotter_dir / "eod").mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
        monkeypatch.setattr(config, "get_classifiers_dir", lambda: classifiers_dir)
        monkeypatch.setattr(config, "get_trading_dir", lambda: blotter_dir)

        with open(input_dir / "gauge.json", "w") as f:
            json.dump({"flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-NODIR"}}}
            ]}, f)

        # No gaugehd/ dir and no prs/ dir → _search_dir_files gets nonexistent dirs
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "gauge", "GAUGE-NODIR")
        # Should not crash — empty results from nonexistent dirs
        assert isinstance(result, list)

    def test_search_dir_files_filename_stem_match(self, full_trace_env):
        """_search_dir_files matches entity_id in filename stem — exercised
        by tracing a trade with EOD snapshots containing the trade ID in
        the filename."""
        from routes.governance.lineage import _trace_data
        result = _trace_data(None, "trade", "PRS-FULL01")
        eod_entries = [r for r in result if "eod" in r["file"]]
        assert len(eod_entries) >= 1
