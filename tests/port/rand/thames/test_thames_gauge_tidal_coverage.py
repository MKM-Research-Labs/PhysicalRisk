# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for the thames gauge TidalInfluence fallbacks — mirrors the
halong tidal tests: missing longitude and a bounds-lookup failure both yield
"Non-tidal"."""

from port.rand.thames.gauge import gauge_field_generators as gfg


class TestThamesTidalFallbacks:
    def test_missing_lon_returns_non_tidal(self):
        meta = {"location": {"lon": None}}
        assert gfg.generate_menu_value("TidalInfluence", {}, 0, meta) == "Non-tidal"  # 256

    def test_bounds_error_returns_non_tidal(self, monkeypatch):
        def _boom():
            raise RuntimeError("no catchment bounds")

        monkeypatch.setattr(gfg, "get_catchment_bounds", _boom)
        meta = {"location": {"lon": -0.1}}
        assert gfg.generate_menu_value("TidalInfluence", {}, 0, meta) == "Non-tidal"  # 261-262
