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

"""Typed configuration for the Event Frequency Model (MKM-EF-001).

Holds the peaks-over-threshold calibration knobs. Every numeric value the
frequency layer uses lives here (rule R1); no module outside ``config`` may
embed one.

The values are engineering-judgement SEEDS chosen from standard UK flood
frequency practice, not calibrated values:

- ``declustering_window_days`` — the Flood Estimation Handbook independence
  criterion for peaks-over-threshold is of the order of three times the mean
  time to peak, which for the catchment scales modelled here is a few days.
- ``target_exceedance_rate_per_year`` — POT series are conventionally extracted
  at one to five peaks per year; below one the series is too sparse to estimate
  dispersion, above five the peaks stop being independent extremes.

See ``docs/storm_freq/frequency_layer_definition_and_plan_v2.md`` §4.2.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple

# Model identity, stamped into every calibration's provenance record so a
# persisted rate can be traced to the model version that produced it.
MODEL_ID: str = "MKM-EF-001"
MODEL_VERSION: str = "1.0.0"  # 1.0: built, wired to pricing, validated end-to-end (Stages 1-4)

# Dataset identifier recorded as the source of a peaks-over-threshold
# calibration run over the gauge daily record.
SOURCE_DATASET_GAUGE_DAILY: str = "gauge_historical_daily"

# Peril labels. The frequency layer is generic; only flood is calibrated in
# this phase, with wind, fire and seismic attaching later.
PERIL_FLOOD: str = "flood"

# Key carried on each storm dict naming the hours-clause event it belongs to.
# Written by the hazard loader, read by the frequency layer.
SEQUENCE_ID_KEY: str = "sequence_id"

# Seed for the gauge response model's character and noise draws.
#
# These draws were previously unseeded, which made every hazard curve
# irreproducible: twelve rebuilds of one gauge spanned 36-48% of the mean.
# Seeding is per gauge and per (gauge, storm), derived from this value and the
# identifiers, so a gauge's character does not shift when an unrelated gauge is
# added to or removed from the portfolio.
GAUGE_RESPONSE_SEED: int = 20260723

# Storm intensity categories in ascending severity. An event's category is the
# most severe category among the storms in its sequence.
INTENSITY_SEVERITY_ORDER: Tuple[str, ...] = (
    "minimal", "baseline", "moderate", "severe", "extreme", "catastrophic",
)

# Relative frequency of each intensity category among qualifying events in a
# real year.
#
# THE CATALOGUE IS NOT A SAMPLE OF THIS DISTRIBUTION. MKM-SS-001 generates its
# batches from config.port DEFAULT_INTENSITY_WEIGHTS — 40% moderate, 35%
# severe, 20% extreme, 5% catastrophic, and no minimal or baseline at all —
# because it exists to train the stress classifier, where oversampling the
# interesting region is exactly right.
#
# Resampling that catalogue uniformly and calling the result P(flood | event)
# therefore answers a different question: P(flood | event is at least
# moderate). Multiplying that by a lambda counting ALL qualifying events
# double-counts severity. Measured, it implied a severe flood every 0.81 years.
#
# These weights reweight the catalogue back onto the population it is meant to
# represent. They are engineering-judgement seeds: most qualifying storms are
# unremarkable, and the tail thins by roughly a factor of three per category.
# Calibrated 2026-07-23 to a severe-or-worse share of 8%, on the owner's
# judgement. The internal 8:3:1 ratio across severe/extreme/catastrophic is
# unchanged; only the tail's total mass moved (from 12%). On halong this puts
# the severe-flood return period at roughly 7 years against the pre-frequency
# model's 8-10, so the annualisation is no longer buying its reprice purely by
# making floods more frequent.
EVENT_POPULATION_WEIGHTS: Dict[str, float] = {
    "minimal": 0.420,
    "baseline": 0.310,
    "moderate": 0.190,
    "severe": 0.053,
    "extreme": 0.020,
    "catastrophic": 0.007,
}

# Days per year used to convert a record span into a length in years. The
# fractional value keeps long records from drifting against leap years.
DAYS_PER_YEAR: float = 365.25

# Length of one block in the annual count series. Whole 365-day blocks are
# measured from the first observation rather than split on calendar years: a
# calendar split would discard a partial first and last year, and splitting a
# seasonal record mid-flood-season would bias the counts.
ANNUAL_BLOCK_DAYS: int = 365


@dataclass(frozen=True)
class PotConfig:
    """Peaks-over-threshold extraction knobs.

    Attributes:
        declustering_window_days: minimum separation between independent peaks.
            Exceedances closer together than this belong to one flood event and
            collapse to their maximum.
        target_exceedance_rate_per_year: the mean number of declustered peaks
            per year the threshold search aims for. Set from the catchment
            arrival rate by ``load_frequency_config``, so the qualifying-event
            threshold and lambda describe the same event population.
        target_rate_tolerance: acceptable absolute deviation from the target
            rate before the search reports that it failed to converge.
        search_quantile_lo: lowest quantile of the record considered as a
            candidate threshold.
        search_quantile_hi: highest quantile of the record considered.
        search_steps: number of candidate thresholds evaluated between the two
            quantile bounds.
    """

    declustering_window_days: int = 5
    target_exceedance_rate_per_year: float = 4.5
    target_rate_tolerance: float = 0.5
    search_quantile_lo: float = 0.90
    search_quantile_hi: float = 0.999
    search_steps: int = 200


# Catchment event arrival rates, in qualifying storm events per year.
#
# lambda is a property of the CATCHMENT, not of a gauge. A storm arrives over
# the catchment and reaches every gauge in it; what differs per gauge is the
# conditional response, not the arrival rate. Multiplying a per-gauge
# exceedance rate by a per-gauge conditional would square the conditional and
# double-count — see the plan's §4.3 event-alignment task.
#
# These are engineering-judgement seeds. The per-gauge peaks-over-threshold
# calibration validates them rather than producing them: lambda multiplied by
# the per-gauge conditional must reproduce that gauge's measured rate.
CATCHMENT_LAMBDA_PER_YEAR: Dict[str, float] = {
    "thames": 4.5,
}

# Arrival rate used for a catchment with no seed of its own.
DEFAULT_LAMBDA_PER_YEAR: float = 4.5

# Wind peril label, for the per-peril arrival-rate registry below.
PERIL_WIND: str = "wind"

# Per-catchment WIND event arrival rates (MKM-EF-001, Stage 6f). This is the
# per-peril lambda registry the plan's §4.14 architected for.
#
# It is deliberately EMPTY. Under the current 1:1 storm-typhoon coupling wind is
# not an independent arrival process: every wind event is paired with a storm
# sequence, and the wind leg works in that sequence space, dropping any typhoon
# with no paired sequence (see port .../pricing/_wind.py). So wind shares the
# storm event arrival rate, and ``catchment_wind_lambda`` falls back to
# ``catchment_lambda`` for every catchment.
#
# A genuinely independent wind rate only becomes meaningful once those unpaired,
# off-sequence typhoon events are counted — a larger change that also re-derives
# the coupled union/intersection legs and, because it moves the priced wind
# spread, is gated on model-risk sign-off and real typhoon data (the same
# circularity as flood lambda applies on synthetic catchments — plan §5). Until
# then this registry is the seam, not a set of validated rates: an entry here
# overrides only the ADDITIVE wind-loss view, never the priced spread.
CATCHMENT_WIND_LAMBDA_PER_YEAR: Dict[str, float] = {}

# Per-catchment annual growth of the arrival rate (MKM-EF-001, Stage 6h): the
# fractional change in lambda per contract year, for a non-stationary
# (climate-drifting) multi-year term structure — lambda_t = lambda_0 * (1+g)^t.
#
# Deliberately EMPTY, default zero — a stationary rate, the behaviour of every
# stage before 6h. This is the seam, not a set of validated trends: a non-zero
# growth moves a priced multi-year quantity, so populating it is a model-risk
# decision resting on a real climate signal. With the registry empty the term
# structure is byte-identical to the stationary one.
CATCHMENT_ANNUAL_GROWTH: Dict[str, float] = {}

# Growth used for a catchment with no seed of its own: stationary.
DEFAULT_ANNUAL_GROWTH: float = 0.0

# Catchments whose wind peril is priced as an INDEPENDENT arrival process rather
# than coupled 1:1 to the storm sequences (MKM-EF-001, Stage 6i).
#
# Deliberately EMPTY: every catchment is coupled by default, the behaviour of
# every stage before 6i. The coupled model drops any typhoon with no paired
# storm sequence, so it understates wind where unpaired typhoons are common; the
# decoupled model counts those events and prices wind on its own lambda, treating
# flood and wind as independent Poisson processes for the union/intersection.
#
# That independence is an explicit modelling assumption — it trades the coupled
# model's pairing correlation for coverage of unpaired events — and the wind rate
# it uses is unvalidated on synthetic catchments (the plan-§5 circularity), so
# opting a catchment in is a model-risk decision resting on real typhoon data.
DECOUPLED_WIND_CATCHMENTS: frozenset = frozenset()


@dataclass(frozen=True)
class RateConfig:
    """Arrival-rate estimation and fallback knobs.

    Attributes:
        min_record_years: shortest record accepted for a per-gauge rate. Below
            this the regional fallback is used and recorded in provenance.
        min_events_for_rate: fewest declustered peaks accepted for a per-gauge
            rate. Below this the regional fallback is used.
        min_plausible_return_period_years: shortest severe-flood return period
            a calibration may imply before it is flagged. A trigger breached
            more often than this is not a severe flood.
        max_plausible_return_period_years: longest return period before a
            calibration is flagged as implausibly benign.
        regional_fallback_lambda_per_year: the rate assigned when a gauge record
            is too short or too sparse to support its own estimate.
        return_periods_years: the return-period grid reported in output tables.
    """

    min_record_years: float = 5.0
    min_events_for_rate: int = 5
    min_plausible_return_period_years: float = 2.0
    max_plausible_return_period_years: float = 500.0
    regional_fallback_lambda_per_year: float = DEFAULT_LAMBDA_PER_YEAR
    return_periods_years: Tuple[int, ...] = (2, 5, 10, 25, 50, 100, 200)


@dataclass(frozen=True)
class SelectionConfig:
    """Distribution-family selection knobs (MKM-EF-001, Stage 2).

    Only two families are fitted: Poisson (the default) and Negative Binomial
    (for over-dispersed counts, the physical signature of storm clustering).

    There is deliberately no under-dispersion family. Under-dispersion in this
    platform is largely an artefact of declustering — merging nearby events
    caps the annual count and pushes the variance below the mean — measured at a
    mean dispersion index of 0.90 when genuinely-Poisson daily injection is put
    through the pipeline. Fitting a distribution to it would dress a pipeline
    quirk as a physical regularity. Under-dispersion is therefore recorded and
    flagged, and Poisson selected as the nearest fittable family.

    Attributes:
        overdispersion_significance: two-sided significance level for the
            chi-square dispersion test. The test guards against selecting
            NegBin on a dispersion index that is high only by sampling chance —
            with fifty years of counts, a genuine Poisson process produces
            index values up to about 1.4 (§5.2), so a bare ``D > 1`` rule would
            over-select NegBin badly.
        prefer_poisson_within_aic: when NegBin's AIC beats Poisson's by less
            than this margin, keep Poisson. NegBin nests Poisson in the limit,
            so a negligible AIC gain is not evidence for the extra parameter.
        force_family: optional family name (``"poisson"`` / ``"negbin"``) that
            overrides selection for every gauge. The override and its
            justification are logged (SR 11-7); ``None`` leaves selection
            data-driven.
    """

    overdispersion_significance: float = 0.05
    prefer_poisson_within_aic: float = 2.0
    force_family: object = None


@dataclass(frozen=True)
class SimulationConfig:
    """Monte Carlo year-simulation knobs.

    Attributes:
        n_years: number of one-year simulations per run. Ten thousand years
            costs about 0.4s for a full portfolio on an M2 and holds the
            sampling error near 1.6% of the annual probability. Raising it
            tightens accuracy as the square root: a hundred thousand years is
            about 4s and 0.5%. Run-to-run stability does not depend on this
            number — the seed is pinned, so a re-run reprices identically
            either way; what it buys is closeness to the true expectation.
        seed: default seed. Every run is seeded, so a quote is reproducible.
        reconciliation_sigmas: how many sampling standard errors the simulated
            annual probability may sit from its closed form before the run is
            flagged. Expressed in standard errors rather than as a fixed
            percentage because the sampling error depends on ``n_years``: a
            fixed 2% band false-alarms on 17% of runs at ten thousand years
            while never binding at all at a million.
    """

    n_years: int = 10_000
    seed: int = 20260722
    reconciliation_sigmas: float = 4.0


@dataclass(frozen=True)
class FrequencyConfig:
    """Top-level frequency-model configuration.

    Passed explicitly into every calibration call so that calibration is a pure
    function of (data, config) and its hash can be recorded in provenance.

    Attributes:
        pot: peaks-over-threshold extraction knobs.
        rate: arrival-rate estimation and fallback knobs.
        selection: distribution-family selection knobs.
        simulation: Monte Carlo year-simulation knobs.
    """

    pot: PotConfig = field(default_factory=PotConfig)
    rate: RateConfig = field(default_factory=RateConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
