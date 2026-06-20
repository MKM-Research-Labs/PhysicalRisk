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

"""Shared fixtures for pipeline integration tests."""

import hashlib
import json
import os

import pytest

from config import config

# Known password used by `port_admin_pw` fixture. The fixture installs a
# tmp ``.port_admin`` file with this password's hash and points
# ``app.commands.port._ADMIN_FILE`` at it; tests then authenticate via
# the ``MKM_PORT_ADMIN_PASSWORD`` env var rather than mocking out the
# ``_authenticate`` function. Mocking the gate hides any breakage in
# the auth path itself; this fixture exercises the real verification.
_TEST_PORT_PW = "test-port-admin-pw"


@pytest.fixture
def port_admin_pw(monkeypatch, tmp_path):
    """Authenticate cmd_port without bypassing the password gate.

    Sets up a tmp admin file with a known password's hash, points the
    ``_ADMIN_FILE`` constant at it, and exposes the password via the
    ``MKM_PORT_ADMIN_PASSWORD`` env var. Also redirects
    ``config.input_dir`` to ``tmp_path`` as defence-in-depth so any
    generator that slips through unmocked writes to tmp rather than
    ``data/input/<catchment>/`` (regression: 2026-05-04 incident where
    a test mocked ``_authenticate`` but missed prerequisite generators,
    overwriting real ``gauge.json``).
    """
    from app.commands import port as port_cmd
    from app.commands.port import auth as port_auth

    admin_file = tmp_path / ".port_admin"
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + _TEST_PORT_PW).encode()).hexdigest()
    admin_file.write_text(json.dumps({"salt": salt, "hash": h}))

    # Patch both the re-exported alias in app.commands.port and the
    # actual module-level binding in app.commands.port.auth — the verify
    # function looks up the name locally in auth.py, so patching only
    # the re-export silently misses.
    monkeypatch.setattr(port_cmd, "_ADMIN_FILE", admin_file)
    monkeypatch.setattr(port_auth, "_ADMIN_FILE", admin_file)
    monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", _TEST_PORT_PW)

    original_input_dir = getattr(config, "input_dir", None)
    config.input_dir = tmp_path
    try:
        yield _TEST_PORT_PW
    finally:
        if original_input_dir is not None:
            config.input_dir = original_input_dir


def _available_gauge_points() -> int:
    """Number of gauge points defined for the active catchment.

    Generators cap the requested gauge count to the catchment's available
    ``GAUGE_POINTS`` (thames has 52, halong only 3), so the pipeline
    assertions must use the capped count, not a hardcoded 5.
    """
    try:
        from port.src.gauge import GaugePortfolioGenerator
        # Reads params only (no generate/write), so no scratch backend is needed;
        # the WP2.4 ctor takes a catchment, not a directory.
        gen = GaugePortfolioGenerator(verbose=False)
        n = len(gen.params.GAUGE_POINTS)
        if n:
            return n
    except Exception:
        pass
    return 5


# Catchment-agnostic: never request more gauges than the catchment defines.
N_GAUGES = min(5, _available_gauge_points())
N_PROPERTIES = 5
N_STORMS = 50
SIMULATION_HOURS = 12
HISTORY_YEARS = 5


def _run_pipeline(output_dir):
    """Execute all pipeline steps with small counts."""
    from port.src.gauge import GaugePortfolioGenerator
    from port.src.property import PropertyPortfolioGenerator
    from port.src.mortgage import MortgagePortfolioGenerator
    from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
    from port.src.storm_multi.generators.batch_generator import generate_event_set
    from port.src.storm_multi.utils.serialization import save_sequences, save_summary
    from port.src.gauge.gaugehd import generate_all_gauge_histories
    from port.src.hazard import build_hazard_curves
    from port.src.property.propertyts import PropertyTimeSeriesGenerator
    from port.src.property.propertyhc import PropertyHazardCurveGenerator
    from port.src.counterparty import CounterpartyPortfolioGenerator
    from db_helpers import tmp_catchment

    # The migrated gauge + property + loan writers persist through ``database``; root a
    # scratch backend at ``output_dir`` (catchment "thames") so their saves land
    # ``gauge.json`` / ``property.json`` / ``loan.json`` in the same dir the other, still
    # directory-injected generators read/write (and so the property generator's gauge read
    # and the loan generator's property read resolve there too).
    with tmp_catchment(output_dir):
        GaugePortfolioGenerator(verbose=False).generate(count=N_GAUGES)
        PropertyPortfolioGenerator(verbose=False).generate(count=N_PROPERTIES)
        MortgagePortfolioGenerator(verbose=False).generate()
        GaugeTimeSeriesGenerator(output_dir, verbose=False).generate(simulation_hours=SIMULATION_HOURS)
        # Generate storm sequences (replaces old generate_storms)
        sequences = generate_event_set(count=N_STORMS, catchment_id='thames', seed=42)
        save_sequences(sequences, output_dir / 'storm_sequences.json')
        save_summary(sequences, output_dir / 'sequences_summary.json')
        generate_all_gauge_histories(years=HISTORY_YEARS)
        build_hazard_curves(
            output_dir=output_dir, catchment_id='thames',
            distribution='gev', verbose=False,
        )
        PropertyTimeSeriesGenerator(output_dir, verbose=False).generate()
        PropertyHazardCurveGenerator(output_dir, verbose=False).generate()
        CounterpartyPortfolioGenerator(verbose=False).generate()


@pytest.fixture(scope="module")
def pipeline_dir(tmp_path_factory):
    """Run a mini pipeline once per module; yield the directory.

    Module scope prevents config.input_dir mutations in generators.py
    from racing with the fixture setup for integration.py.
    """
    d = tmp_path_factory.mktemp("pipeline")
    original_input_dir = config.input_dir
    config.input_dir = d
    try:
        _run_pipeline(d)
        yield d
    finally:
        config.input_dir = original_input_dir
