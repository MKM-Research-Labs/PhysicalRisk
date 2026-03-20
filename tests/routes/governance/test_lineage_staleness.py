"""Tests for governance data lineage staleness route."""

from tests.routes.governance.lineage_shared import (
    create_fresh_file,
    create_stale_file,
)


# ══════════════════════════════════════════════════════════════════
# GET /governance/data-lineage/staleness
# ══════════════════════════════════════════════════════════════════


class TestStalenessRoute:

    def test_all_missing_zero_health(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["health_pct"] == 0.0
        assert len(data["steps"]) == 10

    def test_all_fresh_full_health(self, lineage_env, lineage_client):
        tmp = lineage_env["tmp_path"]
        for step_out in [
            "gauge.json", "property.json", "mortgage.json",
            "gaugehc.json", "propertyhc.json", "counterparty.json",
        ]:
            create_fresh_file(tmp, step_out)
        for dir_out in ["gaugehd", "gaugets", "propertyts", "prs"]:
            create_fresh_file(tmp, f"{dir_out}/dummy.json")

        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        data = r.get_json()
        assert data["health_pct"] == 100.0

    def test_partial_health(self, lineage_env, lineage_client):
        tmp = lineage_env["tmp_path"]
        create_fresh_file(tmp, "gauge.json")
        # 1 out of 10 fresh => 10%
        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        data = r.get_json()
        assert data["health_pct"] == 10.0

    def test_stale_does_not_count_as_fresh(self, lineage_env, lineage_client):
        tmp = lineage_env["tmp_path"]
        create_stale_file(tmp, "gauge.json", days_old=5)

        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        data = r.get_json()
        assert data["health_pct"] == 0.0

    def test_has_as_of(self, lineage_env, lineage_client):
        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        data = r.get_json()
        assert "as_of" in data
