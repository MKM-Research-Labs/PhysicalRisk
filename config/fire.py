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
Configuration schema for the BRI fire-resilience credit model.

Defines the *shape* of the calibration knobs the fire model expects and the
loader that hydrates them from config/fire_matrices.json. The fire model is
designed to sit pari-passu with the 10,000-storm Monte Carlo engine so fire
loss aggregates into the same resilience-credit currency.

Architecture (governance-separated component models):
- Model A — Initiation / Exposure Frequency  (this stage; Poisson)
- Model B — Fire Growth & Intensity          (15-min stepwise; next stage)
- Model C — Detection, Suppression, Response  (next stage)
- Model D — Containment, Loss & Resilience Credit (next stage)

The 8-state discrete-time Bayesian state machine progresses in 15-minute
steps. The central concept is the *point of no return*: the first step where
latent intensity I_t exceeds I_crit before suppression bites, at which point
the S5_Contained column collapses to ~0 and the chain is absorbing into
{S6_PartialLoss, S7_TotalLoss}.

All numeric values live in config/fire_matrices.json and are
engineering-judgement SEEDS (placeholders), not calibrated values. This
module never embeds the numbers; it only describes their structure and loads
them. The resilience-level vocabulary is imported from the CDM
(port.cdm.asset.resilience) to stay single-source.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

# ===========================================================================
# Enums
# ===========================================================================


class FireState(Enum):
    """The 8 states of the discrete-time fire progression machine.

    S0..S4 are transient; S5 is the absorbing success state; S6 and S7 are
    terminal loss states. The integer value is the index into the state
    vector P_t and into the rows/cols of the 8x8 transition matrices.
    """
    S0_EXPOSURE_OR_IGNITION = 0
    S1_GROWTH = 1
    S2_DETECTED = 2
    S3_INTERNAL_RESPONSE = 3
    S4_EXTERNAL_RESPONSE = 4
    S5_CONTAINED = 5
    S6_PARTIAL_LOSS = 6
    S7_TOTAL_LOSS = 7


class InitiationClass(Enum):
    """Entry-point / cause class assigned to a fire at initiation.

    Drawn from the per-CommercialType categorical in fire_matrices.json. Seeds
    the building entry point the progression stage starts from.
    """
    INTERNAL_ELECTRICAL = "InternalElectrical"
    KITCHEN_OCCUPANT = "KitchenOccupant"
    PLANT_TECHNICAL = "PlantTechnical"
    PROCESS_RELATED = "ProcessRelated"
    BASEMENT_SERVICE = "BasementService"
    EXTERNAL_EXPOSURE = "ExternalExposure"
    OTHER = "Other"


# ===========================================================================
# Run configuration
# ===========================================================================


@dataclass
class FireRunConfig:
    """Top-level simulation knobs.

    Attributes:
        n_sim: number of Monte Carlo draws per asset (Poisson initiation).
        step_minutes: progression step length in minutes (15-min steps).
        max_steps: max progression steps per fire (200 steps * 15 min = 50 h
            controllability horizon).
        horizon_years: exposure horizon for the Poisson rate (1.0 = annual).
    """
    n_sim: int = 1000
    step_minutes: int = 15
    max_steps: int = 200
    horizon_years: float = 1.0

    @property
    def horizon_hours(self) -> float:
        """Total progression horizon in hours (max_steps * step length)."""
        return self.max_steps * self.step_minutes / 60.0


# ===========================================================================
# Model A — initiation parameters
# ===========================================================================


@dataclass
class InitiationConfig:
    """Model A seed parameters — Poisson initiation frequency.

    lambda_i = lambda_0,c * m_occ * m_proc * m_cond * m_protection * m_history

    All mappings are keyed on the CDM option vocabularies (CommercialType,
    OccupancyStatus, PropertyCondition, resilience levels, FireDamageSeverity).
    Values are seeds from fire_matrices.json.

    Attributes:
        base_annual_frequency_by_type: lambda_0,c per CommercialType (events/yr).
        m_occ_by_status: occupancy multiplier per OccupancyStatus.
        m_proc_by_type: process-load multiplier per CommercialType.
        m_proc_business_rates_override: override m_proc by BusinessRatesCategory.
        m_cond_by_condition: condition multiplier per PropertyCondition.
        m_protection_by_level: protection multiplier per resilience level.
        m_history: history multiplier block (recent_years + severity keys).
        initiation_classes: ordered InitiationClass label list.
        initiation_class_priors_by_type: per-type categorical (sums to 1).
    """
    base_annual_frequency_by_type: Dict[str, float] = field(default_factory=dict)
    m_occ_by_status: Dict[str, float] = field(default_factory=dict)
    m_proc_by_type: Dict[str, float] = field(default_factory=dict)
    m_proc_business_rates_override: Dict[str, float] = field(default_factory=dict)
    m_cond_by_condition: Dict[str, float] = field(default_factory=dict)
    m_protection_by_level: Dict[str, float] = field(default_factory=dict)
    m_history: Dict[str, float] = field(default_factory=dict)
    initiation_classes: List[str] = field(default_factory=list)
    initiation_class_priors_by_type: Dict[str, List[float]] = field(default_factory=dict)


# ===========================================================================
# Model B/C/D — progression parameters (seeds for the next build stage)
# ===========================================================================


@dataclass
class ProgressionConfig:
    """Model B/C/D seed parameters — stepwise progression and the PNR gate.

    Loaded now so all numeric governance lives in one file; consumed by the
    next build stage (15-min progression engine).

    Attributes:
        growth_per_step_intensity: I_t additive growth per step by compartmentation.
        i_crit_by_level: critical intensity threshold graded by suppression level.
        detection_time_multiplier_by_level: time-to-detect scale per level.
        suppression_growth_multiplier_by_level: growth scale once suppressing.
        suppression_bite_multiplier_by_level: time-to-bite scale per suppression level.
        race_jitter: per-fire lognormal sigmas for the intensity-race timing/growth.
        passive_effectiveness_ranges: [min,max] passive defence by field.
        response_effectiveness_ranges: [min,max] active response by field.
        upper_floor_penalty_per_storey: {"range":[min,max], "max_storeys":int}.
        fire_service_reach: {"reach_storeys":int, "internal_suppression_threshold":int,
            "no_reach_bite_steps":float} — the fire-truck reach cut-off.
        timing: base steps for detection and suppression-bite.
        intensity_dynamics: passive_damp_weight + level-index thresholds.
        controllability: matrix-selection weights + switch_threshold.
        transition_matrices: named 8x8 row-stochastic matrices.
    """
    growth_per_step_intensity: Dict[str, float] = field(default_factory=dict)
    i_crit_by_level: Dict[str, float] = field(default_factory=dict)
    detection_time_multiplier_by_level: Dict[str, float] = field(default_factory=dict)
    suppression_growth_multiplier_by_level: Dict[str, float] = field(default_factory=dict)
    suppression_bite_multiplier_by_level: Dict[str, float] = field(default_factory=dict)
    race_jitter: Dict[str, float] = field(default_factory=dict)
    passive_effectiveness_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    response_effectiveness_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    upper_floor_penalty_per_storey: Dict[str, object] = field(default_factory=dict)
    fire_service_reach: Dict[str, float] = field(default_factory=dict)
    timing: Dict[str, float] = field(default_factory=dict)
    intensity_dynamics: Dict[str, float] = field(default_factory=dict)
    controllability: Dict[str, object] = field(default_factory=dict)
    transition_matrices: Dict[str, List[List[float]]] = field(default_factory=dict)


# ===========================================================================
# Aggregate config
# ===========================================================================


@dataclass
class FireModelConfig:
    """Aggregate fire-model configuration (run knobs + all seed parameters)."""
    run: FireRunConfig
    initiation: InitiationConfig
    progression: ProgressionConfig


# ===========================================================================
# Loader
# ===========================================================================


DEFAULT_MATRICES_PATH = Path(__file__).parent / "fire_matrices.json"


def _strip_docs(obj):
    """Recursively drop documentation keys (_doc, _meta) from loaded JSON."""
    if isinstance(obj, dict):
        return {k: _strip_docs(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(obj, list):
        return [_strip_docs(v) for v in obj]
    return obj


def load_fire_config(
    matrices_path: Path = DEFAULT_MATRICES_PATH,
    run: FireRunConfig = None,
) -> FireModelConfig:
    """Load the fire model config from the seed-matrices JSON.

    Args:
        matrices_path: path to fire_matrices.json (defaults next to this file).
        run: optional run-config override; defaults to FireRunConfig().

    Returns:
        A hydrated FireModelConfig.
    """
    raw = json.loads(Path(matrices_path).read_text())
    data = _strip_docs(raw)

    init_raw = data["initiation"]
    classes = init_raw["initiation_class_priors_by_type"].pop("classes")
    initiation = InitiationConfig(
        base_annual_frequency_by_type=init_raw["base_annual_frequency_by_type"],
        m_occ_by_status=init_raw["m_occ_by_status"],
        m_proc_by_type=init_raw["m_proc_by_type"],
        m_proc_business_rates_override=init_raw["m_proc_business_rates_override"],
        m_cond_by_condition=init_raw["m_cond_by_condition"],
        m_protection_by_level=init_raw["m_protection_by_level"],
        m_history=init_raw["m_history"],
        initiation_classes=classes,
        initiation_class_priors_by_type=init_raw["initiation_class_priors_by_type"],
    )

    prog_raw = data["progression"]
    progression = ProgressionConfig(
        growth_per_step_intensity=prog_raw["growth_per_step_intensity"],
        i_crit_by_level=prog_raw["i_crit_by_level"],
        detection_time_multiplier_by_level=prog_raw["detection_time_multiplier_by_level"],
        suppression_growth_multiplier_by_level=prog_raw["suppression_growth_multiplier_by_level"],
        suppression_bite_multiplier_by_level=prog_raw["suppression_bite_multiplier_by_level"],
        race_jitter=prog_raw["race_jitter"],
        passive_effectiveness_ranges={
            k: tuple(v) for k, v in prog_raw["passive_effectiveness_ranges"].items()
        },
        response_effectiveness_ranges={
            k: tuple(v) for k, v in prog_raw["response_effectiveness_ranges"].items()
        },
        upper_floor_penalty_per_storey=prog_raw["upper_floor_penalty_per_storey"],
        fire_service_reach=prog_raw["fire_service_reach"],
        timing=prog_raw["timing"],
        intensity_dynamics=prog_raw["intensity_dynamics"],
        controllability=prog_raw["controllability"],
        transition_matrices=prog_raw["transition_matrices"],
    )

    return FireModelConfig(
        run=run or FireRunConfig(),
        initiation=initiation,
        progression=progression,
    )
