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
Model C — Seismic Response Effectiveness (MKM-SEIS-001).

A deterministic mapping from an asset's BRI geoseismic measure flags
(GS01-GS18) to the modifiers Model D consumes. No randomness is introduced.

It produces:

- **theta_mult** — the per-damage-state fragility median multiplier. For each
  present measure the median PGA at the targeted damage states is shifted up by
  ``(1 + delta_j)``; the governance measures GS16-GS18 contribute a single
  combined, capped factor (Appendix D1). A higher multiplier means the asset
  needs a larger PGA to reach that damage state — the resilience credit.

- **r_acc** — the recovery acceleration factor, derived from the asset's BRI
  geoseismic rating (Appendix D2), with an extra GS18 (EGGAR) uplift.

- **p_pef_by_ds** — the post-earthquake-fire cascade probability per damage
  state, reduced by 80% when GS15 (flexible gas piping with automatic seismic
  shut-off) is installed.

The soft-soil F_a gate (GS02) is reported on the profile for completeness; the
amplification itself is applied in Model B from the same flag.
"""

from typing import Dict, List

from config.seismic import ResponseConfig, SeismicModelConfig
from models.seismic.datastructures import AssetSeismicFeatures, SeismicResponseProfile

__all__ = [
    "DAMAGE_STATE_KEYS",
    "fragility_multipliers",
    "geoseismic_rating",
    "recovery_acceleration",
    "pef_probabilities",
    "derive_response_profile",
]

# The fragility damage-state thresholds a median multiplier can shift. DS0 is
# the no-collapse floor and carries no median.
DAMAGE_STATE_KEYS = ("DS1", "DS2", "DS3")


def _targets(applies, keys=DAMAGE_STATE_KEYS) -> List[str]:
    """Resolve an ``applies`` spec ("all" or an explicit list) to DS keys."""
    return list(keys) if applies == "all" else [ds for ds in applies if ds in keys]


def fragility_multipliers(
    features: AssetSeismicFeatures, cfg: ResponseConfig,
) -> Dict[str, float]:
    """Per-damage-state fragility median multiplier theta_mult (Appendix D1).

    ``theta_mult[DS] = product over present measures applying to DS of
    (1 + delta_j)``, with the GS16-GS18 governance block folded in as a single
    combined factor capped at ``combined_cap``.
    """
    mult = {ds: 1.0 for ds in DAMAGE_STATE_KEYS}

    for code, block in cfg.measure_modifiers.items():
        if not features.has(code):
            continue
        for ds in _targets(block["applies"]):
            mult[ds] *= 1.0 + block["delta"]

    gov = cfg.governance
    n_present = sum(1 for code in gov["codes"] if features.has(code))
    if n_present:
        combined = min(gov["delta_each"] * n_present, gov["combined_cap"])
        for ds in _targets(gov.get("applies", "all")):
            mult[ds] *= 1.0 + combined

    return mult


def geoseismic_rating(
    features: AssetSeismicFeatures, cfg: ResponseConfig,
) -> str:
    """The BRI geoseismic rating ("AA"/"A"/"B"/"NR") from the present measures.

    A tier is achieved when a majority of its own measure set is present and
    every lower tier is also achieved (Section 7.4, Table 5).
    """
    sets = cfg.grade_code_sets

    def majority(group: List[str]) -> bool:
        return bool(group) and (
            sum(1 for code in group if features.has(code)) >= (len(group) + 1) // 2)

    b_ok = majority(sets.get("B", []))
    a_ok = b_ok and majority(sets.get("A_extra", []))
    aa_ok = a_ok and majority(sets.get("AA_extra", []))

    if aa_ok:
        return "AA"
    if a_ok:
        return "A"
    if b_ok:
        return "B"
    return "NR"


def recovery_acceleration(
    features: AssetSeismicFeatures, cfg: ResponseConfig,
) -> float:
    """Recovery acceleration factor r_acc (Appendix D2), with the GS18 uplift."""
    racc = cfg.recovery_acceleration
    rating = geoseismic_rating(features, cfg)
    value = racc["r_acc_by_rating"][rating]
    if features.has(racc.get("gs18_code", "GS18")):
        value *= racc["gs18_multiplier"]
    return value


def pef_probabilities(
    features: AssetSeismicFeatures, cfg: ResponseConfig,
) -> Dict[str, float]:
    """Post-earthquake-fire probability per damage state (Appendix E4 / 3.6)."""
    pef = cfg.post_earthquake_fire
    reduction = (1.0 - pef["gs15_reduction"]
                 if features.has(pef.get("gs15_code", "GS15")) else 1.0)
    return {ds: p * reduction for ds, p in pef["p_pef_by_ds"].items()}


def derive_response_profile(
    features: AssetSeismicFeatures, config: SeismicModelConfig,
) -> SeismicResponseProfile:
    """Assemble the full deterministic :class:`SeismicResponseProfile`."""
    cfg = config.response
    return SeismicResponseProfile(
        asset_id=features.asset_id,
        theta_mult=fragility_multipliers(features, cfg),
        rating=geoseismic_rating(features, cfg),
        r_acc=recovery_acceleration(features, cfg),
        p_pef_by_ds=pef_probabilities(features, cfg),
        gs02_present=features.has(cfg.gs02_soil_gate.get("code", "GS02")),
    )
