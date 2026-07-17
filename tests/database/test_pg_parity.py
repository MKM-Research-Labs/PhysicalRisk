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

"""Dual-read parity harness (JSON→Postgres WP1.7).

The pure-logic tests run everywhere (no DB): they drive the harness with two
``InMemoryRepository`` backends, one holding a collection in *source-file* order
and the other in *id* order, proving the by-id normalisation makes them compare
equal — the exact real-data trap a positional ``==`` would fall into.

The live test at the bottom imports an out-of-order file catchment into a real
Postgres and asserts every parity check passes end-to-end; it SKIPS when no
Postgres is reachable, so the normal suite stays green.
"""

import pytest

from database import FileRepository, InMemoryRepository
from database._pg import parity
from database._pg.parity import (
    ParityResult,
    _diff_detail,
    all_ok,
    check_catchment,
    check_collection,
    check_document,
    check_keyed,
    format_report,
    normalize_collection,
)

CAT = "__paritytest__"


def _gauge(gid, **extra):
    header = {"GaugeID": gid, **extra}
    return {"FloodGauge": {"Header": header}}


def _gauge_doc(order, **per_id_extra):
    """A gauge collection whose records appear in ``order`` (a list of ids)."""
    return {
        "flood_gauges": [_gauge(gid, **per_id_extra.get(gid, {})) for gid in order],
        "generation_metadata": {"count": len(order)},
    }


def _ghc_doc():
    return {
        "metadata": {"distribution": "gev"},
        "hazard_curves": {
            "GAUGE-002": {"gauge_id": "GAUGE-002", "scale": 0.6},
            "GAUGE-001": {"gauge_id": "GAUGE-001", "scale": 0.5},
        },
    }


# ---------------------------------------------------------------------------
# normalize_collection — the by-id ordering that makes parity hold
# ---------------------------------------------------------------------------

def test_normalize_sorts_list_by_id_without_mutating_input():
    doc = _gauge_doc(["GAUGE-003", "GAUGE-001", "GAUGE-002"])
    out = normalize_collection("gauge", doc)
    assert [g["FloodGauge"]["Header"]["GaugeID"] for g in out["flood_gauges"]] == \
        ["GAUGE-001", "GAUGE-002", "GAUGE-003"]
    # original untouched (we copied, not sorted in place)
    assert doc["flood_gauges"][0]["FloodGauge"]["Header"]["GaugeID"] == "GAUGE-003"


def test_normalize_dict_collection_returned_unchanged():
    doc = _ghc_doc()
    assert normalize_collection("gauge_hazard_curve", doc) is doc


def test_normalize_missing_container_returned_unchanged():
    doc = {"generation_metadata": {}}
    assert normalize_collection("gauge", doc) is doc


def test_normalize_tolerates_record_missing_its_id():
    """A malformed record (no GaugeID) sorts to the front instead of raising."""
    doc = {"flood_gauges": [_gauge("GAUGE-001"), {"FloodGauge": {}}],
           "generation_metadata": {}}
    out = normalize_collection("gauge", doc)
    assert out["flood_gauges"][0] == {"FloodGauge": {}}  # "" id sorts first


# ---------------------------------------------------------------------------
# check_collection
# ---------------------------------------------------------------------------

def test_collection_equal_despite_record_order():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(["GAUGE-003", "GAUGE-001", "GAUGE-002"]))
    pg.save("gauge", CAT, _gauge_doc(["GAUGE-001", "GAUGE-002", "GAUGE-003"]))
    result = check_collection("gauge", CAT, file_repo, pg)
    assert result == ParityResult("gauge", "collection", True, 3, 3, "")


def test_collection_mismatch_on_record_value():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(["GAUGE-001"]))
    pg.save("gauge", CAT, _gauge_doc(["GAUGE-001"], **{"GAUGE-001": {"GaugeName": "X"}}))
    result = check_collection("gauge", CAT, file_repo, pg)
    assert result.equal is False
    assert result.detail == "value for 'flood_gauges' differs"


def test_collection_mismatch_on_envelope_keys():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(["GAUGE-001"]))
    pg_doc = _gauge_doc(["GAUGE-001"])
    pg_doc["seed"] = 7  # extra top-level (envelope) key
    pg.save("gauge", CAT, pg_doc)
    result = check_collection("gauge", CAT, file_repo, pg)
    assert result.equal is False
    assert "only-pg={'seed'}" in result.detail


def test_collection_present_only_one_side():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(["GAUGE-001"]))
    result = check_collection("gauge", CAT, file_repo, pg)
    assert result == ParityResult("gauge", "collection", False, 1, 0,
                                  "present only in file backend")


def test_collection_absent_both_sides_skipped():
    assert check_collection("gauge", CAT, InMemoryRepository(), InMemoryRepository()) is None


# ---------------------------------------------------------------------------
# check_keyed
# ---------------------------------------------------------------------------

def _trade(sid, **header):
    return {"PhysicalSwap": {"Header": {"SwapID": sid, **header}}}


def test_keyed_equal():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("prs_trade", CAT, _trade("PRS-1"), key="PRS-1")
    result = check_keyed("prs_trade", CAT, file_repo, pg)
    assert result == ParityResult("prs_trade", "keyed", True, 1, 1, "")


def test_keyed_both_empty_is_parity():
    result = check_keyed("prs_trade", CAT, InMemoryRepository(), InMemoryRepository())
    assert result == ParityResult("prs_trade", "keyed", True, 0, 0, "")


def test_keyed_key_sets_differ():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("prs_trade", CAT, _trade("PRS-1"), key="PRS-1")
    pg.save("prs_trade", CAT, _trade("PRS-2"), key="PRS-2")
    result = check_keyed("prs_trade", CAT, file_repo, pg)
    assert result.equal is False
    assert "only-file={'PRS-1'}" in result.detail and "only-pg={'PRS-2'}" in result.detail


def test_keyed_record_value_differs():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("prs_trade", CAT, _trade("PRS-1", TradeStatus="Open"), key="PRS-1")
    pg.save("prs_trade", CAT, _trade("PRS-1", TradeStatus="Closed"), key="PRS-1")
    result = check_keyed("prs_trade", CAT, file_repo, pg)
    assert result.equal is False
    assert result.detail.startswith("record 'PRS-1' differs")


def test_keyed_mode_aware_label_and_compare():
    """A mode-varying keyed-record artifact (timeseries) is compared per mode and
    labelled with its mode when non-default."""
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("property_timeseries", CAT, {"ts": [1, 2]}, key="PROP-1", mode="she")
    result = check_keyed("property_timeseries", CAT, file_repo, pg, "she")
    assert result == ParityResult("property_timeseries:she", "keyed", True, 1, 1, "")


def test_keyed_mode_isolates_keys():
    """Keys under one mode don't leak into another mode's comparison."""
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("property_timeseries", CAT, {"ts": [1]}, key="PROP-1", mode="flood")
    pg.save("property_timeseries", CAT, {"ts": [1]}, key="PROP-1", mode="she")
    # comparing the 'flood' mode: file has PROP-1, pg has none
    result = check_keyed("property_timeseries", CAT, file_repo, pg, "flood")
    assert result.equal is False
    assert "only-file={'PROP-1'}" in result.detail


def test_blob_kind_compares_bytes_equal():
    """The blob tier reuses check_keyed with kind='blob'; records are bytes."""
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("classifier", CAT, b"\x80\x03model", key="GAUGE-1")
    result = check_keyed("classifier", CAT, file_repo, pg, kind="blob")
    assert result == ParityResult("classifier", "blob", True, 1, 1, "")


def test_blob_kind_byte_mismatch():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("classifier", CAT, b"aaa", key="GAUGE-1")
    pg.save("classifier", CAT, b"bbb", key="GAUGE-1")
    result = check_keyed("classifier", CAT, file_repo, pg, kind="blob")
    assert result.equal is False
    assert result.detail == "record 'GAUGE-1' differs: values differ"


# ---------------------------------------------------------------------------
# check_document — whole-document artifacts (no by-id normalisation)
# ---------------------------------------------------------------------------

def test_document_equal_default_mode():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("market_state", CAT, {"rates": {"GBP": 0.05}})
    result = check_document("market_state", CAT, file_repo, pg, "flood")
    assert result == ParityResult("market_state", "document", True, 1, 1, "")


def test_document_label_carries_non_default_mode():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("property_hazard_curve", CAT, {"hc": [1]}, mode="she")
    result = check_document("property_hazard_curve", CAT, file_repo, pg, "she")
    assert result.artifact == "property_hazard_curve:she"
    assert result.equal is True


def test_document_value_mismatch():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("trade_marks", CAT, {"v": 1})
    pg.save("trade_marks", CAT, {"v": 2})
    result = check_document("trade_marks", CAT, file_repo, pg, "flood")
    assert result.equal is False
    assert result.detail == "value for 'v' differs"


def test_document_present_one_side():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    pg.save("fire_results", CAT, {"events": []})
    result = check_document("fire_results", CAT, file_repo, pg, "flood")
    assert result == ParityResult("fire_results", "document", False, 0, 1,
                                  "present only in pg backend")


def test_document_absent_both_skipped():
    assert check_document("fire_results", CAT, InMemoryRepository(),
                          InMemoryRepository(), "flood") is None


# ---------------------------------------------------------------------------
# modes_for — which scenario modes a document artifact spans (pure, no DB)
# ---------------------------------------------------------------------------

def test_modes_for_real_artifacts():
    from database._pg.pg_repo import modes_for
    assert modes_for("market_state") == ["flood"]               # mode-invariant
    assert modes_for("property_hazard_curve") == list(
        ("flood", "shd", "she", "bri", "win", "faw", "fow", "bow", "baw"))


def test_modes_for_skips_modes_without_a_location(monkeypatch):
    """A document whose location map lacks some modes yields only the ones it has
    — the defensive KeyError guard that decouples SCENARIO_MODES from each map."""
    from database._pg import pg_repo
    from database.artifacts import DOCUMENT, Spec

    def loc(mode):
        return {"flood": "a.json", "she": "b.json"}[mode]  # KeyError for other modes

    monkeypatch.setattr(pg_repo.artifacts, "spec", lambda _a: Spec(DOCUMENT, loc))
    assert pg_repo.modes_for("anything") == ["flood", "she"]


# ---------------------------------------------------------------------------
# check_catchment + reporting
# ---------------------------------------------------------------------------

def _seed_parity_pair():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(["GAUGE-002", "GAUGE-001"]))
    pg.save("gauge", CAT, _gauge_doc(["GAUGE-001", "GAUGE-002"]))
    for repo in (file_repo, pg):
        repo.save("prs_trade", CAT, _trade("PRS-1"), key="PRS-1")
        repo.save("market_state", CAT, {"rates": {"GBP": 0.05}})            # document
        repo.save("gauge_timeseries", CAT, {"series": [1]}, key="GAUGE-1")  # keyed record
        repo.save("classifier", CAT, b"model-bytes", key="GAUGE-1")         # blob
    return file_repo, pg


def test_check_catchment_aggregates_and_passes():
    file_repo, pg = _seed_parity_pair()
    results = check_catchment(CAT, file_repo=file_repo, pg=pg)
    by_artifact = {r.artifact: r for r in results}
    # gauge present + compared; the other collections absent both sides -> skipped
    assert by_artifact["gauge"].equal is True
    assert "property" not in by_artifact
    # both keyed artifacts always reported (eod_snapshot empty on both -> parity)
    assert by_artifact["prs_trade"].equal is True
    assert by_artifact["eod_snapshot"] == ParityResult("eod_snapshot", "keyed", True, 0, 0, "")
    # the seeded document is checked; documents absent both sides are skipped
    assert by_artifact["market_state"] == ParityResult("market_state", "document", True, 1, 1, "")
    assert "fire_results" not in by_artifact
    # the seeded keyed record is checked; keyed-records absent both sides are skipped
    assert by_artifact["gauge_timeseries"] == ParityResult("gauge_timeseries", "keyed", True, 1, 1, "")
    assert "stress_storm" not in by_artifact
    # the seeded blob is checked (kind 'blob')
    assert by_artifact["classifier"] == ParityResult("classifier", "blob", True, 1, 1, "")
    assert all_ok(results) is True


def test_check_catchment_uses_default_backends(monkeypatch):
    file_repo, pg = _seed_parity_pair()
    monkeypatch.setattr(parity, "from_config", lambda: file_repo)
    monkeypatch.setattr(parity, "PostgresRepository", lambda: pg)
    results = check_catchment(CAT)
    assert all_ok(results) is True


def test_all_ok_false_when_any_mismatch():
    results = [ParityResult("gauge", "collection", True, 1, 1),
               ParityResult("prs_trade", "keyed", False, 1, 0, "key sets differ")]
    assert all_ok(results) is False


def test_format_report_pass_and_fail():
    ok = [ParityResult("gauge", "collection", True, 152, 152)]
    report = format_report("thames", ok)
    assert "catchment 'thames'" in report
    assert "[OK  ] gauge" in report
    assert report.endswith("ALL PARITY CHECKS PASSED")

    bad = [ParityResult("gauge", "collection", False, 152, 151, "value for 'flood_gauges' differs")]
    report = format_report("thames", bad)
    assert "[FAIL] gauge" in report
    assert "(value for 'flood_gauges' differs)" in report
    assert report.endswith("PARITY MISMATCHES FOUND")


def test_diff_detail_on_non_dict_payloads():
    assert _diff_detail("a", "b") == "values differ"


# ---------------------------------------------------------------------------
# Live Postgres: import out-of-order file data, parity must hold end-to-end
# ---------------------------------------------------------------------------

def _postgres_available() -> bool:
    try:
        from sqlalchemy import text

        from database._pg import get_engine, reset_engine
        reset_engine()
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        from database._pg import reset_engine
        reset_engine()


@pytest.mark.skipif(
    not _postgres_available(),
    reason="no live Postgres (run: scripts/pg-native.sh start)",
)
def test_live_parity_holds_despite_file_order(tmp_path):
    """The convincing end-to-end proof: file records deliberately stored out of
    id order still pass parity once Postgres reassembles them in id order."""
    from database._pg import (
        Catchment,
        EodSnapshot,
        Gauge,
        GaugeHazardCurve,
        PortDocument,
        PortRecord,
        PortRun,
        PrsTrade,
        get_session,
        reset_engine,
    )
    from database._pg.etl import import_catchment
    from database._pg.pg_repo import PostgresRepository

    reset_engine()
    files = FileRepository(dir_resolver=lambda _catchment: tmp_path)
    files.save("gauge", CAT, _gauge_doc(["GAUGE-003", "GAUGE-001", "GAUGE-002"]))
    files.save("gauge_hazard_curve", CAT, _ghc_doc())
    files.save("prs_trade", CAT, _trade("PRS-1"), key="PRS-1")
    files.save("market_state", CAT, {"rates": {"GBP": 0.05}})          # document
    files.save("property_hazard_curve", CAT, {"hc": [1]}, mode="she")  # mode-varying document
    files.save("gauge_timeseries", CAT, {"series": [1]}, key="GAUGE-1")          # keyed record
    files.save("property_timeseries", CAT, {"ts": [2]}, key="PROP-1", mode="she")  # mode-varying

    pg = PostgresRepository()
    try:
        import_catchment(CAT, file_repo=files, pg=pg)
        results = check_catchment(CAT, file_repo=files, pg=pg)
        assert all_ok(results), format_report(CAT, results)
        # the gauge collection genuinely round-tripped all three records
        assert next(r for r in results if r.artifact == "gauge").pg_count == 3
        # the document + keyed-record tiers were exercised too (incl. non-default modes)
        labels = {r.artifact for r in results}
        assert {"market_state", "property_hazard_curve:she",
                "gauge_timeseries", "property_timeseries:she"} <= labels
    finally:
        with get_session() as session:
            for model in (Gauge, GaugeHazardCurve, PrsTrade, EodSnapshot,
                          PortDocument, PortRecord, PortRun):
                session.query(model).filter_by(catchment_id=CAT).delete()
            anchor = session.get(Catchment, CAT)
            if anchor is not None:
                session.delete(anchor)
            session.commit()
        reset_engine()
