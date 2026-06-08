# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Model D damage / loss / resilience-credit output types."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class DamageOutcome:
    """The terminal outcome of one instantiated earthquake (Model D).

    Attributes:
        draw_index: the Monte Carlo draw this outcome belongs to.
        pga_g: the site PGA (g) that drove the fragility draw.
        damage_state: assigned damage state index (0 = DS0 .. 3 = DS3).
        structural_loss: structural loss ratio L_s in [0, 1] (DS3 -> 1.0).
        cascade_fire: whether a post-earthquake fire ignited this scenario.
        combined_loss: max(L_seismic, L_fire) — the scenario loss after any
            post-earthquake-fire cascade.
        resilience_index: normalised area under the functionality curve Q(t)
            over the control horizon, in [0, 1] (1.0 = full function retained).
    """
    draw_index: int
    pga_g: float
    damage_state: int
    structural_loss: float
    cascade_fire: bool
    combined_loss: float
    resilience_index: float


@dataclass
class AssetSeismicResult:
    """End-to-end per-asset seismic result (occurrence + ground motion +
    response + damage), and the resilience-credit leg the PRS pricer consumes.

    Attributes:
        asset_id: stable identifier for the asset.
        zone: resolved seismic hazard zone.
        site_class: resolved Eurocode 8 site class.
        construction_type: fragility-class key used for the base medians.
        rating: BRI geoseismic rating ("AA"/"A"/"B"/"NR").
        lambda_annual: per-asset annual occurrence rate.
        n_sim: number of Monte Carlo draws.
        n_events: number of draws that instantiated an earthquake.
        damage_state_counts: terminal count per damage state {0,1,2,3}.
        n_cascade_fire: number of scenarios with a post-earthquake fire.
        loss_frequency: mean annual structural loss ratio (Sum L_s / n_sim).
        no_collapse_rate: conditional (n_DS0+n_DS1+n_DS2)/n_events.
        seismic_spread_bps: the full-collapse leg = n_DS3/n_sim x LGE x 10,000.
        mean_resilience_index: mean functionality area over instantiated events.
        pml_475: probable maximum loss ratio at the 475-year return period.
        pml_2475: probable maximum loss ratio at the 2,475-year return period.
        outcomes: the per-event DamageOutcome records.
    """
    asset_id: str
    zone: str
    site_class: str
    construction_type: str
    rating: str
    lambda_annual: float
    n_sim: int
    n_events: int
    damage_state_counts: Dict[int, int]
    n_cascade_fire: int
    loss_frequency: float
    no_collapse_rate: float
    seismic_spread_bps: float
    mean_resilience_index: float
    pml_475: float
    pml_2475: float
    outcomes: List[DamageOutcome] = field(default_factory=list)

    def to_dict(self) -> dict:
        """JSON-serialisable summary for the port stage (excludes per-event rows)."""
        return {
            "asset_id": self.asset_id,
            "zone": self.zone,
            "site_class": self.site_class,
            "construction_type": self.construction_type,
            "rating": self.rating,
            "lambda_annual": self.lambda_annual,
            "n_sim": self.n_sim,
            "n_events": self.n_events,
            "damage_state_counts": {str(k): v for k, v in self.damage_state_counts.items()},
            "n_cascade_fire": self.n_cascade_fire,
            "loss_frequency": round(self.loss_frequency, 6),
            "no_collapse_rate": round(self.no_collapse_rate, 6),
            "seismic_spread_bps": round(self.seismic_spread_bps, 4),
            "mean_resilience_index": round(self.mean_resilience_index, 6),
            "pml_475": round(self.pml_475, 6),
            "pml_2475": round(self.pml_2475, 6),
        }
