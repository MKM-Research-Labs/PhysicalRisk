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

"""save→load parity for PostgresRepository (WP1.6) — live Postgres required.

Skips automatically when no Postgres is reachable. Uses a dedicated test
catchment and deletes everything it wrote on teardown, so the database is left
exactly as found.
"""

import pytest

from database._pg import (
    Catchment, Commercial, CommercialLoan, Counterparty, EodSnapshot, Gauge,
    GaugeHazardCurve, Loan, PortRun, PrsTrade, Property, get_engine, get_session,
    reset_engine,
)
from database._pg.pg_repo import PostgresRepository

TEST_CATCHMENT = "__pgtest__"
_ALL_MODELS = (Gauge, Property, Loan, Commercial, CommercialLoan, Counterparty,
               GaugeHazardCurve, PrsTrade, EodSnapshot, PortRun)


def _postgres_available() -> bool:
    try:
        reset_engine()
        from sqlalchemy import text
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        reset_engine()


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="no live Postgres (run: docker compose -f docker/docker-compose.yml up -d postgres)",
)


@pytest.fixture
def repo():
    reset_engine()
    yield PostgresRepository()
    reset_engine()  # drop any test-repointed engine (e.g. the ping-false test) first
    # Teardown: remove every row this test wrote under the test catchment.
    with get_session() as session:
        for model in _ALL_MODELS:
            session.query(model).filter_by(catchment_id=TEST_CATCHMENT).delete()
        anchor = session.get(Catchment, TEST_CATCHMENT)
        if anchor is not None:
            session.delete(anchor)
        session.commit()
    reset_engine()


def _gauge_doc():
    return {
        "flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001", "GaugeName": "A"},
                            "Location": {"GaugeLatitude": 51.5}}},
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-002", "GaugeName": "B"},
                            "Location": {"GaugeLatitude": 51.6}}},
        ],
        "generation_metadata": {"count": 2, "seed": 42},
    }


def _ghc_doc():
    return {
        "metadata": {"distribution": "gev"},
        "hazard_curves": {
            "GAUGE-001": {"gauge_id": "GAUGE-001", "gev_scale": 0.5, "curve_points": [1, 2, 3]},
            "GAUGE-002": {"gauge_id": "GAUGE-002", "gev_scale": 0.6, "curve_points": [4, 5]},
        },
    }


# ---------------------------------------------------------------------------
# Round-trip parity
# ---------------------------------------------------------------------------

def test_collection_list_roundtrip(repo):
    """A list-container document (gauge) shreds + reassembles record-for-record."""
    doc = _gauge_doc()
    repo.save("gauge", TEST_CATCHMENT, doc)
    assert repo.load("gauge", TEST_CATCHMENT) == doc


def test_collection_dict_roundtrip(repo):
    """A dict-container document (gauge_hazard_curve) round-trips its mapping."""
    doc = _ghc_doc()
    repo.save("gauge_hazard_curve", TEST_CATCHMENT, doc)
    assert repo.load("gauge_hazard_curve", TEST_CATCHMENT) == doc


def test_keyed_roundtrip(repo):
    trade = {"PhysicalSwap": {"Header": {"SwapID": "PRS-001"}, "Pricing": {"SpreadBps": 250}}}
    repo.save("prs_trade", TEST_CATCHMENT, trade, key="PRS-001")
    assert repo.load("prs_trade", TEST_CATCHMENT, "PRS-001") == trade


def test_keyed_replace_overwrites(repo):
    snap = {"date": "2026-01-01", "portfolio_summary": {"total_notional": 1_000_000}}
    repo.save("eod_snapshot", TEST_CATCHMENT, snap, key="2026-01-01")
    snap2 = {"date": "2026-01-01", "portfolio_summary": {"total_notional": 2_000_000}}
    repo.save("eod_snapshot", TEST_CATCHMENT, snap2, key="2026-01-01")
    assert repo.load("eod_snapshot", TEST_CATCHMENT, "2026-01-01") == snap2


def test_collection_replace_clears_prior_rows(repo):
    repo.save("gauge", TEST_CATCHMENT, _gauge_doc())
    smaller = {"flood_gauges": [
        {"FloodGauge": {"Header": {"GaugeID": "GAUGE-009"}}}], "generation_metadata": {}}
    repo.save("gauge", TEST_CATCHMENT, smaller)
    loaded = repo.load("gauge", TEST_CATCHMENT)
    assert [g["FloodGauge"]["Header"]["GaugeID"] for g in loaded["flood_gauges"]] == ["GAUGE-009"]


# ---------------------------------------------------------------------------
# Promoted columns populate (the relational payoff) — cdm stays exact
# ---------------------------------------------------------------------------

def test_promoted_columns_populated_collection(repo):
    doc = {"flood_gauges": [{"FloodGauge": {
        "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Westminster"},
        "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GaugeElevation": 5.0},
        "FloodStages": {"FloodAlert": 3.5, "FloodWarning": 4.6, "SevereFloodWarning": 5.5},
        "NRFAMetadata": {"NRFAStationID": "39001"},
    }}], "generation_metadata": {}}
    repo.save("gauge", TEST_CATCHMENT, doc)
    with get_session() as session:
        row = session.get(Gauge, (TEST_CATCHMENT, "GAUGE-001"))
        assert row.gauge_name == "Westminster"
        assert row.latitude == 51.5
        assert row.flood_warning == 4.6
        assert row.nrfa_station_id == "39001"
    assert repo.load("gauge", TEST_CATCHMENT) == doc  # round-trip still exact


def test_promoted_columns_populated_keyed(repo):
    trade = {"PhysicalSwap": {
        "Header": {"SwapID": "PRS-001", "CounterParty": "BANK-A", "TradeStatus": "Open"},
        "LegData": {"Notional": 10_000_000, "Currency": "GBP"},
        "Pricing": {"SpreadBps": 250.0, "NPV": 1234.5, "TriggerLevel": "warning"},
    }}
    repo.save("prs_trade", TEST_CATCHMENT, trade, key="PRS-001")
    with get_session() as session:
        row = session.get(PrsTrade, (TEST_CATCHMENT, "PRS-001"))
        assert row.counterparty == "BANK-A"
        assert row.notional == 10_000_000
        assert row.spread_bps == 250.0
        assert row.trigger_level == "warning"
    assert repo.load("prs_trade", TEST_CATCHMENT, "PRS-001") == trade


def test_keyed_update_refreshes_promoted_columns(repo):
    repo.save("prs_trade", TEST_CATCHMENT,
              {"PhysicalSwap": {"Header": {"TradeStatus": "Open"}}}, key="PRS-9")
    repo.save("prs_trade", TEST_CATCHMENT,
              {"PhysicalSwap": {"Header": {"TradeStatus": "Closed"}}}, key="PRS-9")
    with get_session() as session:
        assert session.get(PrsTrade, (TEST_CATCHMENT, "PRS-9")).trade_status == "Closed"


def test_missing_promoted_fields_are_none(repo):
    doc = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-X"}}}],
           "generation_metadata": {}}
    repo.save("gauge", TEST_CATCHMENT, doc)
    with get_session() as session:
        row = session.get(Gauge, (TEST_CATCHMENT, "GAUGE-X"))
        assert row.latitude is None
        assert row.gauge_name is None
    assert repo.load("gauge", TEST_CATCHMENT) == doc


# ---------------------------------------------------------------------------
# Interface semantics
# ---------------------------------------------------------------------------

def test_load_missing_raises_filenotfound(repo):
    with pytest.raises(FileNotFoundError):
        repo.load("gauge", TEST_CATCHMENT)
    with pytest.raises(FileNotFoundError):
        repo.load("prs_trade", TEST_CATCHMENT, "NOPE")


def test_exists_and_has_collection(repo):
    assert repo.exists("gauge", TEST_CATCHMENT) is False
    repo.save("gauge", TEST_CATCHMENT, _gauge_doc())
    assert repo.exists("gauge", TEST_CATCHMENT) is True
    assert repo.has_collection("gauge", TEST_CATCHMENT) is True
    assert repo.exists("prs_trade", TEST_CATCHMENT, "PRS-001") is False


def test_iter_keys_sorted(repo):
    for sid in ("PRS-003", "PRS-001", "PRS-002"):
        repo.save("prs_trade", TEST_CATCHMENT, {"PhysicalSwap": {"Header": {"SwapID": sid}}}, key=sid)
    assert list(repo.iter_keys("prs_trade", TEST_CATCHMENT)) == ["PRS-001", "PRS-002", "PRS-003"]


def test_delete_collection_and_keyed(repo):
    repo.save("gauge", TEST_CATCHMENT, _gauge_doc())
    repo.delete("gauge", TEST_CATCHMENT)
    assert repo.exists("gauge", TEST_CATCHMENT) is False

    repo.save("prs_trade", TEST_CATCHMENT, {"PhysicalSwap": {}}, key="PRS-X")
    repo.delete("prs_trade", TEST_CATCHMENT, "PRS-X")
    assert repo.exists("prs_trade", TEST_CATCHMENT, "PRS-X") is False
    repo.delete("prs_trade", TEST_CATCHMENT, "ALREADY-GONE")  # no-op, no raise


def test_catchments_includes_written(repo):
    repo.save("gauge", TEST_CATCHMENT, _gauge_doc())
    assert TEST_CATCHMENT in repo.catchments()


def test_unmapped_artifact_raises_everywhere(repo):
    """Every method rejects an artifact with no table yet (not a KeyError)."""
    with pytest.raises(NotImplementedError):
        repo.save("market_state", TEST_CATCHMENT, {"x": 1})
    with pytest.raises(NotImplementedError):
        repo.load("market_state", TEST_CATCHMENT)
    with pytest.raises(NotImplementedError):
        repo.delete("market_state", TEST_CATCHMENT)
    with pytest.raises(NotImplementedError):
        list(repo.iter_keys("market_state", TEST_CATCHMENT))
    with pytest.raises(NotImplementedError):
        repo.has_collection("market_state", TEST_CATCHMENT)


def test_ping(repo):
    assert repo.ping() is True


def test_ping_false_when_unreachable(repo, monkeypatch):
    monkeypatch.setenv("MKM_DATABASE_URL", "postgresql+psycopg2://x:y@127.0.0.1:1/nope")
    reset_engine()
    assert repo.ping() is False
