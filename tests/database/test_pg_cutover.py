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

"""Cutover CLI (WP2.2) — orchestration only, driven with in-memory backends so the
whole thing runs without a live database."""

from database import InMemoryRepository
from database._pg import cutover

CAT = "__cutovertest__"


def _gauge_doc(order=("GAUGE-001", "GAUGE-002")):
    return {
        "flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": gid}}} for gid in order],
        "generation_metadata": {"count": len(order)},
    }


def test_run_import_reports_counts():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc())
    counts = cutover.run_import(CAT, file_repo, pg)
    assert counts["gauge"] == 2
    assert pg.exists("gauge", CAT) is True


def test_verify_true_when_parity_holds():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    # Records in opposing order — verify must normalise and still pass.
    file_repo.save("gauge", CAT, _gauge_doc(("GAUGE-002", "GAUGE-001")))
    pg.save("gauge", CAT, _gauge_doc(("GAUGE-001", "GAUGE-002")))
    assert cutover.verify(CAT, file_repo, pg) is True


def test_verify_false_on_mismatch():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(("GAUGE-001",)))
    pg.save("gauge", CAT, _gauge_doc(("GAUGE-009",)))
    assert cutover.verify(CAT, file_repo, pg) is False


def test_main_returns_zero_on_parity():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("gauge", CAT, _gauge_doc())
    assert cutover.main([CAT], file_repo=file_repo, pg=pg) == 0


def test_main_returns_one_on_mismatch():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc(("GAUGE-001",)))
    pg.save("gauge", CAT, _gauge_doc(("GAUGE-009",)))
    assert cutover.main([CAT], file_repo=file_repo, pg=pg) == 1


def test_main_import_flag_imports_then_verifies():
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    file_repo.save("gauge", CAT, _gauge_doc())   # pg starts empty
    assert cutover.main([CAT, "--import"], file_repo=file_repo, pg=pg) == 0
    assert pg.exists("gauge", CAT) is True        # the --import step populated pg


def test_main_uses_default_backends(monkeypatch):
    file_repo, pg = InMemoryRepository(), InMemoryRepository()
    for repo in (file_repo, pg):
        repo.save("gauge", CAT, _gauge_doc())
    monkeypatch.setattr(cutover, "from_config", lambda: file_repo)
    monkeypatch.setattr(cutover, "PostgresRepository", lambda: pg)
    assert cutover.main([CAT]) == 0
