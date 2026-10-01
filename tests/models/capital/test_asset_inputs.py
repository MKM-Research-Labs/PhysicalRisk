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

"""Building one asset's case from the platform's records."""

import numpy as np
import pytest

import database
from models.capital import asset_inputs
from models.capital.asset_inputs import build_asset_case, load_asset_case, reference_gauge

from ._asset_fixtures import (
    ASSET,
    ASSET_ID,
    LOAN,
    REFERENCE_RESPONSES,
    SEQUENCES,
    TIMESERIES,
)


@pytest.fixture
def case():
    return build_asset_case(ASSET, LOAN, TIMESERIES, SEQUENCES,
                            REFERENCE_RESPONSES, 4.5, "thames")


def test_events_follow_the_catalogue(case):
    assert case.event_ids == ("EVT-A", "EVT-B", "EVT-C")
    assert case.event_weights.sum() == pytest.approx(1.0)
    assert 0.0 < case.event_coverage <= 1.0
    assert case.lambda_per_year == 4.5


def test_depth_and_damage_are_read_per_event(case):
    """Flood series events are keyed by event id; absent events did not flood."""
    assert list(case.flood_depth_m) == [0.8, 0.0, 0.0]
    assert list(case.damage_ratio) == [0.35, 0.0, 0.0]


def test_trigger_is_any_member_storm_passing_severe(case):
    """EVT-A triggers through its second storm; EVT-C triggers with no flood."""
    assert list(case.triggered) == [True, False, True]


def test_gauges_controlling_and_reference(case):
    assert case.controlling_gauge_id == "SYNTH-0001"
    assert case.reference_gauge_id == "GAUGE-0002"


def test_finances(case):
    assert case.property_value == 10_000_000.0
    assert case.annual_rent == pytest.approx(600_000.0)
    assert case.remaining_term_years == 5.0
    assert case.amortising_share == 0.0
    assert case.annual_debt_service == pytest.approx(300_000.0)


def test_amortising_loan_adds_principal():
    loan = {"Mortgage": {**LOAN["Mortgage"], "Features": {"RepaymentType": "Repayment"}}}
    case = build_asset_case(ASSET, loan, TIMESERIES, SEQUENCES, [], 4.5, "thames")
    assert case.amortising_share == 1.0
    assert case.annual_debt_service == pytest.approx(300_000.0 + 6_000_000.0 / 5.0)


def test_unknown_repayment_type_is_interest_only():
    loan = {"Mortgage": {**LOAN["Mortgage"], "Features": {"RepaymentType": "Balloon"}}}
    case = build_asset_case(ASSET, loan, TIMESERIES, SEQUENCES, [], 4.5, "thames")
    assert case.amortising_share == 0.0


def test_unknown_event_ids_are_ignored():
    ts = {**TIMESERIES, "flood_events": [{"storm_id": "EVT-ZZZ", "flood_depth_m": 1.0,
                                          "damage_ratio": 0.5}]}
    responses = [{"storm_id": "S-ZZZ", "exceeded_severe": True}]
    case = build_asset_case(ASSET, LOAN, ts, SEQUENCES, responses, 4.5, "thames")
    assert not case.damage_ratio.any() and not case.triggered.any()


def test_flood_series_may_name_storms_instead_of_events():
    ts = {**TIMESERIES, "flood_events": [{"storm_id": "S-A1", "flood_depth_m": 0.4,
                                          "damage_ratio": 0.2}]}
    case = build_asset_case(ASSET, LOAN, ts, SEQUENCES, [], 4.5, "thames")
    assert case.damage_ratio[0] == 0.2


def test_reference_gauge_skips_synthetic_gauges():
    assert reference_gauge([{"gauge_id": "SYNTH-1"}, {"gauge_id": "GAUGE-9"}]) == "GAUGE-9"


def test_reference_gauge_required():
    with pytest.raises(ValueError, match="no real gauge"):
        reference_gauge([{"gauge_id": "SYNTH-1"}])


def test_case_without_nearest_gauges_has_no_controlling_gauge():
    ts = {**TIMESERIES, "nearest_gauges": []}
    with pytest.raises(ValueError):
        build_asset_case(ASSET, LOAN, ts, SEQUENCES, [], 4.5, "thames")


class TestLoadThroughDatabase:
    @pytest.fixture
    def seeded(self, monkeypatch):
        monkeypatch.setattr(database, "list_commercial", lambda c: [ASSET])
        monkeypatch.setattr(database, "list_commercial_loans", lambda c: [LOAN])
        monkeypatch.setattr(database, "get_commercial_timeseries",
                            lambda c, a, mode: TIMESERIES)
        monkeypatch.setattr(database, "get_gauge_timeseries", lambda c, g: {
            "storm_responses": {"responses": REFERENCE_RESPONSES}})
        monkeypatch.setattr(database, "get_storm_sequences", lambda c: SEQUENCES)
        monkeypatch.setattr(asset_inputs, "catchment_lambda", lambda c: 4.5)

    def test_loads_the_asset_from_nested_records(self, seeded):
        case = load_asset_case("thames", ASSET_ID)
        assert case.asset_id == ASSET_ID
        assert list(case.triggered) == [True, False, True]

    def test_unknown_asset(self, seeded):
        with pytest.raises(ValueError, match="no commercial asset CPROP-nope"):
            load_asset_case("thames", "CPROP-nope")

    def test_missing_flood_series(self, seeded, monkeypatch):
        monkeypatch.setattr(database, "get_commercial_timeseries", lambda c, a, mode: None)
        with pytest.raises(ValueError, match="no flood series"):
            load_asset_case("thames", ASSET_ID)

    def test_reference_gauge_without_responses_never_triggers(self, seeded, monkeypatch):
        monkeypatch.setattr(database, "get_gauge_timeseries", lambda c, g: None)
        assert not load_asset_case("thames", ASSET_ID).triggered.any()
