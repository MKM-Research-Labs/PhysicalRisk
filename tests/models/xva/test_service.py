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

"""Running XVA on the book outside any one caller (models.xva.service).

The port pipeline, the trade-commit route and the trading routes all go
through here. The property worth pinning is the netting-set refresh a new
trade triggers: it replaces only that counterparty's figures in the stored
run, leaves every other netting set as it was, and recomputes the totals.
"""

from datetime import date, timedelta

import pytest

import database
from config import config
from config.port import DEFAULT_YIELD_CURVE
from db_helpers import tmp_catchment
from models.xva import service

STATE = {"yield_curve": DEFAULT_YIELD_CURVE, "risk_free_rate": 0.03}


def _row(swap_id, cpty, payer=True):
    return {"swap_id": swap_id, "gauge_id": "G1", "trigger": "severe", "notional": 5e6,
            "trade_spread_bps": 150.0, "is_payer": payer, "counterparty_id": cpty, "mtm": 0.0,
            "maturity": (date.today() + timedelta(days=3 * 365)).isoformat()}


def _hazard(gauge, trigger):
    return 0.02


_hazard.fallbacks = []


def _inputs(rows):
    return rows, {}, STATE, _hazard


@pytest.fixture(autouse=True)
def _iso(tmp_path):
    with tmp_catchment(tmp_path):
        yield


def _stored():
    return database.get_xva_run(config.catchment_id)


def test_run_and_save_stores_the_whole_book():
    out = service.run_and_save(200, _inputs([_row("S1", "A"), _row("S2", "B")]))
    assert out["audit"]["scope"] == "book" and out["audit"]["hazard_curve_fallbacks"] == []
    assert _stored()["summary"]["n_netting_sets"] == 2


def test_refresh_replaces_only_that_netting_set():
    service.run_and_save(200, _inputs([_row("S1", "A"), _row("S2", "B")]))
    before = {s["counterparty_id"]: s for s in _stored()["netting_sets"]}
    merged = service.refresh_netting_set(
        "A", 200, _inputs([_row("S1", "A"), _row("S3", "A", payer=False), _row("S2", "B")]))
    after = {s["counterparty_id"]: s for s in merged["netting_sets"]}
    assert after["B"] == before["B"]
    assert after["A"]["n_trades"] == 2
    assert {t["swap_id"] for t in merged["trades"]} == {"S1", "S2", "S3"}
    assert merged["summary"]["xva_total"] == pytest.approx(
        sum(s["booked"]["total"]["value"] for s in merged["netting_sets"]))
    assert merged["audit"]["refreshed"]["counterparty_id"] == "A"
    assert _stored() == merged


def test_refresh_without_a_stored_run_is_marked_partial():
    merged = service.refresh_netting_set("A", 200, _inputs([_row("S1", "A"), _row("S2", "B")]))
    assert merged["audit"]["scope"] == "partial"
    assert [s["counterparty_id"] for s in merged["netting_sets"]] == ["A"]


def test_an_unassigned_trade_refreshes_the_unassigned_set():
    merged = service.refresh_netting_set(None, 200, _inputs([_row("S1", None)]))
    assert merged["netting_sets"][0]["counterparty_id"] == "UNASSIGNED"
