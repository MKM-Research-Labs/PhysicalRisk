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

"""Shared fixtures and helpers for stressm package tests."""

import json
import pytest

from port.src.stressm import generate_stressm


# ---------------------------------------------------------------------------
# Synthetic gauge data helpers
# ---------------------------------------------------------------------------

def _make_nested_gauge(gauge_id, lat, lon, alert, warning, severe):
    """Build a gauge record in the nested FloodGauge schema (matches gauge.json)."""
    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id, "CatchmentID": "thames"},
            "Location": {"GaugeLatitude": lat, "GaugeLongitude": lon, "GaugeElevation": 10.0},
            "FloodStages": {
                "FloodAlert": alert,
                "FloodWarning": warning,
                "SevereFloodWarning": severe,
            },
        }
    }


# Three synthetic Thames-corridor gauges
_G1 = _make_nested_gauge("GAUGE-test001", 51.46, -0.30, 3.5, 4.6, 5.5)
_G2 = _make_nested_gauge("GAUGE-test002", 51.47, -0.20, 4.0, 5.2, 6.1)
_G3 = _make_nested_gauge("GAUGE-test003", 51.48, -0.10, 3.8, 4.9, 5.8)

_SYNTHETIC_GAUGE_JSON = {
    "flood_gauges": [_G1, _G2, _G3],
    "generation_metadata": {"num_gauges": 3},
}


@pytest.fixture(scope="module")
def gauge_dir(tmp_path_factory):
    """Temp directory with a 3-gauge gauge.json, with a tmp-rooted database backend.

    ``generate_stressm`` runs the migrated gauge-timeseries generator (via
    ``populate_gaugets``), which reads the gauge portfolio and writes per-gauge
    timeseries through ``database``. Rooting a tmp backend at this directory means the
    gauge read resolves to ``gauge.json`` here and the keyed timeseries land at
    ``<dir>/gaugets/`` — exactly where ``populate_gaugets`` then reads them back to merge
    storm responses. The module-scoped ``full_run``/``single_run`` fixtures execute under
    this binding."""
    from db_helpers import tmp_catchment, test_backend
    if test_backend() == "pg":
        pytest.skip(
            "generate_stressm runs a filesystem-based pipeline: gaugets_writer / "
            "gauge_parser / pipeline.stages / summary / orchestrator and "
            "gauge._stress_storms_stages.scan_gauge_responses read and write "
            "input_dir/output_dir files directly (e.g. glob gaugets/GAUGE-*.json), "
            "while the migrated gaugets generator writes through the seam — so the "
            "pipeline only completes against a file backend. This package is deferred "
            "on pg until the stressm pipeline migrates to the database seam (a "
            "generator-migration WP); every test here reaches this fixture via the "
            "autouse _bind_stressm_backend, so the whole package skips under pg.")
    d = tmp_path_factory.mktemp("stressm_input")
    (d / "gauge.json").write_text(json.dumps(_SYNTHETIC_GAUGE_JSON))
    with tmp_catchment(d, catchment="thames"):
        yield d


@pytest.fixture(autouse=True)
def _bind_stressm_backend(gauge_dir):
    """Re-bind the tmp backend (rooted at gauge_dir) for each test *body*.

    gauge_dir's module-scoped binding covers the module-scoped full_run/single_run
    fixtures; but the function-scoped autouse ``_database_file_backend`` (root conftest)
    rebinds the guarded backend per test, so this re-establishes the tmp backend for
    tests that call ``generate_stressm`` in their own body. A test that binds its own
    ``tmp_catchment`` (e.g. ``pipeline_env``) still wins, as it is set up after this."""
    from db_helpers import tmp_catchment
    with tmp_catchment(gauge_dir, catchment="thames"):
        yield


@pytest.fixture(scope="module")
def full_run(gauge_dir, tmp_path_factory):
    """Full generate_stressm run with 40 sequences and 3 synthetic gauges."""
    out_dir = tmp_path_factory.mktemp("stressm_output")
    return generate_stressm(
        input_dir=gauge_dir,
        output_dir=out_dir,
        count=40,
        catchment_id="thames",
        seed=42,
    )


@pytest.fixture(scope="module")
def single_run(gauge_dir, tmp_path_factory):
    """Single-gauge generate_stressm run."""
    out_dir = tmp_path_factory.mktemp("stressm_single_output")
    return generate_stressm(
        input_dir=gauge_dir,
        output_dir=out_dir,
        count=40,
        catchment_id="thames",
        seed=42,
        gauge_id="GAUGE-test002",
    )
