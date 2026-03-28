"""Tests for governance data lineage and trace routes."""

from tests.routes.governance.lineage_shared import (
    SAMPLE_LINEAGE,
    create_fresh_file,
    create_stale_file,
    write_lineage,
)


# ══════════════════════════════════════════════════════════════════
# GET /governance/data-lineage route
# ══════════════════════════════════════════════════════════════════


class TestGetDataLineage:

    def test_with_no_manifest(self, lineage_env, lineage_client):
        """When lineage file does not exist, manifest is None but route succeeds."""
        r = lineage_client.get("/api/v1/governance/data-lineage")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["manifest"] is None
        assert data["summary"]["missing"] == 14
        assert data["summary"]["health"] == "unhealthy"

    def test_all_fresh(self, lineage_env, lineage_client):
        """All pipeline outputs exist and are fresh."""
        tmp = lineage_env["tmp_path"]
        for step_out in [
            "gauge.json", "property.json", "mortgage.json",
            "gaugehc.json", "propertyhc.json", "propertyshd.json",
            "propertyshe.json", "counterparty.json",
        ]:
            create_fresh_file(tmp, step_out)
        for dir_out in ["gaugehd", "gaugets", "propertyts", "propertytsd",
                         "propertytse", "prs"]:
            create_fresh_file(tmp, f"{dir_out}/dummy.json")

        write_lineage(lineage_env, SAMPLE_LINEAGE)

        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert data["status"] == "success"
        assert data["summary"]["fresh"] == 14
        assert data["summary"]["stale"] == 0
        assert data["summary"]["missing"] == 0
        assert data["summary"]["health"] == "healthy"
        assert data["manifest"] is not None

    def test_mixed_statuses(self, lineage_env, lineage_client):
        """Mix of fresh, stale, and missing."""
        tmp = lineage_env["tmp_path"]
        create_fresh_file(tmp, "gauge.json")
        create_stale_file(tmp, "property.json", days_old=5)

        write_lineage(lineage_env, SAMPLE_LINEAGE)

        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert data["summary"]["fresh"] == 1
        assert data["summary"]["stale"] == 1
        assert data["summary"]["missing"] == 12
        assert data["summary"]["health"] == "unhealthy"

    def test_degraded_health(self, lineage_env, lineage_client):
        """All present but some stale = degraded."""
        tmp = lineage_env["tmp_path"]
        for step_out in [
            "gauge.json", "property.json", "mortgage.json",
            "gaugehc.json", "propertyhc.json", "propertyshd.json",
            "propertyshe.json", "counterparty.json",
        ]:
            create_fresh_file(tmp, step_out)
        for dir_out in ["gaugehd", "gaugets", "propertyts", "propertytsd",
                         "propertytse", "prs"]:
            create_fresh_file(tmp, f"{dir_out}/dummy.json")

        # Make one stale
        create_stale_file(tmp, "gauge.json", days_old=5)

        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert data["summary"]["missing"] == 0
        assert data["summary"]["stale"] == 1
        assert data["summary"]["health"] == "degraded"

    def test_has_as_of(self, lineage_env, lineage_client):
        """Response includes as_of timestamp."""
        r = lineage_client.get("/api/v1/governance/data-lineage")
        data = r.get_json()
        assert "as_of" in data


# ══════════════════════════════════════════════════════════════════
# GET /governance/data-lineage/trace
# ══════════════════════════════════════════════════════════════════


class TestTraceDataLineageRoute:

    def test_missing_params(self, lineage_env, lineage_client):
        """Missing data_type or data_id returns 400."""
        r = lineage_client.get("/api/v1/governance/data-lineage/trace")
        assert r.status_code == 400
        assert "required" in r.get_json()["message"]

    def test_missing_data_id(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/data-lineage/trace?data_type=gauge")
        assert r.status_code == 400

    def test_missing_data_type(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/data-lineage/trace?data_id=GAUGE-001")
        assert r.status_code == 400

    def test_whitespace_only_params(self, lineage_env, lineage_client):
        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=%20&data_id=%20"
        )
        assert r.status_code == 400

    def test_valid_trace(self, lineage_env, lineage_client):
        import json as _json
        from pathlib import Path

        write_lineage(lineage_env, SAMPLE_LINEAGE)

        # Create gauge.json with GAUGE-001 so file-scan trace finds it
        tmp = lineage_env["tmp_path"]
        gauge_data = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}]}
        (tmp / "gauge.json").write_text(_json.dumps(gauge_data))
        # Create gaugehc.json referencing GAUGE-001
        hc_data = {"hazard_curves": {"GAUGE-001": {"annual_flood_prob_alert": 0.1}}}
        (tmp / "gaugehc.json").write_text(_json.dumps(hc_data))

        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-001"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["found"] is True
        assert len(data["trace"]) >= 1
        assert data["data_type"] == "gauge"
        assert data["data_id"] == "GAUGE-001"

    def test_trace_not_found(self, lineage_env, lineage_client):
        write_lineage(lineage_env, SAMPLE_LINEAGE)

        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-999"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is False
        assert data["trace"] == []

    def test_trace_no_manifest(self, lineage_env, lineage_client):
        """No lineage file => found=False, empty trace."""
        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=gauge&data_id=GAUGE-001"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is False

    def test_trace_fallback_scan(self, lineage_env, lineage_client):
        """Fallback scan when no direct traces key matches."""
        lineage = {
            "steps": {
                "gauges": {"outputs": ["GAUGE-XYZ.json"]},
            },
        }
        write_lineage(lineage_env, lineage)

        r = lineage_client.get(
            "/api/v1/governance/data-lineage/trace?data_type=storm&data_id=GAUGE-XYZ"
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is True
        assert len(data["trace"]) == 1
