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

"""Tests for the subject-loss adapter (MKM-EF-001, Stage 6b).

Four things are pinned:

- **The gauge vector maps peaks through the caller's curve** and clamps at zero,
  and an unknown gauge yields zeros rather than raising.
- **Asset records regroup onto events by their maximum**, matching the
  occurrence rule, and unresolved identifiers are refused rather than silently
  dropped — the failure that once produced a confident zero from real floods.
- **The coverage scaling is applied once and consistently.** The trap this
  adapter exists to close: the event loss table scales lambda by coverage
  itself while the sampler does not, so a naive wiring would overstate every
  loss by ``1/coverage``. The adapter's average annual loss must match the
  closed form that already carries the scaling.
- **Shared draws keep subjects correlated**, the loss-side statement of the
  portfolio design.
"""

import numpy as np
import pytest

from config.frequency import load_frequency_config
from models.frequency import (
    loss_metrics,
    peak_level_losses,
    regrouped_event_losses,
    shared_draws,
)
from models.frequency.datastructures import EventCatalogue, EventFrame

_PERIODS = (2, 10, 100)


@pytest.fixture
def config():
    return load_frequency_config("thames").simulation


def _weights(n=4):
    w = np.array([0.4, 0.3, 0.2, 0.1][:n], dtype=float)
    return w / w.sum()


def _catalogue(coverage=0.3):
    return EventCatalogue(
        event_ids=("E0", "E1", "E2", "E3"),
        storms_per_event=(1, 1, 1, 1),
        categories=("minimal", "moderate", "severe", "extreme"),
        weights=_weights(),
        coverage=coverage,
        peak_levels={"G1": np.array([0.0, 1.0, 3.0, 5.0])},
    )


def _frame(coverage=0.3):
    return EventFrame(
        event_ids=("E0", "E1", "E2", "E3"),
        storms_per_event=(1, 1, 1, 1),
        categories=("minimal", "moderate", "severe", "extreme"),
        weights=_weights(),
        coverage=coverage,
        event_of={"S0": "E0", "S1a": "E1", "S1b": "E1", "S2": "E2", "S3": "E3"},
    )


# --------------------------------------------------------- gauge peak losses

def test_peak_losses_apply_the_callers_curve():
    losses = peak_level_losses(_catalogue(), "G1", lambda lvl: lvl * 100.0)
    assert list(losses) == [0.0, 100.0, 300.0, 500.0]


def test_an_unknown_gauge_yields_zero_losses():
    losses = peak_level_losses(_catalogue(), "NOPE", lambda lvl: lvl * 100.0)
    assert list(losses) == [0.0, 0.0, 0.0, 0.0]


def test_a_negative_loss_is_clamped_to_zero():
    """A curve that dips below zero cannot manufacture a gain."""
    losses = peak_level_losses(_catalogue(), "G1", lambda lvl: lvl - 2.0)
    assert list(losses) == [0.0, 0.0, 1.0, 3.0]


# ------------------------------------------------------- asset regrouping

def test_records_regroup_onto_events_by_maximum():
    frame = _frame()
    losses = regrouped_event_losses(frame, ["S1a", "S1b", "S3"], [200.0, 500.0, 900.0])
    # E1 takes the worse of its two member storms; E3 takes S3; others zero.
    assert list(losses) == [0.0, 500.0, 0.0, 900.0]


def test_event_identifiers_are_accepted_directly():
    frame = _frame()
    losses = regrouped_event_losses(frame, ["E2"], [42.0])
    assert list(losses) == [0.0, 0.0, 42.0, 0.0]


def test_mismatched_lengths_are_rejected():
    with pytest.raises(ValueError):
        regrouped_event_losses(_frame(), ["S0", "S1a"], [1.0])


def test_an_unresolved_identifier_is_refused():
    """The strictness that stops a record from another storm set contributing a
    plausible but meaningless loss."""
    with pytest.raises(ValueError):
        regrouped_event_losses(_frame(), ["S0", "GHOST"], [1.0, 2.0])


# --------------------------------------------------- coverage scaling / metrics

def test_average_annual_loss_matches_the_coverage_scaled_closed_form(config):
    """The adapter must apply the coverage scaling exactly once. The closed form
    is ``lambda * coverage * weighted-mean-loss``; a wiring that fed the raw
    lambda to the sampler would land at ``1/coverage`` times this."""
    cat = _catalogue(coverage=0.3)
    losses = peak_level_losses(cat, "G1", lambda lvl: lvl * 100.0)
    metrics = loss_metrics(
        cat, losses, 4.5, config, "G1", "thames", "generator_derived", _PERIODS)

    expected = 4.5 * 0.3 * float(np.dot(cat.weights, losses))
    assert metrics["average_annual_loss"] == pytest.approx(expected, rel=0.02)
    assert metrics["reconciliation"]["within_tolerance"]


def test_metrics_carry_the_curves_and_an_attributed_elt(config):
    cat = _catalogue()
    losses = peak_level_losses(cat, "G1", lambda lvl: lvl * 100.0)
    metrics = loss_metrics(
        cat, losses, 4.5, config, "G1", "thames", "generator_derived", _PERIODS,
        config_hash="cfg123")

    assert set(metrics["aep"]) == set(_PERIODS)
    assert set(metrics["oep"]) == set(_PERIODS)
    elt = metrics["elt"]
    assert elt["metadata"]["subject_id"] == "G1"
    assert elt["metadata"]["config_hash"] == "cfg123"
    assert elt["metadata"]["provenance_class"] == "generator_derived"
    assert sum(row["Rate"] for row in elt["events"]) == pytest.approx(4.5 * 0.3)


def test_the_frame_path_reconciles_too(config):
    """Asset subjects price off a frame, not a catalogue; the assembly must work
    against either."""
    frame = _frame()
    losses = regrouped_event_losses(frame, ["S1a", "S3"], [500.0, 900.0])
    metrics = loss_metrics(
        frame, losses, 4.5, config, "PROP-1", "thames", "generator_derived",
        _PERIODS)
    assert metrics["reconciliation"]["within_tolerance"]


def test_shared_draws_drive_the_metrics_and_correlate_subjects(config):
    """Draw once at the coverage-scaled rate, apply to each subject; the two
    gauges are then correlated through the events they share."""
    cat = _catalogue()
    draws = shared_draws(cat, 4.5, config)
    # The draws are at the effective rate, not the raw one.
    assert draws.events_per_year.mean() == pytest.approx(4.5 * 0.3, rel=0.05)

    losses_a = peak_level_losses(cat, "G1", lambda lvl: lvl * 100.0)
    metrics = loss_metrics(
        cat, losses_a, 4.5, config, "G1", "thames", "generator_derived",
        _PERIODS, draws=draws)
    assert metrics["reconciliation"]["within_tolerance"]


def test_an_empty_frame_yields_zero_metrics(config):
    empty = EventFrame(
        event_ids=(), storms_per_event=(), categories=(),
        weights=np.array([]), coverage=0.3, event_of={})
    metrics = loss_metrics(
        empty, np.array([]), 4.5, config, "PROP-0", "thames",
        "generator_derived", _PERIODS)
    assert metrics["average_annual_loss"] == 0.0
    assert metrics["aep"] == {rp: 0.0 for rp in _PERIODS}
