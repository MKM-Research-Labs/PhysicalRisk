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

"""
Unit tests for port.src.gauge.gaugets — part 1.

Covers default parameter values, gaugets_random defaults, and
generate() output structure.
"""

import pytest

import database
from db_helpers import test_backend, tmp_catchment


@pytest.fixture(autouse=True)
def _iso_catchment_with_gauges(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") and seed a gauge portfolio.

    The migrated gauge-timeseries generator reads the gauge portfolio and writes
    per-gauge timeseries through ``database``. Rooting the backend at ``tmp_path`` means
    those still land physically at ``tmp_path/gaugets/GAUGE-*.json`` (so existing glob
    read-backs keep working), and the seeded portfolio satisfies the generator's read."""
    from port.src.gauge import GaugePortfolioGenerator
    with tmp_catchment(tmp_path):
        GaugePortfolioGenerator(verbose=False).generate(count=5)
        yield


# ===========================================================================
# Default parameter values
# ===========================================================================

class TestGaugeTimeSeriesDefaults:

    def test_default_simulation_hours_is_168(self):
        """DEFAULT_PARAMS and generate() default must both be 168 hours (7 days).
        Regression: was hardcoded to 60 / 72, showing only ~63 readings."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        assert GaugeTimeSeriesGenerator.DEFAULT_PARAMS["simulation_hours"] == 168

    def test_generate_default_argument_is_168(self):
        """generate(simulation_hours) default parameter must be 168."""
        import inspect
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        sig = inspect.signature(GaugeTimeSeriesGenerator.generate)
        default = sig.parameters["simulation_hours"].default
        assert default == 168, f"Expected 168, got {default}"

    def test_generate_gaugets_function_default_is_168(self):
        """Convenience function generate_gaugets() default must be 168."""
        import inspect
        from port.src.gauge.gaugets import generate_gaugets
        sig = inspect.signature(generate_gaugets)
        default = sig.parameters["simulation_hours"].default
        assert default == 168, f"Expected 168, got {default}"

    def test_peak_hour_max_within_simulation_window(self):
        """peak_hour_max must be strictly less than simulation_hours."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        p = GaugeTimeSeriesGenerator.DEFAULT_PARAMS
        assert p["peak_hour_max"] < p["simulation_hours"], (
            f"peak_hour_max ({p['peak_hour_max']}) must be < "
            f"simulation_hours ({p['simulation_hours']})"
        )

    def test_peak_hour_min_less_than_max(self):
        """peak_hour_min must be less than peak_hour_max."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        p = GaugeTimeSeriesGenerator.DEFAULT_PARAMS
        assert p["peak_hour_min"] < p["peak_hour_max"]


# ===========================================================================
# gaugets_random DEFAULT_PARAMS
# ===========================================================================

class TestGaugetsRandomDefaults:

    def test_random_default_simulation_hours_is_168(self):
        """gaugets_random.DEFAULT_PARAMS simulation_hours must be 168."""
        from port.rand.thames.gauge.gaugets_random import DEFAULT_PARAMS
        assert DEFAULT_PARAMS["simulation_hours"] == 168, (
            f"Expected 168, got {DEFAULT_PARAMS['simulation_hours']}"
        )

    def test_random_default_peak_hour_max_within_window(self):
        """Random module peak_hour_max must be < simulation_hours."""
        from port.rand.thames.gauge.gaugets_random import DEFAULT_PARAMS
        assert DEFAULT_PARAMS["peak_hour_max"] < DEFAULT_PARAMS["simulation_hours"]


# ===========================================================================
# Generated output has correct reading count
# ===========================================================================

class TestGaugeTimeSeriesGenerate:

    def test_explicit_168_hours_produces_168_readings(self, tmp_path):
        """generate(168) should produce ~168 readings per gauge."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(verbose=False)
        result = gen.generate(simulation_hours=168)

        # Read the per-gauge timeseries back through the seam so the assertion holds on
        # both file (gaugets/GAUGE-*.json) and pg (keyed records) backends.
        catchment = database.active_catchment()
        ids = [g for g in database.iter_gauge_timeseries_ids(catchment)
               if g.startswith("GAUGE-")]
        assert len(ids) > 0, "No gaugets timeseries generated"

        for gid in ids:
            data = database.get_gauge_timeseries(catchment, gid)
            sim = data.get("flood_simulation", {})
            assert sim.get("simulation_hours") == 168, (
                f"{gid}: simulation_hours is {sim.get('simulation_hours')}, expected 168"
            )
            readings = sim.get("readings", [])
            # Should have approximately 168 readings (one per hour)
            assert len(readings) >= 160, (
                f"{gid}: only {len(readings)} readings for 168h simulation"
            )

    def test_explicit_60_hours_stores_60_in_metadata(self, tmp_path):
        """Explicit override stores the passed value in simulation_hours metadata."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(verbose=False)
        gen.generate(simulation_hours=60)

        # Read back through the seam (file glob is empty on pg -> would assert nothing).
        catchment = database.active_catchment()
        ids = [g for g in database.iter_gauge_timeseries_ids(catchment)
               if g.startswith("GAUGE-")]
        assert ids, "No gaugets timeseries generated"
        for gid in ids:
            data = database.get_gauge_timeseries(catchment, gid)
            sim = data.get("flood_simulation", {})
            assert sim.get("simulation_hours") == 60

    def test_168_produces_more_readings_than_60(self, tmp_path):
        """168-hour simulation produces significantly more readings than 60-hour."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator

        def _first_gauge_reading_count():
            catchment = database.active_catchment()
            gid = next(iter(database.iter_gauge_timeseries_ids(catchment)))
            return len(database.get_gauge_timeseries(catchment, gid)
                       ["flood_simulation"]["readings"])

        GaugeTimeSeriesGenerator(verbose=False).generate(simulation_hours=60)
        count60 = _first_gauge_reading_count()

        # Re-run overwrites the same catchment's per-gauge timeseries.
        GaugeTimeSeriesGenerator(verbose=False).generate(simulation_hours=168)
        count168 = _first_gauge_reading_count()

        assert count168 > count60, (
            f"168h ({count168} readings) should exceed 60h ({count60} readings)"
        )

    def test_simulation_hours_stored_in_output(self, tmp_path):
        """simulation_hours is written into each gaugets JSON."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(verbose=False)
        gen.generate(simulation_hours=168)

        # Read back through the seam (file glob is empty on pg -> would assert nothing).
        catchment = database.active_catchment()
        ids = [g for g in database.iter_gauge_timeseries_ids(catchment)
               if g.startswith("GAUGE-")]
        assert ids, "No gaugets timeseries generated"
        for gid in ids:
            data = database.get_gauge_timeseries(catchment, gid)
            assert "simulation_hours" in data["flood_simulation"]

    def test_configure_known_param(self, tmp_path):
        """Lines 127-130: configure() updates a known sim_param key."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(verbose=False)
        gen.configure(simulation_hours=48)
        assert gen.sim_params['simulation_hours'] == 48

    def test_configure_unknown_param_ignored(self, tmp_path):
        """Lines 127-129: unknown key is silently ignored (if branch is False)."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        gen = GaugeTimeSeriesGenerator(verbose=False)
        gen.configure(nonexistent_param=999)
        assert 'nonexistent_param' not in gen.sim_params

    def test_missing_gauge_portfolio_raises(self, tmp_path):
        """Gauge portfolio absent -> FileNotFoundError re-raised."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        # Bind a fresh empty backend (no gauge portfolio seeded) over the autouse one.
        with tmp_catchment(tmp_path / "empty"):
            with pytest.raises(FileNotFoundError):
                GaugeTimeSeriesGenerator(verbose=False).generate(simulation_hours=10)

    @pytest.mark.skipif(
        test_backend() == "pg",
        reason="asserts stale gaugets/GAUGE-*.json FILES are deleted; on Postgres "
               "timeseries are rows, not files — no stale files to clean.")
    def test_stale_gauge_files_removed(self, tmp_path):
        """Line 175: stale GAUGE-*.json files in gaugets/ are deleted before writing."""
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        # Pre-create a stale file in the gaugets directory
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir(parents=True)
        stale = gaugets_dir / "GAUGE-stale1234.json"
        stale.write_text('{"stale": true}')
        assert stale.exists()

        gen = GaugeTimeSeriesGenerator(verbose=False)
        gen.generate(simulation_hours=10)

        # Stale file must have been removed (line 175 executed)
        assert not stale.exists()
