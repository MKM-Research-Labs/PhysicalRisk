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

"""Tests for the event frame (MKM-EF-001).

The frame turns a subject's own per-record flood outcomes into a per-event
conditional. It exists because the property and commercial legs price off
per-asset flood series rather than gauge levels, so they need the hours-clause
grouping without needing anyone's peak levels.

The identifier handling is the delicate part: the property flood series names
its field ``storm_id`` but stores *sequence* identifiers, so the frame accepts
either and — critically — refuses to guess when it recognises neither.
"""

import numpy as np
import pytest

from models.frequency import build_event_frame
from models.hazard.io import load_storms_from_sequences


def _sequences(sizes, category="severe"):
    return {"sequences": [
        {
            "sequence_id": f"SEQ-{i:03d}",
            "storms": [{
                "storm_id": f"ST-{i:03d}-{j}",
                "precipitation_mm": 20.0,
                "duration_hours": 12,
                "intensity_factor": 1.0,
                "peak_position": 0.5,
                "intensity_category": category,
            } for j in range(size)],
        }
        for i, size in enumerate(sizes)
    ]}


def _frame(sizes, category="severe"):
    return build_event_frame(load_storms_from_sequences(_sequences(sizes, category)))


# ------------------------------------------------------------------- structure

def test_frame_counts_events_and_storms():
    frame = _frame([1, 2, 5])
    assert frame.n_events == 3
    assert frame.n_storms == 8
    assert frame.storms_per_event == (1, 2, 5)


def test_frame_maps_every_storm_to_its_event():
    frame = _frame([2, 3])
    assert frame.event_of["ST-000-0"] == "SEQ-000"
    assert frame.event_of["ST-001-2"] == "SEQ-001"


def test_frame_weights_and_coverage_are_populated():
    frame = _frame([1, 1, 1])
    assert frame.weights.sum() == pytest.approx(1.0)
    assert 0.0 < frame.coverage <= 1.0


# ------------------------------------------------------ identifier resolution

def test_storm_identifiers_resolve_to_their_event():
    frame = _frame([3])
    hit, unresolved = frame.resolve(["ST-000-0", "ST-000-2"])
    assert hit == {"SEQ-000"}
    assert unresolved == 0


def test_event_identifiers_resolve_to_themselves():
    """The property flood series stores sequence identifiers in a field named
    ``storm_id``; the frame must accept them as they are."""
    frame = _frame([3])
    hit, unresolved = frame.resolve(["SEQ-000"])
    assert hit == {"SEQ-000"}
    assert unresolved == 0


def test_the_two_forms_agree():
    frame = _frame([2, 2])
    by_storm = frame.event_flags(["ST-000-0", "ST-001-1"])
    by_event = frame.event_flags(["SEQ-000", "SEQ-001"])
    assert np.array_equal(by_storm, by_event)


def test_unknown_identifiers_are_counted_not_dropped():
    frame = _frame([2])
    hit, unresolved = frame.resolve(["ST-000-0", "ST-999-9", "nonsense"])
    assert hit == {"SEQ-000"}
    assert unresolved == 2


def test_a_conditional_from_foreign_records_refuses_to_answer():
    """The regression for a silent zero.

    An earlier version dropped unrecognised identifiers, so a property whose
    records came from a different storm generation returned a confident 0.0
    from 110 genuine flood events. Records that do not correspond to this
    catalogue must fail loudly rather than price at zero."""
    frame = _frame([2, 2])
    with pytest.raises(ValueError, match="different storm sets"):
        frame.conditional_probability(["STORM-from-another-run"])


def test_the_error_reports_how_many_failed():
    frame = _frame([2])
    with pytest.raises(ValueError, match="2 of 3"):
        frame.conditional_probability(["ST-000-0", "foreign-a", "foreign-b"])


# ------------------------------------------------------------ the conditional

def test_several_storms_in_one_event_count_once():
    """A week containing two breaches is one breach of the contract."""
    frame = _frame([3])
    assert frame.event_flags(["ST-000-0", "ST-000-1", "ST-000-2"]).sum() == 1


def test_conditional_is_the_weighted_share_scaled_by_coverage():
    frame = _frame([1, 1, 1, 1])
    conditional = frame.conditional_probability(["SEQ-000", "SEQ-001"])
    within = float(np.dot(frame.event_flags(["SEQ-000", "SEQ-001"]), frame.weights))
    assert conditional == pytest.approx(within * frame.coverage)


def test_no_floods_gives_a_zero_conditional():
    assert _frame([2, 2]).conditional_probability([]) == 0.0


def test_every_event_flooding_gives_the_coverage():
    frame = _frame([1, 1, 1])
    assert frame.conditional_probability(frame.event_ids) == pytest.approx(
        frame.coverage)


def test_an_empty_frame_has_no_conditional():
    frame = build_event_frame([])
    assert frame.n_events == 0
    assert frame.conditional_probability(["anything"]) == 0.0
