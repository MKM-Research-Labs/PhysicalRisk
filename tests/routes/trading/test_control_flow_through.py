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
Single-source-of-truth tests for storm control parameters.

Asserts the invariant that ``event_window_hours`` exposed by
``GET /trading/control/params`` matches what dependent server endpoints
actually use (stress runs, animations). Regressions here mean a consumer
has drifted from the centralised config and is reading a stale/hardcoded
value — the exact bug that caused the 168→120 cascade.

This file intentionally does NOT exercise the admin-gated POST endpoints;
the goal is to verify read-path consistency across the platform.
"""

import json

import pytest


@pytest.fixture
def control_env(trading_env):
    """Trading env with storm_control.json at the canonical 168 default."""
    p = trading_env['input_dir'] / 'storm_control.json'
    p.write_text(json.dumps({
        "version": "1.0.0",
        "sections": {
            "storm_generation": {"event_window_hours": 168},
            "hydrograph_synthesis": {},
            "gauge_propagation": {},
            "spatial_correlation": {},
            "stress_catalogue": {},
        },
    }))
    return trading_env


@pytest.fixture
def flow_client(control_env):
    # Apply our fixture JSON so config.port is in sync before assertions.
    # (Other tests in the session may have patched it.)
    from config.storm_control import apply_storm_control
    apply_storm_control()
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


def _get_control_hours(client) -> int:
    r = client.get('/api/v1/trading/control/params')
    assert r.status_code == 200
    sections = r.get_json()['params']['sections']
    hrs = sections['storm_generation']['event_window_hours']
    assert isinstance(hrs, int) and hrs > 0
    return hrs


class TestControlHoursMatchesPythonConstant:
    """Control endpoint must report the same value as ``config.port.EVENT_WINDOW_HOURS``."""

    def test_control_matches_config_port_constant(self, flow_client):
        import config.port as cp
        hrs = _get_control_hours(flow_client)
        assert hrs == cp.EVENT_WINDOW_HOURS, (
            f"Control API reports {hrs} but config.port.EVENT_WINDOW_HOURS="
            f"{cp.EVENT_WINDOW_HOURS}. Single source of truth broken."
        )

    def test_control_matches_stress_helpers_constant(self, flow_client):
        from routes.trading.stress._helpers import STORM_HOURS
        hrs = _get_control_hours(flow_client)
        assert hrs == STORM_HOURS, (
            f"Control API reports {hrs} but routes.trading.stress._helpers."
            f"STORM_HOURS={STORM_HOURS}. Consumer drift detected."
        )

    def test_control_matches_animation_constant(self, flow_client):
        from routes.propertyts.animation import STORM_HOURS
        hrs = _get_control_hours(flow_client)
        assert hrs == STORM_HOURS, (
            f"Control API reports {hrs} but routes.propertyts.animation."
            f"STORM_HOURS={STORM_HOURS}. Animation drift detected."
        )


class TestAllStormHoursImportsAlign:
    """Every module that reads EVENT_WINDOW_HOURS must see the same integer."""

    def test_all_known_readers_agree(self, flow_client):
        import config.port as cp
        from routes.propertyts.animation import STORM_HOURS as ANIM_HOURS
        from routes.trading.stress._helpers import STORM_HOURS as STRESS_HOURS

        control_hrs = _get_control_hours(flow_client)

        # All four should be identical — the whole point of a centralised config.
        assert control_hrs == cp.EVENT_WINDOW_HOURS == STRESS_HOURS == ANIM_HOURS, (
            f"Storm-hours sources disagree: "
            f"control={control_hrs}, "
            f"config.port={cp.EVENT_WINDOW_HOURS}, "
            f"stress._helpers={STRESS_HOURS}, "
            f"animation={ANIM_HOURS}"
        )


class TestFloodPolyJsHasNoHardcodedStormHours:
    """The port_stress JS helper must not hardcode storm hours — it must read from window global.

    This test guards against regressing the client-side bug that made FloodPoly
    use a different value than the backend whenever the user changed Control.
    """

    def test_fpStormHours_is_not_hardcoded(self):
        from pathlib import Path
        from tests.visual.conftest import _augment_with_static
        repo = str(Path('.').resolve())
        setup = Path('src/visual/interactivity/trading/port_stress/setup.py')
        # The factory JS body now lives in src/static/js/trading/port_stress/
        # setup.js (returned via js_static()); fold it back in so the source
        # assertions see the migrated JS.
        src = _augment_with_static(setup.read_text(), repo)
        # The literal form "var _fpStormHours = 168;" is the known bug.
        # We want a getter that reads from window.__STORM_CONTROL_HOURS.
        assert 'var _fpStormHours = 168' not in src, (
            "setup.py hardcodes _fpStormHours — it must read from "
            "window.__STORM_CONTROL_HOURS so Control tab changes propagate."
        )
        assert 'window.__STORM_CONTROL_HOURS' in src, (
            "setup.py must reference window.__STORM_CONTROL_HOURS as the "
            "single source of truth for storm hours."
        )
