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
MODEL_VERSION: str = "0.1.0"

# Dataset identifier recorded as the source of a peaks-over-threshold
# calibration run over the gauge daily record.
SOURCE_DATASET_GAUGE_DAILY: str = "gauge_historical_daily"

# Peril labels. The frequency layer is generic; only flood is calibrated in
# this phase, with wind, fire and seismic attaching later.
PERIL_FLOOD: str = "flood"

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


@dataclass(frozen=True)
class RateConfig:
    """Arrival-rate estimation and fallback knobs.

    Attributes:
        min_record_years: shortest record accepted for a per-gauge rate. Below
            this the regional fallback is used and recorded in provenance.
        min_events_for_rate: fewest declustered peaks accepted for a per-gauge
            rate. Below this the regional fallback is used.
        regional_fallback_lambda_per_year: the rate assigned when a gauge record
            is too short or too sparse to support its own estimate.
        return_periods_years: the return-period grid reported in output tables.
    """

    min_record_years: float = 5.0
    min_events_for_rate: int = 5
    regional_fallback_lambda_per_year: float = DEFAULT_LAMBDA_PER_YEAR
    return_periods_years: Tuple[int, ...] = (2, 5, 10, 25, 50, 100, 200)


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
        simulation: Monte Carlo year-simulation knobs.
    """

    pot: PotConfig = field(default_factory=PotConfig)
    rate: RateConfig = field(default_factory=RateConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
