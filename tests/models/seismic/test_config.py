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

"""Tests for the seismic model config schema and loader (config/seismic.py).

Covers: both seed-matrices files load into a complete SeismicModelConfig;
documentation keys are stripped; the Appendix A/C/D/E seed values are wired
through to the typed config; and the zone/site-class/fragility vocabularies are
internally consistent (every fragility class carries three ordered medians,
every zone names a regime the GMPE block defines, etc.).
"""

import pytest

from config.seismic import (
    DamageState,
    SeismicModelConfig,
    SeismicRunConfig,
    load_seismic_config,
)


@pytest.fixture
def config():
    return load_seismic_config()


# ===========================================================================
# Loading and doc-stripping
# ===========================================================================


def test_load_returns_complete_config(config):
    assert isinstance(config, SeismicModelConfig)
    assert isinstance(config.run, SeismicRunConfig)
    assert config.occurrence.zones
    assert config.ground_motion.gmpe_by_regime
    assert config.response.measure_modifiers
    assert config.fragility.medians_by_construction


def test_doc_keys_are_stripped(config):
    assert "_doc" not in config.occurrence.zones
    assert "_meta" not in config.fragility.medians_by_construction
    for block in config.response.measure_modifiers.values():
        assert "_doc" not in block


def test_run_override_is_respected():
    cfg = load_seismic_config(run=SeismicRunConfig(n_sim=500))
    assert cfg.run.n_sim == 500


def test_default_run_uses_ten_thousand_draws(config):
    # The DS3 leg is charged as n_DS3/n_sim x 1.0 x 10,000; the default draw
    # count matches the resilience-credit currency of the storm engine.
    assert config.run.n_sim == 10000
    assert config.run.loss_given_event_collapse == 1.0


# ===========================================================================
# Appendix A — zones
# ===========================================================================


def test_zone_rates_increase_with_hazard(config):
    zones = config.occurrence.zones
    order = ["Very low", "Low", "Moderate", "High", "Very high"]
    rates = [zones[z]["lambda_zone"] for z in order]
    assert rates == sorted(rates)
    assert rates[0] == pytest.approx(0.0005)
    assert rates[-1] == pytest.approx(0.080)


def test_every_zone_names_a_defined_regime(config):
    regimes = config.ground_motion.gmpe_by_regime
    for zone, block in config.occurrence.zones.items():
        assert block["tectonic_regime"] in regimes, zone


def test_hazard_class_maps_to_known_zone(config):
    occ = config.occurrence
    for cls, zone in occ.hazard_class_to_zone.items():
        assert zone in occ.zones, cls
    assert occ.hazard_class_to_zone["Medium"] == "Moderate"


# ===========================================================================
# Appendix C — ground motion / site class
# ===========================================================================


def test_vs30_proxies_and_bands_are_ordered(config):
    gm = config.ground_motion
    classes = ["A", "B", "C", "D", "E"]
    proxies = [gm.vs30_proxy_by_class[c] for c in classes]
    assert proxies == sorted(proxies, reverse=True)
    assert gm.vs30_proxy_by_class["A"] == 800


def test_soft_soil_amplification_gate(config):
    amp = config.ground_motion.soil_amplification
    assert amp["fa"] == pytest.approx(1.30)
    assert set(amp["applies_classes"]) == {"D", "E"}


def test_soil_recurrence_modifier_is_monotone(config):
    m = config.occurrence.soil_recurrence_m_soil
    assert m["A"] == 1.00 and m["B"] == 1.00
    assert m["C"] < m["D"] < m["E"]


# ===========================================================================
# Appendix E — fragility / loss
# ===========================================================================


def test_fragility_medians_are_ordered_per_class(config):
    # DS1 < DS2 < DS3 median PGA for every construction class.
    for cls, row in config.fragility.medians_by_construction.items():
        assert row["DS1"] < row["DS2"] < row["DS3"], cls
        assert row["beta"] > 0.0


def test_urm_is_more_fragile_than_modern_rc(config):
    med = config.fragility.medians_by_construction
    for ds in ("DS1", "DS2", "DS3"):
        assert med["Masonry_URM"][ds] < med["RC_Modern"][ds]


def test_loss_given_damage_state_ds3_is_fixed_total(config):
    lgds = config.fragility.loss_given_damage_state
    assert lgds["DS3"]["fixed"] == 1.00
    assert lgds["DS2"]["mean"] < 1.00
    assert lgds["DS0"]["mean"] < lgds["DS1"]["mean"] < lgds["DS2"]["mean"]


def test_recovery_functionality_and_times_by_ds(config):
    rec = config.fragility.recovery
    q = rec["q_t0_by_ds"]
    t = rec["t_rec_months_by_ds"]
    assert q["DS0"] == 1.00 and q["DS3"] == 0.00
    assert q["DS0"] > q["DS1"] > q["DS2"] > q["DS3"]
    assert t["DS0"] < t["DS1"] < t["DS2"] < t["DS3"]


# ===========================================================================
# Appendix D — response effectiveness modifiers
# ===========================================================================


def test_base_isolation_is_the_largest_single_modifier(config):
    mods = config.response.measure_modifiers
    deltas = {code: blk["delta"] for code, blk in mods.items()}
    assert deltas["GS12"] == max(deltas.values())
    assert deltas["GS12"] == pytest.approx(0.40)
    assert deltas["GS08"] > deltas["GS09"]


def test_governance_cap_present(config):
    gov = config.response.governance
    assert set(gov["codes"]) == {"GS16", "GS17", "GS18"}
    assert gov["combined_cap"] == pytest.approx(0.05)
    assert gov["delta_each"] == pytest.approx(0.03)


def test_pef_probabilities_and_gs15_reduction(config):
    pef = config.response.post_earthquake_fire
    p = pef["p_pef_by_ds"]
    assert p["DS0"] == 0.0 and p["DS1"] == 0.0
    assert p["DS2"] == pytest.approx(0.08)
    assert p["DS3"] == pytest.approx(0.18)
    assert pef["gs15_reduction"] == pytest.approx(0.80)


def test_recovery_acceleration_ratings_are_ordered(config):
    r = config.response.recovery_acceleration["r_acc_by_rating"]
    assert r["AA"] > r["A"] > r["B"] > r["NR"]
    assert r["AA"] == 1.00


def test_damage_state_enum_indices():
    assert DamageState.DS0.value == 0
    assert DamageState.DS3.value == 3
