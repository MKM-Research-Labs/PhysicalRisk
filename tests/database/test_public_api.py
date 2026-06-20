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

"""Public-API tests — run against BOTH backends, exercising every domain module."""

import pytest

import database
from database.file_repo import FileRepository
from database.memory_repo import InMemoryRepository

CATCH = "thames"


@pytest.fixture(params=["file", "memory"])
def repo(request, tmp_path):
    """Configure the package backend and hand back the raw repo for direct setup."""
    r = FileRepository(tmp_path) if request.param == "file" else InMemoryRepository()
    database.configure_backend(r)
    yield r
    database.configure_backend(None)


def test_requires_configured_backend():
    database.configure_backend(None)
    with pytest.raises(RuntimeError, match="not configured"):
        database.list_gauges(CATCH)


def test_meta(repo):
    database.save_gauges(CATCH, [])
    assert database.ping() is True
    assert database.catchments() == [CATCH]


def test_portfolio_entities(repo):
    database.save_properties(CATCH, [{"id": "PROP-1", "address": "1 Mill Lane"},
                                     {"id": "PROP-2", "address": "2 River View"}])
    database.save_gauges(CATCH, [{"gauge_id": "GAUGE-1"}])
    database.save_loans(CATCH, [{"loan_id": "RLOAN-1"}])
    database.save_commercial(CATCH, [{"asset_id": "CPROP-1"}])
    database.save_commercial_loans(CATCH, [{"loan_id": "CLOAN-1"}])
    database.save_counterparties(CATCH, [{"counterparty_id": "CTPY-1"}])

    assert database.get_property(CATCH, "PROP-2")["address"] == "2 River View"
    assert database.get_property(CATCH, "PROP-404") is None
    assert len(database.list_properties(CATCH)) == 2
    assert database.get_gauge(CATCH, "GAUGE-1")["gauge_id"] == "GAUGE-1"
    assert database.get_loan(CATCH, "RLOAN-1")
    assert database.get_commercial(CATCH, "CPROP-1")
    assert database.get_commercial_loan(CATCH, "CLOAN-1")
    assert database.get_commercial_portfolio(CATCH) is not None  # raw doc present
    assert database.get_commercial_portfolio("nocatch") is None   # absent -> None
    assert database.get_gauge_portfolio(CATCH) is not None
    assert database.get_property_portfolio(CATCH) is not None
    assert database.get_loan_portfolio(CATCH) is not None
    assert database.get_commercial_loan_portfolio(CATCH) is not None
    assert database.get_commercial_loan_portfolio("nocatch") is None
    assert database.get_property_portfolio("nocatch") is None
    assert database.get_counterparty(CATCH, "CTPY-1")
    assert database.list_loans(CATCH) and database.list_commercial(CATCH)
    assert database.list_commercial_loans(CATCH) and database.list_counterparties(CATCH)


def test_entity_lookup_handles_wrapped_document(repo):
    # portfolios stored as {"gauges": [...]} resolve the same as a bare list
    repo.save("gauge", CATCH, {"gauges": [{"gauge_id": "GAUGE-7"}]})
    assert database.get_gauge(CATCH, "GAUGE-7") == {"gauge_id": "GAUGE-7"}


def test_absent_data_returns_none_or_empty(repo):
    assert database.get_gauge_hazard_curves(CATCH) is None
    assert database.list_gauges(CATCH) == []
    assert database.get_property(CATCH, "PROP-1") is None
    assert database.list_prs_trades(CATCH) == []
    assert database.get_market_state(CATCH) is None
    assert database.get_fire_results(CATCH) is None


def test_hazard_curves_all_modes(repo):
    database.save_gauge_hazard_curves(CATCH, {"curves": 1})
    assert database.get_gauge_hazard_curves(CATCH) == {"curves": 1}
    for mode in ("flood", "shd", "she", "bri", "win", "faw", "fow", "bow", "baw"):
        database.save_property_hazard_curves(CATCH, {"m": mode}, mode=mode)
        database.save_commercial_hazard_curves(CATCH, {"m": mode}, mode=mode)
        assert database.get_property_hazard_curves(CATCH, mode)["m"] == mode
        assert database.get_commercial_hazard_curves(CATCH, mode)["m"] == mode


def test_timeseries(repo):
    database.save_property_timeseries(CATCH, "PROP-1", {"mode": "flood"})
    database.save_property_timeseries(CATCH, "PROP-1", {"mode": "she"}, mode="she")
    database.save_commercial_timeseries(CATCH, "CPROP-1", {"x": 1})
    database.save_gauge_timeseries(CATCH, "GAUGE-1", {"y": 2})
    database.save_gauge_history(CATCH, "GAUGE-1", {"z": 3})
    database.save_property_timeseries(CATCH, "_summary_unused", {"_": 0})  # not a summary

    assert database.get_property_timeseries(CATCH, "PROP-1")["mode"] == "flood"
    assert database.get_property_timeseries(CATCH, "PROP-1", mode="she")["mode"] == "she"
    assert "PROP-1" in list(database.iter_property_timeseries_ids(CATCH))
    assert database.property_timeseries_exists(CATCH) is True
    assert database.property_timeseries_exists("nocatch") is False
    assert database.get_commercial_timeseries(CATCH, "CPROP-1") == {"x": 1}
    assert list(database.iter_commercial_timeseries_ids(CATCH)) == ["CPROP-1"]
    assert database.commercial_timeseries_exists(CATCH) is True
    assert database.commercial_timeseries_exists("nocatch") is False
    assert database.get_gauge_timeseries(CATCH, "GAUGE-1") == {"y": 2}
    assert list(database.iter_gauge_timeseries_ids(CATCH)) == ["GAUGE-1"]
    assert database.gauge_timeseries_exists(CATCH) is True
    assert database.gauge_timeseries_exists("nocatch") is False
    assert database.get_gauge_history(CATCH, "GAUGE-1") == {"z": 3}
    assert list(database.iter_gauge_history_ids(CATCH)) == ["GAUGE-1"]
    assert database.get_portfolio_flood_summary(CATCH) is None


def test_storms_and_perils(repo):
    database.save_storm_sequences(CATCH, {"sequences": []})
    database.save_stress_storm(CATCH, "STORM-A", {"severity": "severe"})
    repo.save("stress_storm_index", CATCH, {"storms": [{"id": "STORM-A"}]})
    database.save_sequence_gauge(CATCH, "GAUGE-1", {"count": 5})
    database.save_fire_results(CATCH, {"assets": []})
    database.save_seismic_results(CATCH, {"assets": []})

    assert database.get_storm_sequences(CATCH) == {"sequences": []}
    assert database.storm_sequences_exists(CATCH) is True
    assert database.storm_sequences_exists("nocatch") is False
    assert database.get_stress_storm(CATCH, "STORM-A")["severity"] == "severe"
    assert database.list_stress_storms(CATCH) == [{"id": "STORM-A"}]
    assert database.get_stress_storm_index(CATCH) == {"storms": [{"id": "STORM-A"}]}
    assert database.list_sequence_gauges(CATCH) == ["GAUGE-1"]
    assert database.get_sequence_gauge(CATCH, "GAUGE-1") == {"count": 5}
    assert database.get_fire_results(CATCH) == {"assets": []}
    assert database.get_seismic_results(CATCH) == {"assets": []}


def test_typhoon_events(repo):
    assert database.typhoon_events_exist(CATCH) is False
    assert database.get_typhoon_event(CATCH, "EVT-1") is None

    database.save_typhoon_event(CATCH, "EVT-1", {"event_id": "EVT-1", "damages": []})
    assert database.typhoon_events_exist(CATCH) is True
    assert database.get_typhoon_event(CATCH, "EVT-1")["event_id"] == "EVT-1"
    assert list(database.iter_typhoon_event_ids(CATCH)) == ["EVT-1"]


def test_legacy_storm_fallbacks(repo):
    """The pre-shard single-file artifacts resolve via their own getters and
    return None when absent (so a route can fall through to the modern layout)."""
    assert database.get_legacy_stress_storms(CATCH) is None
    assert database.get_legacy_storm_sequences(CATCH) is None

    repo.save("stress_storms_legacy", CATCH, {"storms": [{"storm_id": "OLD-1"}]})
    repo.save("storm_sequences_legacy", CATCH, {"storms": [{"storm_id": "OLD-1"}]})

    assert database.get_legacy_stress_storms(CATCH) == {"storms": [{"storm_id": "OLD-1"}]}
    assert database.get_legacy_storm_sequences(CATCH) == {"storms": [{"storm_id": "OLD-1"}]}


def test_trading_lifecycle(repo):
    database.commit_prs_trade(CATCH, {"swap_id": "PRS-1", "notional": 5_000_000})
    database.commit_prs_trade(CATCH, {"swap_id": "PRS-2", "notional": 250_000})
    assert database.get_prs_trade(CATCH, "PRS-1")["notional"] == 5_000_000
    assert sorted(t["swap_id"] for t in database.list_prs_trades(CATCH)) == ["PRS-1", "PRS-2"]
    assert sorted(database.iter_prs_trade_ids(CATCH)) == ["PRS-1", "PRS-2"]

    # save_prs_trade rewrites under an explicit key (record need not carry swap_id)
    database.save_prs_trade(CATCH, "PRS-1", {"swap_id": "PRS-1", "closed": True})
    assert database.get_prs_trade(CATCH, "PRS-1")["closed"] is True

    database.set_trade_status(CATCH, "PRS-1", "Closed")
    assert database.get_trade_marks(CATCH)["PRS-1"] == {"trade_status": "Closed"}

    database.save_market_state(CATCH, {"bid": 1})
    assert database.get_market_state(CATCH) == {"bid": 1}

    database.save_eod_snapshot(CATCH, "2026-01-15", {"pnl": 42})
    assert database.get_eod_snapshot(CATCH, "2026-01-15")["pnl"] == 42
    assert list(database.list_eod_snapshots(CATCH)) == ["EOD-20260115"]
    assert database.iter_eod_snapshots(CATCH) == [{"pnl": 42}]


def test_classifiers(repo):
    database.save_classifier(CATCH, "GAUGE-1", b"\x00MODEL\x01")
    assert database.get_classifier(CATCH, "GAUGE-1") == b"\x00MODEL\x01"
    assert database.list_classifier_ids(CATCH) == ["GAUGE-1"]


def test_classifier_training_metadata(repo):
    # training summary document
    assert database.get_classifier_training_summary(CATCH) is None
    database.save_classifier_training_summary(CATCH, {"gauges": [{"gauge_id": "GAUGE-1"}]})
    assert database.get_classifier_training_summary(CATCH)["gauges"][0]["gauge_id"] == "GAUGE-1"
    database.delete_classifier_training_summary(CATCH)
    assert database.get_classifier_training_summary(CATCH) is None

    # timings document
    assert database.get_classifier_timings(CATCH) is None
    database.save_classifier_timings(CATCH, {"runs": [{"num_gauges": 3}]})
    assert database.get_classifier_timings(CATCH) == {"runs": [{"num_gauges": 3}]}
    database.delete_classifier_timings(CATCH)
    assert database.get_classifier_timings(CATCH) is None
    database.delete_classifier(CATCH, "GAUGE-1")
    assert database.get_classifier(CATCH, "GAUGE-1") is None
