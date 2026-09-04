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

"""Tests for GaugeLoader."""

import pytest
from tests.loaders.conftest import gauge_json, write_json


class TestGaugeLoaderBasic:

    def test_load_all_returns_list(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(3))
        assert len(GaugeLoader(tmp_path).load_all()) == 3

    def test_load_missing_file_returns_empty(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        assert GaugeLoader(tmp_path).load_all() == []

    def test_count(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(4))
        assert GaugeLoader(tmp_path).count() == 4

    def test_floodgauges_key_also_works(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        data = {"floodGauges": gauge_json(2)["flood_gauges"]}
        write_json(tmp_path / "gauge.json", data)
        assert GaugeLoader(tmp_path).count() == 2


class TestGaugeLoaderLookup:

    def test_find_by_id_returns_entity(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(3))
        result = GaugeLoader(tmp_path).find_by_id("GAUGE-001")
        assert result is not None
        assert result["FloodGauge"]["Header"]["GaugeID"] == "GAUGE-001"

    def test_find_by_id_missing_returns_none(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        assert GaugeLoader(tmp_path).find_by_id("GAUGE-999") is None

    def test_exists_true(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        assert GaugeLoader(tmp_path).exists("GAUGE-000") is True

    def test_exists_false(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        assert GaugeLoader(tmp_path).exists("GAUGE-999") is False

    def test_list_all_returns_summaries(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        summaries = GaugeLoader(tmp_path).list_all()
        assert len(summaries) == 2
        assert "gaugeId" in summaries[0]


class TestGaugeLoaderCache:

    def test_caching_works(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        loader = GaugeLoader(tmp_path)
        assert loader.load_all() is loader.load_all()

    def test_clear_cache(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        loader = GaugeLoader(tmp_path)
        loader.load_all()
        loader.clear_cache()
        assert not loader._cache_valid

    def test_force_reload(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(2))
        loader = GaugeLoader(tmp_path)
        loader.load_all()
        write_json(tmp_path / "gauge.json", gauge_json(5))
        assert len(loader.load_all(force_reload=True)) == 5


class TestGaugeLoaderStatus:

    def test_get_status_returns_dict(self, tmp_path):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(1))
        status = GaugeLoader(tmp_path).get_status()
        assert "entity_name" in status
        assert "path" in status
        assert "exists" in status


class TestGaugeLoaderMisses:
    """The not-found arms of the lookups.

    ``tests/services/gauge_loader`` covers the hits, using SAMPLE_GAUGE from
    ``tests/conftest/data``. That fixture carries ``Latitude``/``Longitude``
    in the Header — a shape the real ``gauge.json`` does not have (its
    coordinates live under ``SensorDetails.GaugeInformation`` as
    ``GaugeLatitude``/``GaugeLongitude``). So ``get_coordinates`` returns None
    for every real gauge and the fixture hides it. Pinned here against the
    production shape; see the note in the loader review.
    """

    @staticmethod
    def _loader(tmp_path, n=2):
        from loaders.gauge_loader import GaugeLoader
        write_json(tmp_path / "gauge.json", gauge_json(n))
        return GaugeLoader(tmp_path)

    def test_find_by_name_with_no_match_returns_none(self, tmp_path):
        assert self._loader(tmp_path).find_by_name("Nonexistent Weir") is None

    def test_find_by_name_matches_on_a_substring(self, tmp_path):
        """Confirms the miss above is a real miss, not a broken matcher."""
        assert self._loader(tmp_path).find_by_name("gauge 1") is not None

    def test_coordinates_for_an_unknown_gauge_are_none(self, tmp_path):
        assert self._loader(tmp_path).get_coordinates("GAUGE-999") is None

    def test_coordinates_are_none_when_the_header_omits_them(self, tmp_path):
        """The production shape: the Header carries no Latitude/Longitude.

        This is the case that makes the accessor useless against real data.
        Its only caller is get_gauges_in_radius, which nothing in src/ calls,
        so the effect today is dead surface rather than a broken feature.
        """
        assert self._loader(tmp_path).get_coordinates("GAUGE-000") is None

    def test_flood_stages_for_an_unknown_gauge_are_none(self, tmp_path):
        assert self._loader(tmp_path).get_flood_stages("GAUGE-999") is None

    def test_flood_stages_absent_from_a_known_gauge_are_none(self, tmp_path):
        assert self._loader(tmp_path).get_flood_stages("GAUGE-000") is None
