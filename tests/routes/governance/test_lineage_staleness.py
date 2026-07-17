# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for governance data lineage staleness route."""

import pytest

from tests.routes.governance.lineage_shared import (
    create_fresh_file,
    create_stale_file,
)


# ══════════════════════════════════════════════════════════════════
# GET /governance/data-lineage/staleness
# ══════════════════════════════════════════════════════════════════


class TestStalenessRoute:

    def test_all_missing_zero_health(self, lineage_env, lineage_client):
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["health_pct"] == 0.0
        assert len(data["steps"]) == len(_PIPELINE_STEPS)

    def test_all_fresh_full_health(self, lineage_env, lineage_client):
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        tmp = lineage_env["tmp_path"]
        for step_def in _PIPELINE_STEPS:
            output = step_def["output"]
            if output.endswith("/"):
                create_fresh_file(tmp, f"{output}dummy.json")
            else:
                create_fresh_file(tmp, output)

        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        data = r.get_json()
        assert data["health_pct"] == 100.0

    def test_partial_health(self, lineage_env, lineage_client):
        from routes.governance.lineage._trace import _PIPELINE_STEPS
        tmp = lineage_env["tmp_path"]
        create_fresh_file(tmp, "gauge.json")
        # gauge.json is the representative output for both gauges and
        # synthetic_gauges, so creating it freshens both.
        fresh_count = sum(1 for s in _PIPELINE_STEPS if s["output"] == "gauge.json")
        expected_pct = round(100.0 * fresh_count / len(_PIPELINE_STEPS), 1)
        r = lineage_client.get("/api/v1/governance/data-lineage/staleness")
        data = r.get_json()
        assert data["health_pct"] == pytest.approx(expected_pct, abs=0.1)

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
