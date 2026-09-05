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

"""Skip arms in the typhoon-damage helpers.

Each one drops a record rather than failing the request. That is the right
call — a property's storm list should still render when one typhoon file is
unreadable — but it means a systematic problem shows up as quietly missing
wind events rather than an error, so the arms are worth pinning.
"""

import json

import pytest

import database
from routes.propertyts.core_storms import _helpers


class TestTyphoonDamageLoading:

    @staticmethod
    def _load(monkeypatch, ids, getter):
        # typhoon_events_exist gates the whole function. Without forcing it
        # True the helper returns {} before reaching the loop, and every
        # assertion below would pass while testing nothing — which is what
        # the first draft of this file did.
        monkeypatch.setattr(database, "typhoon_events_exist", lambda _c: True)
        monkeypatch.setattr(database, "iter_typhoon_event_ids",
                            lambda _c: iter(ids))
        monkeypatch.setattr(database, "get_typhoon_event", getter)
        return _helpers._load_typhoon_damage_for_property("PROP-1")

    def test_the_gate_is_open_for_these_tests(self, monkeypatch):
        """Guard against the vacuous-pass above: with a good event present,
        the loader must actually return something."""
        result = self._load(
            monkeypatch, ["EVT-1"],
            lambda _c, eid: {"event_id": eid,
                             "damages": [{"property_id": "PROP-1",
                                          "damage_ratio": 0.4}]})
        assert result["EVT-1"]["damage_ratio"] == 0.4

    @pytest.mark.parametrize("exc", [OSError, json.JSONDecodeError])
    def test_an_unreadable_event_is_skipped(self, monkeypatch, exc):
        def _boom(_c, _e):
            if exc is json.JSONDecodeError:
                raise json.JSONDecodeError("bad", "", 0)
            raise exc("unreadable")
        assert self._load(monkeypatch, ["EVT-1"], _boom) == {}

    def test_a_missing_event_is_skipped(self, monkeypatch):
        """iter can name an event get cannot return — a delete between the two
        calls, or a key with no body."""
        assert self._load(monkeypatch, ["EVT-1"], lambda _c, _e: None) == {}

    def test_one_bad_event_does_not_lose_the_good_ones(self, monkeypatch):
        # The failure mode worth guarding: a single corrupt typhoon file
        # costing a property every wind event it has.
        def _get(_c, eid):
            if eid == "EVT-BAD":
                raise OSError("unreadable")
            return {"event_id": eid, "damages": [{"property_id": "PROP-1"}]}

        result = self._load(monkeypatch, ["EVT-BAD", "EVT-OK"], _get)
        assert "EVT-OK" in result


class TestPropertyAddressLookup:

    def test_an_unreadable_portfolio_yields_a_blank_address(self, monkeypatch):
        """The address is decoration on a storm row; failing to read it must
        not fail the row."""
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(
            database, "get_property_portfolio",
            lambda _c: (_ for _ in ()).throw(OSError("unreadable")))
        assert _helpers._lookup_property_address("PROP-1") == ""

    def test_an_unknown_property_yields_a_blank_address(self, monkeypatch):
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "get_property_portfolio",
                            lambda _c: {"properties": []})
        assert _helpers._lookup_property_address("PROP-404") == ""
