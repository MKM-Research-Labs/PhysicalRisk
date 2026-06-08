# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Model C response-effectiveness profile type."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SeismicResponseProfile:
    """Deterministic modifiers derived from an asset's BRI geoseismic measures.

    Model C introduces no randomness; this profile is computed once per asset
    and consumed by Model D.

    Attributes:
        asset_id: stable identifier for the asset.
        theta_mult: per-damage-state fragility median multiplier, keyed
            "DS1"/"DS2"/"DS3". A multiplier > 1.0 raises the median PGA at that
            threshold (more resilient -> rarer damage).
        rating: derived BRI geoseismic rating ("AA"/"A"/"B"/"NR").
        r_acc: recovery acceleration factor (effective T_rec = T_rec / r_acc).
        p_pef_by_ds: post-GS15 post-earthquake-fire probability per damage state.
        gs02_present: whether GS02 is installed (the soft-soil F_a gate; the
            amplification itself is applied in Model B from the same flag).
    """
    asset_id: str
    theta_mult: Dict[str, float]
    rating: str
    r_acc: float
    p_pef_by_ds: Dict[str, float]
    gs02_present: bool
