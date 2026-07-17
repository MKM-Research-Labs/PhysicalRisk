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

"""Tests for Model B — ground motion intensity / GMPE (groundmotion.py).

Covers: the seed GMPE reproducing the Section 7.2 Table 1 indicative PGA
attenuation; monotone decrease with R_JB and increase with magnitude; the
soft-soil amplification gate (GS02 / site class D-E); the aleatory residual
spreading two assets at the same (M, R_JB); and per-event sampling aligned
with the originating occurrence events, reproducible from a single seed.
"""

import numpy as np
import pytest

from config.seismic import load_seismic_config
from models.seismic.datastructures import (
    AssetSeismicFeatures,
    EarthquakeEvent,
    OccurrenceResult,
)
from models.seismic.groundmotion import (
    effective_vs30,
    gmpe_for_regime,
    gmpe_median_pga,
    sample_pga,
    simulate_asset_ground_motion,
    soil_amplification_factor,
)


@pytest.fixture
def config():
    return load_seismic_config()


@pytest.fixture
def crust_gmpe(config):
    return gmpe_for_regime("active_shallow_crust", config.ground_motion)


def _asset(**overrides):
    base = dict(
        asset_id="SEIS-1",
        commercial_type="Office",
        construction_type="RC_PreCode",
        soil_vs30_mps=450.0,            # stiff soil, class B
        seismic_hazard_class="Medium",
        measures=frozenset(),
    )
    base.update(overrides)
    return AssetSeismicFeatures(**base)


def _rng(seed=20260608):
    return np.random.default_rng(seed)


# ===========================================================================
# GMPE median — Table 1 reproduction
# ===========================================================================


def test_seed_gmpe_reproduces_table1_anchors(crust_gmpe):
    # M 6.5, stiff soil (V_S30 = 450). Indicative Section 7.2 Table 1 column.
    anchors = {2: 0.42, 5: 0.28, 10: 0.18, 20: 0.11, 50: 0.05, 100: 0.02}
    for r_jb, expected in anchors.items():
        pga = gmpe_median_pga(6.5, r_jb, 450.0, crust_gmpe)
        assert pga == pytest.approx(expected, abs=0.04), (r_jb, pga)


def test_median_decreases_monotonically_with_distance(crust_gmpe):
    pgas = [gmpe_median_pga(6.5, r, 450.0, crust_gmpe)
            for r in (2, 5, 10, 20, 50, 100)]
    assert pgas == sorted(pgas, reverse=True)


def test_median_increases_with_magnitude(crust_gmpe):
    low = gmpe_median_pga(5.5, 10.0, 450.0, crust_gmpe)
    high = gmpe_median_pga(7.0, 10.0, 450.0, crust_gmpe)
    assert high > low


def test_softer_soil_amplifies_median(crust_gmpe):
    stiff = gmpe_median_pga(6.5, 10.0, 760.0, crust_gmpe)
    soft = gmpe_median_pga(6.5, 10.0, 180.0, crust_gmpe)
    assert soft > stiff


# ===========================================================================
# Soil amplification gate
# ===========================================================================


def test_soft_soil_gate_applies_without_gs02(config):
    gm = config.ground_motion
    # Class D, GS02 absent -> F_a = 1.30.
    assert soil_amplification_factor(_asset(), "D", gm) == pytest.approx(1.30)
    # GS02 present removes it.
    assert soil_amplification_factor(
        _asset(measures=frozenset({"GS02"})), "D", gm) == 1.0
    # Stiff classes are never gated.
    assert soil_amplification_factor(_asset(), "B", gm) == 1.0


def test_effective_vs30_prefers_measured_then_proxy(config):
    gm = config.ground_motion
    assert effective_vs30(_asset(soil_vs30_mps=512.0), "B", gm) == 512.0
    # No measured value -> class proxy.
    assert effective_vs30(_asset(soil_vs30_mps=None), "C", gm) == gm.vs30_proxy_by_class["C"]


# ===========================================================================
# Sampling
# ===========================================================================


def test_sample_pga_lognormal_about_median(crust_gmpe, config):
    sigma = crust_gmpe["sigma_total"]
    rng = _rng()
    draws = [sample_pga(6.5, 10.0, 450.0, 1.0, crust_gmpe, sigma, rng)[0]
             for _ in range(20000)]
    median_model = gmpe_median_pga(6.5, 10.0, 450.0, crust_gmpe)
    assert np.median(draws) == pytest.approx(median_model, rel=0.06)
    # Lognormal mean exceeds the median.
    assert np.mean(draws) > np.median(draws)


def test_amplification_scales_median(crust_gmpe):
    base = sample_pga(6.5, 10.0, 150.0, 1.0, crust_gmpe, 0.0, _rng())[1]
    amp = sample_pga(6.5, 10.0, 150.0, 1.30, crust_gmpe, 0.0, _rng())[1]
    assert amp == pytest.approx(base * 1.30)


# ===========================================================================
# Orchestrator
# ===========================================================================


def _occurrence(events, zone="Moderate", site_class="B"):
    return OccurrenceResult(
        asset_id="SEIS-1", zone=zone, site_class=site_class,
        fault_distance_km=10.0, lambda_annual=0.008, lambda_effective=0.008,
        n_sim=3, n_events=len(events), events=events,
    )


def test_simulate_aligns_samples_with_events(config):
    events = [
        EarthquakeEvent(0, 6.5, 21.0, 106.0, 12.0, 5.0),
        EarthquakeEvent(2, 7.0, 21.0, 106.1, 20.0, 30.0),
    ]
    result = simulate_asset_ground_motion(_occurrence(events), _asset(), config, _rng())
    assert [s.draw_index for s in result.samples] == [0, 2]
    assert result.vs30_mps == 450.0
    assert result.amplification_factor == 1.0
    # Nearer, equal-ish magnitude event sees higher median PGA than the distant one.
    assert result.samples[0].median_pga_g > result.samples[1].median_pga_g


def test_simulate_is_reproducible(config):
    events = [EarthquakeEvent(0, 6.5, 21.0, 106.0, 12.0, 8.0),
              EarthquakeEvent(1, 6.8, 21.0, 106.0, 14.0, 15.0)]
    r1 = simulate_asset_ground_motion(_occurrence(events), _asset(), config, _rng())
    r2 = simulate_asset_ground_motion(_occurrence(events), _asset(), config, _rng())
    assert [s.pga_g for s in r1.samples] == [s.pga_g for s in r2.samples]


def test_soft_soil_asset_gets_amplified_result(config):
    events = [EarthquakeEvent(0, 6.5, 21.0, 106.0, 12.0, 8.0)]
    soft = _asset(soil_vs30_mps=140.0)  # class D
    result = simulate_asset_ground_motion(
        _occurrence(events, site_class="D"), soft, config, _rng())
    assert result.amplification_factor == pytest.approx(1.30)
