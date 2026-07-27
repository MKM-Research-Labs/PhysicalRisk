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

"""Tests for the event loss table and its export (MKM-EF-001, Stage 6).

Three things are pinned:

- **The rates tie the ELT to the sampler.** Each event's rate is
  ``lambda_effective * weight`` and the rates sum to ``lambda_effective``, the
  rate the loss sampler draws at, so the two describe the same event population.
- **The ELT's average annual loss is the closed form.** ``sum(rate * loss)`` is
  the exact expectation the loss simulation reconciles against, not a second
  estimate of it.
- **The export is attributed and portable.** Every row carries the standard
  catastrophe-model columns, and the document carries the model identity and
  provenance in plain JSON so it crosses the seam and a third-party tool
  unchanged.
"""

import json

import numpy as np
import pytest

from config.frequency import MODEL_ID, MODEL_VERSION
from models.frequency import build_event_loss_table, elt_document
from models.frequency.datastructures import EventCatalogue
from models.frequency.ylt import analytic_average_annual_loss

_N = 6


def _catalogue(coverage=0.3, weights=None):
    if weights is None:
        weights = np.full(_N, 1.0 / _N)
    return EventCatalogue(
        event_ids=tuple(f"EVT-{i}" for i in range(_N)),
        storms_per_event=tuple([1] * _N),
        categories=tuple(["severe"] * _N),
        weights=np.asarray(weights, dtype=float),
        coverage=coverage,
        peak_levels={},
    )


def _losses():
    return np.array([0.0, 100.0, 250.0, 40.0, 900.0, 12.0])


# ---------------------------------------------------------------- construction

def test_rates_sum_to_the_effective_lambda():
    table = build_event_loss_table(_catalogue(coverage=0.3), _losses(), 4.5, "G1")
    assert table.lambda_effective == pytest.approx(4.5 * 0.3)
    assert table.rates.sum() == pytest.approx(4.5 * 0.3)


def test_each_rate_is_lambda_effective_times_weight():
    weights = np.array([0.1, 0.1, 0.2, 0.2, 0.3, 0.1])
    table = build_event_loss_table(_catalogue(weights=weights), _losses(), 4.5, "G1")
    assert np.allclose(table.rates, 4.5 * 0.3 * weights)


def test_a_negative_lambda_is_floored_at_zero():
    table = build_event_loss_table(_catalogue(), _losses(), -1.0, "G1")
    assert table.lambda_effective == 0.0
    assert table.rates.sum() == 0.0


def test_a_misaligned_loss_vector_is_rejected():
    """Losses that do not line up with the catalogue would misattribute each
    event's loss silently; the builder refuses rather than guessing."""
    with pytest.raises(ValueError):
        build_event_loss_table(_catalogue(), np.array([1.0, 2.0]), 4.5, "G1")


# ------------------------------------------------------- closed-form agreement

def test_average_annual_loss_matches_the_analytic_form():
    cat, losses = _catalogue(coverage=0.3), _losses()
    table = build_event_loss_table(cat, losses, 4.5, "G1")
    expected = analytic_average_annual_loss(4.5 * 0.3, cat.weights, losses)
    assert table.average_annual_loss() == pytest.approx(expected)


def test_average_annual_loss_of_an_empty_table_is_zero():
    empty = EventCatalogue(
        event_ids=(), storms_per_event=(), categories=(),
        weights=np.array([]), coverage=0.3, peak_levels={})
    table = build_event_loss_table(empty, np.array([]), 4.5, "G1")
    assert table.average_annual_loss() == 0.0
    assert table.n_events == 0


# ---------------------------------------------------------------- export rows

def test_rows_carry_the_standard_columns():
    table = build_event_loss_table(_catalogue(), _losses(), 4.5, "G1")
    rows = table.rows()
    assert len(rows) == _N
    for row in rows:
        assert set(row) == {
            "EventID", "Rate", "MeanLoss", "StdDevIndependent",
            "StdDevCorrelated", "ExposureValue"}


def test_a_point_loss_has_zero_standard_deviation():
    """The loss per event is determined once the event is drawn, so both
    standard-deviation columns are zero and the exposure equals the loss."""
    table = build_event_loss_table(_catalogue(), _losses(), 4.5, "G1")
    row = table.rows()[4]
    assert row["MeanLoss"] == 900.0
    assert row["ExposureValue"] == 900.0
    assert row["StdDevIndependent"] == 0.0
    assert row["StdDevCorrelated"] == 0.0


# ---------------------------------------------------------------- document

def test_document_carries_model_identity_and_provenance():
    table = build_event_loss_table(_catalogue(), _losses(), 4.5, "G1")
    doc = elt_document(table, "thames", "generator_derived", config_hash="abc123")
    meta = doc["metadata"]
    assert meta["model_id"] == MODEL_ID
    assert meta["model_version"] == MODEL_VERSION
    assert meta["catchment"] == "thames"
    assert meta["subject_id"] == "G1"
    assert meta["provenance_class"] == "generator_derived"
    assert meta["config_hash"] == "abc123"
    assert meta["num_events"] == _N
    assert meta["average_annual_loss"] == pytest.approx(table.average_annual_loss())


def test_document_is_json_serialisable():
    table = build_event_loss_table(_catalogue(), _losses(), 4.5, "G1")
    doc = elt_document(table, "thames", "generator_derived")
    restored = json.loads(json.dumps(doc))
    assert restored["events"][0]["EventID"] == "EVT-0"
    assert restored["metadata"]["config_hash"] is None
