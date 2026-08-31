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

"""Tests for config.visual — the map's geography, and what it does without one.

Every accessor here has a fallback wrapped in a bare ``except``, and that is the half
that was untested. It is also the half that runs on a fresh checkout, on a catchment
whose params module is incomplete, and in any test that has not built a portfolio: if
the fallback is wrong, a map centres on the wrong continent and nothing raises.

The coordinates are never asserted as literals — they come from the active catchment,
and hard-coding one here would be the same mistake the accessors exist to prevent.
"""

import pytest

from config import visual


class TestMapCentre:
    def test_is_the_centre_of_the_catchment_bounds(self):
        min_lon, min_lat, max_lon, max_lat = visual.get_catchment_bounds()
        latitude, longitude = visual.get_map_center()
        assert latitude == pytest.approx((min_lat + max_lat) / 2)
        assert longitude == pytest.approx((min_lon + max_lon) / 2)

    def test_falls_back_when_the_bounds_are_unavailable(self, monkeypatch):
        """A catchment with no bounds still puts the map somewhere sensible."""
        monkeypatch.setattr(visual, "get_catchment_bounds",
                            lambda: (_ for _ in ()).throw(RuntimeError("no bounds")))
        assert visual.get_map_center() == visual.MAP_DEFAULT_CENTER


class TestDisplayName:
    def test_returns_a_non_empty_name(self):
        assert visual.get_catchment_display_name()

    def test_falls_back_when_the_params_module_will_not_load(self, monkeypatch):
        from config import config

        monkeypatch.setattr(
            config, "load_params_module",
            lambda: (_ for _ in ()).throw(ImportError("no params")))
        assert visual.get_catchment_display_name() == "catchment"

    def test_title_cases_a_lowercase_name(self, monkeypatch):
        """``thames`` reads as a mistake in a heading; ``Thames`` does not."""
        import types

        from config import config
        module = types.ModuleType("params")
        module.DISPLAYNAME = "thames"
        monkeypatch.setattr(config, "load_params_module", lambda: module)
        assert visual.get_catchment_display_name() == "Thames"

    def test_leaves_an_already_capitalised_name_alone(self, monkeypatch):
        """``title()`` would turn ``RIVER THAMES`` into ``River Thames``."""
        import types

        from config import config
        module = types.ModuleType("params")
        module.DISPLAYNAME = "RIVER THAMES"
        monkeypatch.setattr(config, "load_params_module", lambda: module)
        assert visual.get_catchment_display_name() == "RIVER THAMES"


class TestPositionLabels:
    """North/central/south and east/central/west, as thirds of the catchment."""

    @staticmethod
    def _bounds():
        return visual.get_catchment_bounds()

    def test_latitude_bands(self):
        min_lon, min_lat, max_lon, max_lat = self._bounds()
        third = (max_lat - min_lat) / 3
        assert visual.get_lat_position_label(min_lat + 2.5 * third).startswith("Northern")
        assert visual.get_lat_position_label(min_lat + 1.5 * third).startswith("Central")
        assert visual.get_lat_position_label(min_lat + 0.5 * third).startswith("Southern")

    def test_longitude_bands(self):
        min_lon, min_lat, max_lon, max_lat = self._bounds()
        third = (max_lon - min_lon) / 3
        assert visual.get_lon_position_label(min_lon + 2.5 * third).startswith("Eastern")
        assert visual.get_lon_position_label(min_lon + 1.5 * third).startswith("Central")
        assert visual.get_lon_position_label(min_lon + 0.5 * third).startswith("Western")

    def test_a_degenerate_catchment_has_no_thirds(self, monkeypatch):
        """Zero-height bounds must not divide by zero on their way to a label."""
        monkeypatch.setattr(visual, "get_catchment_bounds", lambda: (1.0, 2.0, 1.0, 2.0))
        assert visual.get_lat_position_label(2.0) == "Location within catchment"
        assert visual.get_lon_position_label(1.0) == "Location within catchment"

    def test_unavailable_bounds_fall_back(self, monkeypatch):
        monkeypatch.setattr(visual, "get_catchment_bounds",
                            lambda: (_ for _ in ()).throw(RuntimeError("no bounds")))
        assert visual.get_lat_position_label(51.5) == "Location within catchment"
        assert visual.get_lon_position_label(-0.1) == "Location within catchment"
