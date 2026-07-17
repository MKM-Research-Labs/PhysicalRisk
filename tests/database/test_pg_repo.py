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

"""save→load parity for PostgresRepository (WP1.6) — live Postgres required.

Skips automatically when no Postgres is reachable. Uses a dedicated test
catchment and deletes everything it wrote on teardown, so the database is left
exactly as found.
"""

import pytest

from database import FileRepository
from database._pg import (
    Catchment,
    Commercial,
    CommercialLoan,
    Counterparty,
    EodSnapshot,
    Gauge,
    GaugeHazardCurve,
    Loan,
    PortBlob,
    PortDocument,
    PortRecord,
    PortRun,
    Property,
    PrsTrade,
    _objectstore,
    get_engine,
    get_session,
    reset_engine,
)
from database._pg.etl import import_catchment
from database._pg.pg_repo import PostgresRepository

TEST_CATCHMENT = "__pgtest__"
_ALL_MODELS = (Gauge, Property, Loan, Commercial, CommercialLoan, Counterparty,
               GaugeHazardCurve, PrsTrade, EodSnapshot, PortDocument, PortRecord,
               PortBlob, PortRun)


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


def _minio_available() -> bool:
    _objectstore.reset_client()
    return _objectstore.reachable()


requires_minio = pytest.mark.skipif(
    not _minio_available(),
    reason="no live MinIO (run: scripts/minio-native.sh start)",
)


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="no live Postgres (run: scripts/pg-native.sh start)",
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
    # Best-effort: drop any blob objects this test left in the object store.
    if _minio_available():
        client, bucket = _objectstore.get_client()
        for obj in client.list_objects(bucket, prefix=f"{TEST_CATCHMENT}/", recursive=True):
            client.remove_object(bucket, obj.object_name)
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


def test_unknown_artifact_raises_everywhere(repo):
    """Every method rejects an artifact with no table mapping (NotImplementedError,
    not a KeyError). Every *registered* artifact is now mapped, so this uses an
    unknown name to exercise the fall-through guard."""
    unknown = "not_a_real_artifact"
    with pytest.raises(NotImplementedError):
        repo.save(unknown, TEST_CATCHMENT, {"x": 1}, key="k1")
    with pytest.raises(NotImplementedError):
        repo.load(unknown, TEST_CATCHMENT, "k1")
    with pytest.raises(NotImplementedError):
        repo.delete(unknown, TEST_CATCHMENT, "k1")
    with pytest.raises(NotImplementedError):
        list(repo.iter_keys(unknown, TEST_CATCHMENT))
    with pytest.raises(NotImplementedError):
        repo.exists(unknown, TEST_CATCHMENT, "k1")
    with pytest.raises(NotImplementedError):
        repo.has_collection(unknown, TEST_CATCHMENT)


# ---------------------------------------------------------------------------
# Blob tier — binary artifacts (PortBlob metadata row + object-store bytes)
# ---------------------------------------------------------------------------

@requires_minio
def test_blob_roundtrip(repo):
    blob = b"\x80\x03}q\x00.PK\x05\x06"  # arbitrary binary
    repo.save("classifier", TEST_CATCHMENT, blob, key="GAUGE-1")
    assert repo.load("classifier", TEST_CATCHMENT, "GAUGE-1") == blob
    with get_session() as session:
        row = session.get(PortBlob, (TEST_CATCHMENT, "classifier", "flood", "GAUGE-1"))
        assert row.object_key == f"{TEST_CATCHMENT}/classifier/flood/GAUGE-1"
        assert row.size_bytes == len(blob)


@requires_minio
def test_blob_replace_overwrites(repo):
    repo.save("classifier", TEST_CATCHMENT, b"old", key="GAUGE-1")
    repo.save("classifier", TEST_CATCHMENT, b"newer-bytes", key="GAUGE-1")
    assert repo.load("classifier", TEST_CATCHMENT, "GAUGE-1") == b"newer-bytes"
    with get_session() as session:
        assert session.get(PortBlob, (TEST_CATCHMENT, "classifier", "flood", "GAUGE-1")).size_bytes == 11


@requires_minio
def test_blob_iter_keys_exists_has_collection(repo):
    assert repo.exists("classifier", TEST_CATCHMENT, "GAUGE-1") is False
    assert repo.has_collection("classifier", TEST_CATCHMENT) is False
    repo.save("classifier", TEST_CATCHMENT, b"a", key="GAUGE-2")
    repo.save("classifier", TEST_CATCHMENT, b"b", key="GAUGE-1")
    assert repo.exists("classifier", TEST_CATCHMENT, "GAUGE-1") is True
    assert repo.has_collection("classifier", TEST_CATCHMENT) is True
    assert list(repo.iter_keys("classifier", TEST_CATCHMENT)) == ["GAUGE-1", "GAUGE-2"]


@requires_minio
def test_blob_delete_removes_row_and_object(repo):
    repo.save("classifier", TEST_CATCHMENT, b"x", key="GAUGE-1")
    repo.delete("classifier", TEST_CATCHMENT, "GAUGE-1")
    assert repo.exists("classifier", TEST_CATCHMENT, "GAUGE-1") is False
    with pytest.raises(FileNotFoundError):
        repo.load("classifier", TEST_CATCHMENT, "GAUGE-1")
    repo.delete("classifier", TEST_CATCHMENT, "GONE")  # no-op, no raise


@requires_minio
def test_blob_load_missing_raises(repo):
    with pytest.raises(FileNotFoundError):
        repo.load("classifier", TEST_CATCHMENT, "NOPE")


@requires_minio
def test_import_catchment_imports_blobs(repo, tmp_path):
    """ETL reads classifier blobs from the file backend and writes them to the
    object store; PG-load then deep-equals the file bytes."""
    files = FileRepository(dir_resolver=lambda _catchment: tmp_path)
    files.save("classifier", TEST_CATCHMENT, b"model-bytes-1", key="GAUGE-1")
    files.save("classifier", TEST_CATCHMENT, b"model-bytes-2", key="GAUGE-2")

    counts = import_catchment(TEST_CATCHMENT, file_repo=files, pg=repo)

    assert counts["classifier"] == 2
    assert list(repo.iter_keys("classifier", TEST_CATCHMENT)) == ["GAUGE-1", "GAUGE-2"]
    assert repo.load("classifier", TEST_CATCHMENT, "GAUGE-1") == \
        files.load("classifier", TEST_CATCHMENT, "GAUGE-1")


# ---------------------------------------------------------------------------
# Keyed-record tier — per-key JSON records (PortRecord), one row per
# (catchment, artifact, mode, key)
# ---------------------------------------------------------------------------

def test_record_roundtrip_mode_invariant(repo):
    repo.save("gauge_timeseries", TEST_CATCHMENT, {"series": [1, 2, 3]}, key="GAUGE-1")
    assert repo.load("gauge_timeseries", TEST_CATCHMENT, "GAUGE-1") == {"series": [1, 2, 3]}
    with get_session() as session:
        row = session.get(PortRecord, (TEST_CATCHMENT, "gauge_timeseries", "flood", "GAUGE-1"))
        assert row.cdm == {"series": [1, 2, 3]}


def test_record_iter_keys_sorted_and_mode_isolated(repo):
    repo.save("property_timeseries", TEST_CATCHMENT, {"a": 1}, key="PROP-2", mode="flood")
    repo.save("property_timeseries", TEST_CATCHMENT, {"a": 1}, key="PROP-1", mode="flood")
    repo.save("property_timeseries", TEST_CATCHMENT, {"a": 9}, key="PROP-9", mode="she")
    assert list(repo.iter_keys("property_timeseries", TEST_CATCHMENT, mode="flood")) == \
        ["PROP-1", "PROP-2"]
    assert list(repo.iter_keys("property_timeseries", TEST_CATCHMENT, mode="she")) == ["PROP-9"]


def test_record_per_mode_isolated(repo):
    repo.save("property_timeseries", TEST_CATCHMENT, {"flood": 1}, key="PROP-1", mode="flood")
    repo.save("property_timeseries", TEST_CATCHMENT, {"she": 1}, key="PROP-1", mode="she")
    assert repo.load("property_timeseries", TEST_CATCHMENT, "PROP-1", mode="she") == {"she": 1}
    assert repo.exists("property_timeseries", TEST_CATCHMENT, "PROP-1", mode="bri") is False


def test_record_replace_overwrites(repo):
    repo.save("stress_storm", TEST_CATCHMENT, {"peak": 1.0}, key="STORM-1")
    repo.save("stress_storm", TEST_CATCHMENT, {"peak": 2.0}, key="STORM-1")
    assert repo.load("stress_storm", TEST_CATCHMENT, "STORM-1") == {"peak": 2.0}


def test_record_exists_has_collection_delete(repo):
    assert repo.exists("typhoon_event", TEST_CATCHMENT, "TC-1") is False
    assert repo.has_collection("typhoon_event", TEST_CATCHMENT) is False
    repo.save("typhoon_event", TEST_CATCHMENT, {"damage": 5}, key="TC-1")
    assert repo.exists("typhoon_event", TEST_CATCHMENT, "TC-1") is True
    assert repo.has_collection("typhoon_event", TEST_CATCHMENT) is True
    repo.delete("typhoon_event", TEST_CATCHMENT, "TC-1")
    assert repo.exists("typhoon_event", TEST_CATCHMENT, "TC-1") is False
    repo.delete("typhoon_event", TEST_CATCHMENT, "GONE")  # no-op, no raise


def test_record_load_missing_raises(repo):
    with pytest.raises(FileNotFoundError):
        repo.load("gauge_timeseries", TEST_CATCHMENT, "NOPE")


# ---------------------------------------------------------------------------
# Document tier — whole-document artifacts (PortDocument), one row per
# (catchment, artifact, mode)
# ---------------------------------------------------------------------------

def test_document_roundtrip_mode_invariant(repo):
    doc = {"market": {"rates": {"GBP": 0.05}}, "as_of": "2026-06-22"}
    repo.save("market_state", TEST_CATCHMENT, doc)
    assert repo.load("market_state", TEST_CATCHMENT) == doc
    with get_session() as session:
        row = session.get(PortDocument, (TEST_CATCHMENT, "market_state", "flood"))
        assert row.cdm == doc


def test_document_roundtrip_per_mode_isolated(repo):
    """A mode-varying document keeps a separate row per scenario mode."""
    she = {"hazard_curves": {"PROP-1": {"rp": [1, 2, 3]}}}
    flood = {"hazard_curves": {"PROP-1": {"rp": [9]}}}
    repo.save("property_hazard_curve", TEST_CATCHMENT, she, mode="she")
    repo.save("property_hazard_curve", TEST_CATCHMENT, flood, mode="flood")
    assert repo.load("property_hazard_curve", TEST_CATCHMENT, mode="she") == she
    assert repo.load("property_hazard_curve", TEST_CATCHMENT, mode="flood") == flood
    assert repo.exists("property_hazard_curve", TEST_CATCHMENT, mode="bri") is False


def test_document_replace_overwrites(repo):
    repo.save("trade_marks", TEST_CATCHMENT, {"v": 1})
    repo.save("trade_marks", TEST_CATCHMENT, {"v": 2})
    assert repo.load("trade_marks", TEST_CATCHMENT) == {"v": 2}


def test_document_load_missing_raises(repo):
    with pytest.raises(FileNotFoundError):
        repo.load("market_state", TEST_CATCHMENT)


def test_document_exists_has_collection_iter_keys(repo):
    assert repo.exists("seismic_results", TEST_CATCHMENT) is False
    assert repo.has_collection("seismic_results", TEST_CATCHMENT) is False
    repo.save("seismic_results", TEST_CATCHMENT, {"events": []})
    assert repo.exists("seismic_results", TEST_CATCHMENT) is True
    assert repo.has_collection("seismic_results", TEST_CATCHMENT) is True
    assert list(repo.iter_keys("seismic_results", TEST_CATCHMENT)) == []  # not keyed


def test_document_delete(repo):
    repo.save("fire_results", TEST_CATCHMENT, {"events": [1]})
    repo.delete("fire_results", TEST_CATCHMENT)
    assert repo.exists("fire_results", TEST_CATCHMENT) is False
    repo.delete("fire_results", TEST_CATCHMENT)  # no-op, no raise


def test_ping(repo):
    assert repo.ping() is True


# ---------------------------------------------------------------------------
# ETL: file → Postgres, with dual-read parity (WP1.5)
# ---------------------------------------------------------------------------

def test_import_catchment_dual_read_parity(repo, tmp_path):
    """Load file-backed artifacts into Postgres, then PG-load must deep-equal
    file-load — the convincing end-to-end proof."""
    files = FileRepository(dir_resolver=lambda _catchment: tmp_path)
    files.save("gauge", TEST_CATCHMENT, _gauge_doc())
    files.save("gauge_hazard_curve", TEST_CATCHMENT, _ghc_doc())
    files.save("prs_trade", TEST_CATCHMENT,
               {"PhysicalSwap": {"Header": {"SwapID": "PRS-1"}}}, key="PRS-1")
    files.save("market_state", TEST_CATCHMENT, {"rates": {"GBP": 0.05}})        # document
    files.save("property_hazard_curve", TEST_CATCHMENT,                          # document, 2 modes
               {"hazard_curves": {"PROP-1": {"rp": [1]}}}, mode="flood")
    files.save("property_hazard_curve", TEST_CATCHMENT,
               {"hazard_curves": {"PROP-1": {"rp": [2]}}}, mode="she")
    files.save("gauge_timeseries", TEST_CATCHMENT, {"series": [1]}, key="GAUGE-1")  # keyed record
    files.save("property_timeseries", TEST_CATCHMENT,                            # keyed record, 2 modes
               {"ts": [1]}, key="PROP-1", mode="flood")
    files.save("property_timeseries", TEST_CATCHMENT, {"ts": [2]}, key="PROP-1", mode="she")

    counts = import_catchment(TEST_CATCHMENT, file_repo=files, pg=repo)

    assert counts["gauge"] == 2
    assert counts["gauge_hazard_curve"] == 2
    assert counts["prs_trade"] == 1
    assert counts["eod_snapshot"] == 0  # nothing written; keyed loop yields nothing
    assert counts["market_state"] == 1                  # one mode imported
    assert counts["property_hazard_curve"] == 2         # flood + she modes imported
    assert counts["fire_results"] == 0                  # document absent on file side
    assert counts["gauge_timeseries"] == 1              # one keyed record
    assert counts["property_timeseries"] == 2           # flood + she records

    # Dual-read parity: every PG read deep-equals the file read.
    assert repo.load("gauge", TEST_CATCHMENT) == files.load("gauge", TEST_CATCHMENT)
    assert repo.load("gauge_hazard_curve", TEST_CATCHMENT) == files.load("gauge_hazard_curve", TEST_CATCHMENT)
    assert repo.load("prs_trade", TEST_CATCHMENT, "PRS-1") == files.load("prs_trade", TEST_CATCHMENT, "PRS-1")
    assert repo.load("market_state", TEST_CATCHMENT) == files.load("market_state", TEST_CATCHMENT)
    assert repo.load("property_hazard_curve", TEST_CATCHMENT, mode="she") == \
        files.load("property_hazard_curve", TEST_CATCHMENT, mode="she")
    assert repo.load("gauge_timeseries", TEST_CATCHMENT, "GAUGE-1") == \
        files.load("gauge_timeseries", TEST_CATCHMENT, "GAUGE-1")
    assert repo.load("property_timeseries", TEST_CATCHMENT, "PROP-1", mode="she") == \
        files.load("property_timeseries", TEST_CATCHMENT, "PROP-1", mode="she")


def test_ping_false_when_unreachable(repo, monkeypatch):
    monkeypatch.setenv("MKM_DATABASE_URL", "postgresql+psycopg2://x:y@127.0.0.1:1/nope")
    reset_engine()
    assert repo.ping() is False
