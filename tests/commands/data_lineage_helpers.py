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

"""Shared sample data and helpers for data_lineage report tests."""


# ---------------------------------------------------------------------------
# Sample data constants
# ---------------------------------------------------------------------------

SAMPLE_MANIFEST = {
    "runs": {
        "run-20260320-120000": ["gauges", "properties", "hazard"],
    },
    "steps": {
        "gauges": {
            "run_id": "run-20260320-120000",
            "timestamp": "2026-03-20T12:00:00",
            "generator": "port (step 1)",
            "status": "success",
            "elapsed_seconds": 2.5,
            "parameters": {"catchment": "thames"},
            "inputs": {},
            "outputs": {
                "gauge.json": {
                    "hash": "abc123def456",
                    "type": "file",
                },
            },
        },
        "properties": {
            "run_id": "run-20260320-120100",
            "timestamp": "2026-03-20T12:01:00",
            "generator": "port (step 2)",
            "status": "success",
            "elapsed_seconds": 1.8,
            "parameters": {},
            "inputs": {
                "gauge.json": {
                    "hash": "abc123def456",
                    "type": "file",
                },
            },
            "outputs": {
                "property.json": {
                    "hash": "789ghi012jkl",
                    "type": "file",
                },
            },
        },
        "hazard": {
            "run_id": "run-20260320-120200",
            "timestamp": "2026-03-20T12:02:00",
            "generator": "port (step 6)",
            "status": "success",
            "elapsed_seconds": 5.1,
            "parameters": {"model": "gev"},
            "inputs": {
                "gauge.json": {
                    "hash": "abc123def456",
                    "type": "file",
                },
            },
            "outputs": {
                "gaugehc.json": {
                    "hash": "mno345pqr678",
                    "type": "file",
                },
            },
        },
    },
}

SAMPLE_LINEAGE_RESULTS = {
    "total": 15,
    "passed": 14,
    "failed": 1,
    "skipped": 0,
    "failures": [
        {
            "name": "test_trade_gauges_exist_in_gauge_json",
            "message": "1 trade gauge_id not found in gauge.json",
        },
    ],
}

SAMPLE_LINEAGE_RESULTS_STALE = {
    "total": 19,
    "passed": 15,
    "failed": 1,
    "skipped": 3,
    "failures": [
        {
            "name": "test_no_stale_inputs",
            "message": "1 pipeline steps have stale inputs: ['propertyhc']",
        },
    ],
}

SAMPLE_LINEAGE_RESULTS_MULTI_FAIL = {
    "total": 19,
    "passed": 9,
    "failed": 10,
    "skipped": 0,
    "failures": [
        {"name": "test_no_stale_inputs",
         "message": "2 pipeline steps have stale inputs"},
        {"name": "test_gauge_id_consistency",
         "message": "3 orphan IDs in gaugehc.json"},
    ],
}

SAMPLE_LINEAGE_RESULTS_CLEAN = {
    "total": 15,
    "passed": 15,
    "failed": 0,
    "skipped": 0,
    "failures": [],
}

SAMPLE_CHAIN_CONSISTENT = {
    "is_consistent": True,
    "stale_steps": [],
    "missing_steps": [],
    "details": {},
}

SAMPLE_CHAIN_ISSUES = {
    "is_consistent": False,
    "stale_steps": ["hazard", "blotter"],
    "missing_steps": ["propertyhc"],
    "details": {
        "hazard": [
            "Input 'gauge.json' is stale: producer 'gauges' hash "
            "changed (abc123.. -> def456..)",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helper functions (called by pytest fixtures in each test file)
# ---------------------------------------------------------------------------

def get_dl_mod():
    """Import and return the data_lineage module."""
    from docs.models import data_lineage
    return data_lineage


def make_sample_data_consistent():
    """Return collected data dict with a consistent pipeline."""
    return {
        "manifest": SAMPLE_MANIFEST,
        "graph": {
            "gauges": [],
            "properties": ["gauges"],
            "hazard": ["gauges"],
        },
        "step_io": {
            "gauges": {"inputs": [], "outputs": ["gauge.json"]},
            "properties": {"inputs": ["gauge.json"],
                           "outputs": ["property.json"]},
            "hazard": {"inputs": ["gauge.json"],
                       "outputs": ["gaugehc.json"]},
        },
        "chain_result": SAMPLE_CHAIN_CONSISTENT,
        "lineage_results": SAMPLE_LINEAGE_RESULTS_CLEAN,
        "step_details": [
            {
                "step": "gauges",
                "dependencies": [],
                "inputs": [],
                "outputs": ["gauge.json"],
                "generator": "port (step 1)",
                "run_id": "run-20260320-120000",
                "timestamp": "2026-03-20T12:00:00",
                "elapsed_s": 2.5,
                "status": "fresh",
                "hash_status": "success",
                "parameters": {"catchment": "thames"},
                "input_hashes": {},
                "output_hashes": {"gauge.json": {"hash": "abc123"}},
            },
            {
                "step": "properties",
                "dependencies": ["gauges"],
                "inputs": ["gauge.json"],
                "outputs": ["property.json"],
                "generator": "port (step 2)",
                "run_id": "run-20260320-120100",
                "timestamp": "2026-03-20T12:01:00",
                "elapsed_s": 1.8,
                "status": "fresh",
                "hash_status": "success",
                "parameters": {},
                "input_hashes": {"gauge.json": {"hash": "abc123"}},
                "output_hashes": {"property.json": {"hash": "789ghi"}},
            },
            {
                "step": "hazard",
                "dependencies": ["gauges"],
                "inputs": ["gauge.json"],
                "outputs": ["gaugehc.json"],
                "generator": "port (step 6)",
                "run_id": "run-20260320-120200",
                "timestamp": "2026-03-20T12:02:00",
                "elapsed_s": 5.1,
                "status": "fresh",
                "hash_status": "success",
                "parameters": {"model": "gev"},
                "input_hashes": {"gauge.json": {"hash": "abc123"}},
                "output_hashes": {"gaugehc.json": {"hash": "mno345"}},
            },
        ],
        "num_runs": 1,
        "num_steps": 3,
        "num_recorded": 3,
    }


def make_sample_data_issues(consistent_data):
    """Return collected data dict with stale/missing steps."""
    data = dict(consistent_data)
    data["chain_result"] = SAMPLE_CHAIN_ISSUES
    data["lineage_results"] = SAMPLE_LINEAGE_RESULTS
    data["step_details"] = list(data["step_details"])
    # Mark hazard as stale
    data["step_details"][2] = dict(data["step_details"][2])
    data["step_details"][2]["status"] = "stale"
    return data
