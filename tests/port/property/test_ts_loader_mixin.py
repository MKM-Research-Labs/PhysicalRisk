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

"""LoaderMixin's guard arms in the property timeseries generator.

Two arms had no test: an unreadable storm-sequence document, and the filter
that keeps synthetic gauges out of the gaugets map. Both decide what the
generator sees, and both fail quietly — a swallowed read leaves every storm
unmapped to its sequence, which shows up much later as flood events that
belong to no scenario.
"""

import pytest

import database
from port.src.property.ts.loader import LoaderMixin


class _Loader(LoaderMixin):
    """The mixin is only ever used through a generator; this is the minimum
    host it needs to be exercised on its own."""


class TestStormSequenceMap:

    def test_sequences_are_flattened_to_storm_ids(self, monkeypatch):
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "get_storm_sequences", lambda _c: {
            "sequences": [
                {"sequence_id": "SEQ-1", "storms": [{"storm_id": "STORM-1"},
                                                    {"storm_id": "STORM-2"}]},
                {"sequence_id": "SEQ-2", "storms": [{"storm_id": "STORM-3"}]},
            ]})
        assert _Loader()._load_storm_sequence_map() == {
            "STORM-1": "SEQ-1", "STORM-2": "SEQ-1", "STORM-3": "SEQ-2"}

    @pytest.mark.parametrize("exc", [OSError, ValueError, KeyError])
    def test_an_unreadable_document_yields_an_empty_map(self, monkeypatch, exc):
        """Empty, not an exception: the generator treats an absent mapping as
        'no sequences known' and carries on."""
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "get_storm_sequences",
                            lambda _c: (_ for _ in ()).throw(exc("unreadable")))
        assert _Loader()._load_storm_sequence_map() == {}

    def test_a_missing_document_yields_an_empty_map(self, monkeypatch):
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "get_storm_sequences", lambda _c: None)
        assert _Loader()._load_storm_sequence_map() == {}

    def test_a_storm_with_no_id_is_skipped(self, monkeypatch):
        """A blank key would collide across sequences and silently overwrite."""
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "get_storm_sequences", lambda _c: {
            "sequences": [{"sequence_id": "SEQ-1",
                           "storms": [{"storm_id": ""}, {"storm_id": "STORM-1"}]}]})
        assert _Loader()._load_storm_sequence_map() == {"STORM-1": "SEQ-1"}


class TestGaugetsLoading:

    def test_synthetic_gauges_are_excluded(self, monkeypatch):
        """SYNTH- gauges carry no observed timeseries, so including them would
        put fabricated readings into the property flood calculation."""
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "iter_gauge_timeseries_ids",
                            lambda _c: iter(["GAUGE-1", "SYNTH-1", "GAUGE-2"]))
        monkeypatch.setattr(database, "get_gauge_timeseries",
                            lambda _c, gid: {"gauge_id": gid})

        result = _Loader()._load_gaugets()

        assert sorted(result) == ["GAUGE-1", "GAUGE-2"]

    def test_an_empty_timeseries_is_not_stored(self, monkeypatch):
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "iter_gauge_timeseries_ids",
                            lambda _c: iter(["GAUGE-1"]))
        monkeypatch.setattr(database, "get_gauge_timeseries", lambda _c, _g: None)
        assert _Loader()._load_gaugets() == {}

    def test_the_key_comes_from_the_record_not_the_id(self, monkeypatch):
        """The stored id wins so a renamed file cannot split one gauge in two."""
        monkeypatch.setattr(database, "active_catchment", lambda: "thames")
        monkeypatch.setattr(database, "iter_gauge_timeseries_ids",
                            lambda _c: iter(["GAUGE-file"]))
        monkeypatch.setattr(database, "get_gauge_timeseries",
                            lambda _c, _g: {"gauge_id": "GAUGE-record"})
        assert list(_Loader()._load_gaugets()) == ["GAUGE-record"]
