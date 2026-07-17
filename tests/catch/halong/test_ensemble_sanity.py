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

"""Phase 1.8 sanity sketches for the Halong typhoon ensemble.

These are not calibration tests — Phase 3 will validate against named
historical typhoons. They confirm the order of magnitude of two things
that would otherwise be invisible until someone plotted the output:

  1. Trajectory passage rate through a northern-Vietnam region box
     (some storms reach the catchment; not all do, not none do).
  2. Peak-wind p99 at the inland Hanoi reference property is in the
     ballpark of a SCS-typhoon impact range.

Both run a small ensemble (~6 seconds combined on dev hardware). They
catch "halong/tc.py is wildly miscalibrated" regressions without
asserting any specific historical event.
"""

import numpy as np
import pytest


def _build_typhoon_config():
    """Lazy import — config (which adds data/ to sys.path) must be loaded
    before `catch.halong.tc` is reachable. Calling this from inside test
    functions and fixtures defers the import past pytest's collection phase.
    """
    # Touching config triggers ConfigPaths._setup_paths which adds data/
    # to sys.path.
    import config  # noqa: F401
    from catch.halong.tc import build_typhoon_config
    return build_typhoon_config


# Northern-Vietnam region box used for the passage-rate check. Spans the
# Red River delta from Hanoi to the coast — wide enough that recurving
# storms have a chance to enter, tight enough that westward storms
# south of lat 18 don't count.
NORTHERN_VIETNAM_BBOX = (102.0, 18.0, 108.0, 23.0)


@pytest.fixture(scope="module")
def halong_sanity_ensemble():
    """Small ensemble for the peak-wind sanity check (cached per module)."""
    from models.typhoon.pipeline import simulate_typhoon_events
    cfg = _build_typhoon_config()()
    rng = np.random.default_rng(0)
    return simulate_typhoon_events(
        config=cfg,
        n_events=20,
        n_particles=30,
        rng=rng,
        horizon_hours=168.0,
    )


class TestTrackPassageRate:
    """Storms should reach northern Vietnam at a plausible rate — not 0%,
    not 100%. Phase 3 will refine against best-track data."""

    def test_passage_rate_in_loose_bounds(self):
        from models.typhoon.particle_filter import ParticleFilter
        cfg = _build_typhoon_config()()
        rng = np.random.default_rng(7)
        pf = ParticleFilter(n_particles=500, config=cfg, rng=rng)
        trajectories = pf.run_to_horizon(horizon_hours=168.0)

        lon_min, lat_min, lon_max, lat_max = NORTHERN_VIETNAM_BBOX
        n_pass = 0
        for traj in trajectories:
            for s in traj.states:
                if lon_min <= s.longitude <= lon_max and lat_min <= s.latitude <= lat_max:
                    n_pass += 1
                    break

        passage_rate = n_pass / len(trajectories)
        # Loose bounds. Calibrated empirically at ~0.50 with the current
        # halong/tc.py. Phase 3 will tighten against historical landfall
        # frequency for the Red River delta.
        assert 0.10 < passage_rate < 0.95, (
            f"Northern Vietnam passage rate {passage_rate:.3f} outside sanity bounds "
            f"(0.10, 0.95). Either the genesis prior or the motion regimes have drifted."
        )


class TestPeakWindReasonableness:
    """p99 peak winds at Hanoi properties should sit in a plausible
    typhoon-impact range — order of magnitude only.
    """

    def test_hanoi_centre_p99_in_plausible_range(self, halong_sanity_ensemble):
        centre = next(
            p for p in halong_sanity_ensemble.properties if p.property_id == "HAN-CENTRE"
        )
        # Inland sustained typhoon winds typically 10-50 m/s for the
        # storm classes simulated. Wide order-of-magnitude bounds.
        assert 5.0 < centre.peak_sustained_p99 < 100.0, (
            f"HAN-CENTRE p99 peak wind {centre.peak_sustained_p99:.1f} m/s "
            f"outside plausible range (5, 100)"
        )

    def test_property_spread_is_meaningful(self, halong_sanity_ensemble):
        # Different properties (coastal vs inland) should see different
        # peak winds. Identical statistics across all properties would
        # mean the wind-field model isn't differentiating positions.
        peaks = [p.peak_sustained_p99 for p in halong_sanity_ensemble.properties]
        assert max(peaks) - min(peaks) > 1.0, (
            f"All properties produced near-identical p99 winds — wind-field "
            f"not differentiating positions: {peaks}"
        )

    def test_coastal_property_higher_than_inland(self, halong_sanity_ensemble):
        # The HAN-COASTAL property is closer to the Gulf of Tonkin and
        # should see stronger winds than HAN-WEST (furthest inland).
        coastal = next(
            p for p in halong_sanity_ensemble.properties if p.property_id == "HAN-COASTAL"
        )
        west = next(
            p for p in halong_sanity_ensemble.properties if p.property_id == "HAN-WEST"
        )
        assert coastal.peak_sustained_p99 > west.peak_sustained_p99, (
            f"Coastal p99 ({coastal.peak_sustained_p99:.1f}) not greater than "
            f"inland p99 ({west.peak_sustained_p99:.1f})"
        )

    def test_gale_force_exceeded_somewhere(self, halong_sanity_ensemble):
        # At least one property should have non-zero probability of
        # exceeding gale-force (17.5 m/s) winds. If none do, the
        # ensemble is too weak to be useful.
        max_exceedance = max(
            p.threshold_exceedance.get(17.5, 0.0)
            for p in halong_sanity_ensemble.properties
        )
        assert max_exceedance > 0.01, (
            f"Maximum gale-force exceedance probability {max_exceedance:.3f} "
            f"essentially zero — typhoon intensity is unrealistically low"
        )


class TestTailCalibrationAnchors:
    """Sanity-rank the historical super-typhoon anchors (Durian 2006 at
    ~69 m/s, Angela 1995 at ~80 m/s) against the analytical EXTREME
    peak-wind distribution.

    These are loose rank tests — not Phase 3 calibration. They ensure
    that historical Cat-5 super-typhoons land in the model's UPPER TAIL
    (rare but plausible), not in the body (would mean the model treats
    them as routine) and not above the model's cap (would mean the model
    can't realize them).
    """

    def test_angela_rarer_than_durian(self):
        # Angela's 80 m/s should be strictly rarer than Durian's 69 m/s
        # under any monotonic peak-wind distribution.
        import config  # noqa: F401
        from catch.halong.tc import HALONG_TAIL_ANCHORS, HALONG_TYPHOON_PEAK_WIND
        from config.typhoon import ScenarioFamily
        from models.typhoon.genesis import peak_wind_exceedance

        extreme = HALONG_TYPHOON_PEAK_WIND[ScenarioFamily.EXTREME]
        durian = next(a for a in HALONG_TAIL_ANCHORS if a["name"] == "Durian")
        angela = next(a for a in HALONG_TAIL_ANCHORS if a["name"] == "Angela")
        p_durian = peak_wind_exceedance(durian["peak_wind_ms"], extreme)
        p_angela = peak_wind_exceedance(angela["peak_wind_ms"], extreme)
        assert p_angela < p_durian, (
            f"Angela ({angela['peak_wind_ms']:.1f} m/s) is stronger than "
            f"Durian ({durian['peak_wind_ms']:.1f} m/s) — its exceedance "
            f"probability must be lower."
        )
