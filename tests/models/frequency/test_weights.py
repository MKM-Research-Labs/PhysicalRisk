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

"""Tests for population reweighting of the event catalogue (MKM-EF-001).

The storm catalogue is an importance sample, not a fair sample of the events a
year contains: MKM-SS-001 generates it to train the stress classifier, so it
oversamples severe categories and omits the mild ones entirely. Averaging over
it uniformly answers ``P(flood | event is at least moderate)``, and multiplying
that by a rate counting *all* qualifying events double-counts severity.

These tests fix the correction, and — just as importantly — the guard that made
the error visible in the first place: the implied return period.
"""

import numpy as np
import pytest

from config.frequency import (
    EVENT_POPULATION_WEIGHTS,
    INTENSITY_SEVERITY_ORDER,
    SimulationConfig,
)
from models.frequency.datastructures import EventCatalogue
from models.frequency.events import (
    build_catalogue,
    effective_sample_size,
    event_category,
    population_weights,
    storm_category,
)
from models.frequency.events._weights import DEFAULT_CATEGORY
from models.frequency.ylt import apply_catalogue, draw_event_years, simulate_years
from models.hazard.io import load_storms_from_sequences

# The distribution MKM-SS-001 actually generates from (config.port
# DEFAULT_INTENSITY_WEIGHTS): no minimal or baseline at all.
_CATALOGUE_MIX = {"moderate": 0.40, "severe": 0.35, "extreme": 0.20,
                  "catastrophic": 0.05}


class _Response:
    def __init__(self, storm_id, peak_level_m):
        self.storm_id = storm_id
        self.peak_level_m = peak_level_m


def _catalogue(n_events=800, seed=7):
    """A catalogue drawn the way the stress generator draws one."""
    rng = np.random.default_rng(seed)
    base = {"minimal": 8.0, "baseline": 16.0, "moderate": 28.0,
            "severe": 45.0, "extreme": 70.0, "catastrophic": 110.0}
    names = list(_CATALOGUE_MIX)
    probabilities = [_CATALOGUE_MIX[n] for n in names]

    sequences = []
    for i in range(n_events):
        category = str(rng.choice(names, p=probabilities))
        n_storms = int(rng.choice([1, 1, 1, 2, 2, 3]))
        sequences.append({
            "sequence_id": f"SEQ-{i:04d}",
            "storms": [{
                "storm_id": f"ST-{i:04d}-{j}",
                "precipitation_mm": float(rng.gamma(6, base[category] / 6)),
                "duration_hours": 12,
                "intensity_factor": 1.0,
                "peak_position": 0.5,
                "intensity_category": category,
            } for j in range(n_storms)],
        })

    storms = load_storms_from_sequences(sequences_data={"sequences": sequences})
    responses = {"G1": [
        _Response(s["storm_id"], s["effective_precipitation_mm"] / 40.0)
        for s in storms
    ]}
    return build_catalogue(responses, storms)


# ------------------------------------------------------------- categorisation

def test_storm_category_reads_the_label():
    assert storm_category({"intensity_category": "severe"}) == "severe"


def test_storm_category_is_case_and_space_insensitive():
    assert storm_category({"intensity_category": " Severe "}) == "severe"


def test_an_unlabelled_storm_takes_the_mildest_category():
    """The conservative default: an unknown must not be resampled as if it were
    a catastrophe."""
    assert storm_category({}) == DEFAULT_CATEGORY
    assert storm_category({"intensity_category": None}) == DEFAULT_CATEGORY
    assert storm_category({"intensity_category": "not-a-category"}) == DEFAULT_CATEGORY
    assert DEFAULT_CATEGORY == INTENSITY_SEVERITY_ORDER[0]


def test_an_event_takes_its_most_severe_storm_category():
    """Matching how its level is aggregated: the event is characterised by its
    worst moment, not its average one."""
    assert event_category(["moderate", "catastrophic", "minimal"]) == "catastrophic"
    assert event_category(["minimal", "baseline"]) == "baseline"


def test_an_event_with_no_storms_takes_the_default():
    assert event_category([]) == DEFAULT_CATEGORY


def test_catalogue_records_the_event_category():
    catalogue = _catalogue(n_events=50)
    assert len(catalogue.categories) == catalogue.n_events
    assert set(catalogue.categories) <= set(INTENSITY_SEVERITY_ORDER)


# ------------------------------------------------------------------- weighting

def test_weights_are_normalised():
    weights = population_weights(["moderate"] * 3 + ["severe"] * 2)
    assert weights.sum() == pytest.approx(1.0)


def test_weights_recover_the_population_shares():
    """The point of the correction: whatever the catalogue's mix, the weight
    landing on each category is its population share."""
    categories = ["moderate"] * 40 + ["severe"] * 35 + ["extreme"] * 20 + \
                 ["catastrophic"] * 5
    weights = population_weights(categories)

    present = {"moderate", "severe", "extreme", "catastrophic"}
    total = sum(EVENT_POPULATION_WEIGHTS[c] for c in present)
    for category in present:
        share = sum(w for c, w in zip(categories, weights) if c == category)
        assert share == pytest.approx(EVENT_POPULATION_WEIGHTS[category] / total)


def test_an_over_represented_category_is_down_weighted_per_event():
    """Severe is 35% of the catalogue but 8% of the population, so each severe
    event must carry less weight than each moderate one."""
    categories = ["moderate"] * 40 + ["severe"] * 35
    weights = population_weights(categories)
    assert weights[0] > weights[-1]


def test_empty_catalogue_has_no_weights():
    assert population_weights([]).size == 0


def test_weights_fall_back_to_uniform_when_no_category_is_known():
    """A degenerate catalogue is better sampled evenly than not at all."""
    weights = population_weights(["not-a-category"] * 4)
    assert weights == pytest.approx(np.full(4, 0.25))


def test_effective_sample_size_equals_the_count_when_uniform():
    assert effective_sample_size(np.full(100, 0.01)) == pytest.approx(100.0)


def test_effective_sample_size_falls_as_weight_concentrates():
    """Reweighting costs precision; this is the diagnostic that says how much."""
    concentrated = np.array([0.97, 0.01, 0.01, 0.01])
    assert effective_sample_size(concentrated) < 2.0


def test_effective_sample_size_of_nothing_is_zero():
    assert effective_sample_size(np.zeros(0)) == 0.0


def test_reweighting_costs_some_precision_but_not_most_of_it():
    catalogue = _catalogue()
    ess = effective_sample_size(catalogue.weights)
    assert 0.5 * catalogue.n_events < ess < catalogue.n_events


# ------------------------------------------------- the conditional it produces

def test_the_weighted_conditional_is_lower_than_the_unweighted_one():
    """The correction's whole purpose. The catalogue over-represents severe
    storms, so averaging over it uniformly overstates the flood conditional."""
    catalogue = _catalogue()
    threshold = 2.4

    unweighted = float(catalogue.flood_flags("G1", threshold).mean())
    weighted = catalogue.conditional_probability("G1", threshold)

    assert weighted < unweighted


def test_an_empty_catalogue_has_no_conditional():
    catalogue = EventCatalogue(
        event_ids=(), storms_per_event=(), categories=(),
        weights=np.zeros(0), coverage=0.0, peak_levels={"G1": np.zeros(0)})
    assert catalogue.conditional_probability("G1", 1.0) == 0.0


# ------------------------------------------------------ the return-period guard

def test_the_implied_return_period_is_the_reciprocal_annual_rate():
    catalogue = _catalogue()
    rate = 4.5
    conditional = catalogue.conditional_probability("G1", 2.4)

    assert catalogue.implied_return_period_years("G1", 2.4, rate) == pytest.approx(
        1.0 / (rate * conditional))


def test_a_gauge_that_never_floods_has_an_infinite_return_period():
    catalogue = _catalogue(n_events=50)
    assert catalogue.implied_return_period_years("G1", 1e9, 4.5) == float("inf")


def test_the_guard_would_have_caught_the_unweighted_error():
    """The regression this whole correction exists for.

    A conditional probability is easy to misread; a severe flood every nine
    months is obviously wrong. Reweighting must push the implied return period
    materially further out — and the assertion is deliberately one-sided,
    because the *level* is still unanchored (plan §6.2) and only the direction
    of the correction is established at this stage."""
    catalogue = _catalogue()
    threshold, rate = 2.4, 4.5

    unweighted_conditional = float(catalogue.flood_flags("G1", threshold).mean())
    unweighted_return_period = 1.0 / (rate * unweighted_conditional)
    weighted_return_period = catalogue.implied_return_period_years(
        "G1", threshold, rate)

    assert weighted_return_period > unweighted_return_period


# ----------------------------------------------------------- weighted sampling

def test_weighted_draws_shift_the_simulated_probability_down():
    catalogue = _catalogue()
    flags = catalogue.flood_flags("G1", 2.4)
    config = SimulationConfig(n_years=20_000)

    uniform = simulate_years(flags, 4.5, config)
    weighted = simulate_years(flags, 4.5, config, weights=catalogue.weights)

    assert weighted.annual_flood_probability() < uniform.annual_flood_probability()


def test_the_simulated_conditional_matches_the_catalogue():
    """``p_event`` feeds the reconciliation gate, so it has to be the weighted
    conditional — otherwise the gate compares against the wrong expectation."""
    catalogue = _catalogue()
    simulation = simulate_years(
        catalogue.flood_flags("G1", 2.4), catalogue.effective_lambda(4.5),
        SimulationConfig(n_years=5_000), weights=catalogue.weights)

    # The sampler works within the catalogue, so its conditional is the
    # within-catalogue one; scaling by coverage recovers the population figure.
    assert simulation.p_event * catalogue.coverage == pytest.approx(
        catalogue.conditional_probability("G1", 2.4))


def test_weighted_draws_reproduce_the_weight_distribution():
    """Every event should be drawn about as often as its weight says."""
    catalogue = _catalogue(n_events=40)
    draws = draw_event_years(
        catalogue.n_events, 50.0, SimulationConfig(n_years=20_000),
        weights=catalogue.weights)

    counts = np.bincount(draws.event_indices, minlength=catalogue.n_events)
    observed = counts / counts.sum()
    assert np.abs(observed - catalogue.weights).max() < 0.01


def test_mismatched_weights_fall_back_to_uniform_sampling():
    """A weight vector of the wrong length is ignored rather than crashing a
    portfolio run mid-flight."""
    catalogue = _catalogue(n_events=30)
    draws = draw_event_years(
        catalogue.n_events, 4.5, SimulationConfig(n_years=2_000),
        weights=np.array([0.5, 0.5]))
    assert draws.event_indices.size > 0


def test_drawn_indices_stay_inside_the_catalogue():
    catalogue = _catalogue(n_events=25)
    draws = draw_event_years(
        catalogue.n_events, 6.0, SimulationConfig(n_years=5_000),
        weights=catalogue.weights)
    assert draws.event_indices.min() >= 0
    assert draws.event_indices.max() < catalogue.n_events


def test_weighted_runs_stay_reproducible():
    catalogue = _catalogue(n_events=60)
    config = SimulationConfig(n_years=3_000)
    first = simulate_years(catalogue.flood_flags("G1", 2.4), 4.5, config,
                           seed=11, weights=catalogue.weights)
    second = simulate_years(catalogue.flood_flags("G1", 2.4), 4.5, config,
                            seed=11, weights=catalogue.weights)
    assert np.array_equal(first.flood_events_per_year,
                          second.flood_events_per_year)


def test_apply_catalogue_reports_the_unweighted_mean_without_weights():
    catalogue = _catalogue(n_events=40)
    flags = catalogue.flood_flags("G1", 2.4)
    draws = draw_event_years(catalogue.n_events, 4.5,
                             SimulationConfig(n_years=1_000))
    assert apply_catalogue(draws, flags).p_event == pytest.approx(
        float(flags.mean()))


# ------------------------------------------------------- the annualisation seam

def test_annual_rate_is_lambda_times_the_conditional():
    from models.frequency import annual_exceedance_rate
    assert annual_exceedance_rate(4.5, 0.1) == pytest.approx(0.45)


def test_annual_rate_clamps_negative_inputs():
    from models.frequency import annual_exceedance_rate
    assert annual_exceedance_rate(-1.0, 0.1) == 0.0
    assert annual_exceedance_rate(4.5, -0.1) == 0.0


def test_return_period_is_the_reciprocal_rate():
    from models.frequency import return_period_years
    assert return_period_years(4.5, 0.1) == pytest.approx(1 / 0.45)


def test_a_zero_rate_gives_an_infinite_return_period():
    from models.frequency import return_period_years
    assert return_period_years(4.5, 0.0) == float("inf")
    assert return_period_years(0.0, 0.1) == float("inf")


# --------------------------------------------------- coverage of the population

def test_coverage_is_the_mass_of_the_categories_present():
    from models.frequency.events import catalogue_coverage
    assert catalogue_coverage(["moderate", "severe"]) == pytest.approx(
        EVENT_POPULATION_WEIGHTS["moderate"] + EVENT_POPULATION_WEIGHTS["severe"])


def test_coverage_of_an_empty_catalogue_is_zero():
    from models.frequency.events import catalogue_coverage
    assert catalogue_coverage([]) == 0.0


def test_coverage_ignores_repeats():
    from models.frequency.events import catalogue_coverage
    assert catalogue_coverage(["severe"] * 50) == pytest.approx(
        EVENT_POPULATION_WEIGHTS["severe"])


def test_a_generated_catalogue_covers_only_part_of_the_population():
    """The generated catalogue has no minimal or baseline events, and those
    carry most of the population's mass. Coverage well below one is the whole
    reason the conditional has to be scaled rather than renormalised."""
    catalogue = _catalogue()
    assert 0.0 < catalogue.coverage < 0.5


def test_mild_events_are_counted_in_the_denominator_not_dropped():
    """The regression for a 3.7x overstatement.

    Renormalising the weights onto the categories that happen to be present
    silently moves the missing mild-event mass to the severe end. Scaling by
    coverage instead keeps those events in the denominator at a conditional of
    zero, which is what they are."""
    catalogue = _catalogue()
    flags = catalogue.flood_flags("G1", 2.4)

    renormalised = float(np.dot(flags, catalogue.weights))
    population = catalogue.conditional_probability("G1", 2.4)

    assert population == pytest.approx(renormalised * catalogue.coverage)
    assert population < renormalised


def test_effective_lambda_scales_the_rate_to_the_catalogue():
    catalogue = _catalogue()
    assert catalogue.effective_lambda(4.5) == pytest.approx(
        4.5 * catalogue.coverage)


def test_the_two_paths_agree_on_the_annual_rate():
    """Scaling the conditional and scaling the rate must give the same annual
    number, or the sampler and the closed form would disagree by construction."""
    from models.frequency import annual_exceedance_rate
    catalogue = _catalogue()
    flags = catalogue.flood_flags("G1", 2.4)

    via_conditional = annual_exceedance_rate(
        4.5, catalogue.conditional_probability("G1", 2.4))
    via_rate = annual_exceedance_rate(
        catalogue.effective_lambda(4.5), float(np.dot(flags, catalogue.weights)))

    assert via_conditional == pytest.approx(via_rate)
