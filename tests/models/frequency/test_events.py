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

"""Tests for event aggregation and the event catalogue (MKM-EF-001).

The platform routes each storm through the gauge response model individually
and then counts storms. A sequence of one to five storms inside the 168-hour
hours clause is a single *event*, and an event is what arrives at a rate.
These tests fix that regrouping, and the fact that it leaves the underlying
physics alone.
"""

import numpy as np
import pytest

from models.frequency.datastructures import EventCatalogue
from models.frequency.events import build_catalogue, event_order, storm_to_event
from models.hazard.io import count_events, event_id, load_storms_from_sequences


class _Response:
    """The two fields of a GaugeResponse that aggregation reads."""

    def __init__(self, storm_id, peak_level_m):
        self.storm_id = storm_id
        self.peak_level_m = peak_level_m


def _sequences(sizes):
    """A sequences document with the given number of storms per sequence."""
    return {
        "sequences": [
            {
                "sequence_id": f"SEQ-{i:03d}",
                "storms": [
                    {
                        "storm_id": f"ST-{i:03d}-{j}",
                        "precipitation_mm": 10.0 + j,
                        "duration_hours": 12,
                        "intensity_factor": 1.0,
                        "peak_position": 0.5,
                    }
                    for j in range(size)
                ],
            }
            for i, size in enumerate(sizes)
        ]
    }


def _responses(storms, gauge_id="G1", scale=0.1):
    """Gauge responses whose level rises with each storm's precipitation."""
    return {
        gauge_id: [
            _Response(s["storm_id"], s["effective_precipitation_mm"] * scale)
            for s in storms
        ]
    }


# ------------------------------------------------------------ loader tagging

def test_loader_tags_every_storm_with_its_event():
    storms = load_storms_from_sequences(_sequences([2, 3]))
    assert [s["sequence_id"] for s in storms] == (
        ["SEQ-000"] * 2 + ["SEQ-001"] * 3)


def test_loader_keeps_the_existing_storm_fields():
    """The tag is added, not substituted, so existing consumers are unaffected."""
    storms = load_storms_from_sequences(_sequences([1]))
    assert set(storms[0]) >= {
        "storm_id", "effective_precipitation_mm", "duration_hours",
        "intensity_factor", "intensity_category", "peak_position",
    }


def test_an_untagged_sequence_gets_a_positional_identity():
    """Two untagged sequences must not merge into one event."""
    document = {"sequences": [
        {"storms": [{"storm_id": "A", "precipitation_mm": 1.0,
                     "duration_hours": 1, "intensity_factor": 1.0}]},
        {"storms": [{"storm_id": "B", "precipitation_mm": 1.0,
                     "duration_hours": 1, "intensity_factor": 1.0}]},
    ]}
    storms = load_storms_from_sequences(document)
    assert count_events(storms) == 2


def test_event_id_falls_back_to_the_storm_itself():
    """An untagged storm degrades to one event per storm, which is the
    platform's behaviour before events existed — not a single merged event."""
    assert event_id({"storm_id": "ST-1"}) == "ST-1"
    assert event_id({"storm_id": "ST-1", "sequence_id": None}) == "ST-1"
    assert event_id({"storm_id": "ST-1", "sequence_id": "SEQ-9"}) == "SEQ-9"


def test_count_events_collapses_sequences():
    storms = load_storms_from_sequences(_sequences([1, 2, 5, 3]))
    assert len(storms) == 11
    assert count_events(storms) == 4


def test_count_events_of_an_empty_catalogue_is_zero():
    assert count_events([]) == 0


# --------------------------------------------------------------- event order

def test_event_order_preserves_first_appearance():
    storms = load_storms_from_sequences(_sequences([2, 1, 3]))
    assert event_order(storms) == ["SEQ-000", "SEQ-001", "SEQ-002"]


def test_event_order_is_stable_across_rebuilds():
    """A catalogue built twice from one input must be identical, or a
    persisted rate could not be reproduced."""
    storms = load_storms_from_sequences(_sequences([2, 1, 3]))
    assert event_order(storms) == event_order(storms)


def test_storm_to_event_maps_every_storm():
    storms = load_storms_from_sequences(_sequences([2, 3]))
    mapping = storm_to_event(storms)
    assert len(mapping) == len(storms)
    assert set(mapping.values()) == {"SEQ-000", "SEQ-001"}


# ----------------------------------------------------------------- catalogue

def test_catalogue_has_one_row_per_event():
    storms = load_storms_from_sequences(_sequences([1, 2, 5]))
    catalogue = build_catalogue(_responses(storms), storms)

    assert catalogue.n_events == 3
    assert catalogue.n_storms == 8
    assert catalogue.storms_per_event == (1, 2, 5)


def test_an_event_takes_the_highest_level_of_its_storms():
    """A PRS pays on the level being breached, and a week containing two
    breaches is one breach of the contract, not two."""
    storms = load_storms_from_sequences(_sequences([3]))
    responses = {"G1": [
        _Response(storms[0]["storm_id"], 1.0),
        _Response(storms[1]["storm_id"], 2.5),
        _Response(storms[2]["storm_id"], 1.8),
    ]}
    catalogue = build_catalogue(responses, storms)
    assert catalogue.peak_levels["G1"][0] == 2.5


def test_grouping_is_by_storm_identity_not_position():
    """Position and identity coincide today, but grouping by position would
    break silently if response ordering ever changed."""
    storms = load_storms_from_sequences(_sequences([2, 2]))
    shuffled = {"G1": [
        _Response(storms[3]["storm_id"], 4.0),
        _Response(storms[1]["storm_id"], 2.0),
        _Response(storms[0]["storm_id"], 1.0),
        _Response(storms[2]["storm_id"], 3.0),
    ]}
    catalogue = build_catalogue(shuffled, storms)
    assert list(catalogue.peak_levels["G1"]) == [2.0, 4.0]


def test_a_response_for_an_unknown_storm_is_skipped():
    storms = load_storms_from_sequences(_sequences([1]))
    responses = {"G1": [
        _Response(storms[0]["storm_id"], 2.0),
        _Response("ST-NOT-IN-CATALOGUE", 99.0),
    ]}
    catalogue = build_catalogue(responses, storms)
    assert catalogue.peak_levels["G1"][0] == 2.0


def test_a_gauge_with_no_responses_is_flat():
    storms = load_storms_from_sequences(_sequences([1, 1]))
    catalogue = build_catalogue({"G1": []}, storms)
    assert list(catalogue.peak_levels["G1"]) == [0.0, 0.0]


def test_missing_responses_fall_to_the_gauge_floor_not_to_zero():
    """A gauge on a negative datum would read a missing response as a flood if
    the gap were filled with zero."""
    storms = load_storms_from_sequences(_sequences([1, 1]))
    responses = {"G1": [_Response(storms[0]["storm_id"], -3.0)]}
    catalogue = build_catalogue(responses, storms)
    assert list(catalogue.peak_levels["G1"]) == [-3.0, -3.0]


def test_catalogue_covers_every_gauge():
    storms = load_storms_from_sequences(_sequences([2]))
    responses = _responses(storms, "G1")
    responses.update(_responses(storms, "G2", scale=0.2))
    catalogue = build_catalogue(responses, storms)
    assert catalogue.gauge_ids == ("G1", "G2")


# ----------------------------------------------------- flags and conditionals

def test_flood_flags_are_per_event():
    storms = load_storms_from_sequences(_sequences([2, 2]))
    responses = {"G1": [
        _Response(storms[0]["storm_id"], 1.0),
        _Response(storms[1]["storm_id"], 3.0),
        _Response(storms[2]["storm_id"], 1.0),
        _Response(storms[3]["storm_id"], 1.0),
    ]}
    catalogue = build_catalogue(responses, storms)
    assert list(catalogue.flood_flags("G1", 2.0)) == [True, False]


def test_the_threshold_is_inclusive():
    storms = load_storms_from_sequences(_sequences([1]))
    catalogue = build_catalogue(
        {"G1": [_Response(storms[0]["storm_id"], 2.0)]}, storms)
    assert catalogue.flood_flags("G1", 2.0)[0]


def test_an_unknown_gauge_never_floods_rather_than_raising():
    storms = load_storms_from_sequences(_sequences([2]))
    catalogue = build_catalogue(_responses(storms), storms)
    assert not catalogue.flood_flags("NOT-A-GAUGE", 0.0).any()
    assert catalogue.conditional_probability("NOT-A-GAUGE", 0.0) == 0.0


def test_conditional_probability_is_the_flagged_fraction():
    storms = load_storms_from_sequences(_sequences([1, 1, 1, 1]))
    responses = {"G1": [
        _Response(s["storm_id"], level)
        for s, level in zip(storms, [3.0, 3.0, 1.0, 1.0])
    ]}
    catalogue = build_catalogue(responses, storms)
    assert catalogue.conditional_probability("G1", 2.0) == pytest.approx(0.5)


def test_an_empty_catalogue_has_no_conditional():
    catalogue = EventCatalogue(
        event_ids=(), storms_per_event=(), categories=(),
        weights=np.zeros(0, dtype=float),
        peak_levels={"G1": np.zeros(0, dtype=float)})
    assert catalogue.n_events == 0
    assert catalogue.n_storms == 0
    assert catalogue.conditional_probability("G1", 1.0) == 0.0


def test_the_event_conditional_differs_from_the_storm_conditional():
    """The denominator change on its own moves the number, before any arrival
    rate is applied. Taking the maximum within an event loses less from the
    numerator than the regrouping takes from the denominator, so the event
    conditional here sits above the storm one — which is why the two effects
    are staged separately rather than landing together."""
    storms = load_storms_from_sequences(_sequences([1, 1, 2, 3, 1, 2, 5, 1, 4, 2]))
    catalogue = build_catalogue(_responses(storms), storms)

    threshold = 1.2
    event_conditional = catalogue.conditional_probability("G1", threshold)
    storm_conditional = sum(
        1 for s in storms if s["effective_precipitation_mm"] * 0.1 >= threshold
    ) / len(storms)

    assert catalogue.n_events == 10
    assert catalogue.n_storms == 22
    assert event_conditional > storm_conditional
