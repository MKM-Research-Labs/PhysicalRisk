# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.prs.waterfall — the shared PRS spread-waterfall utility."""

from models.prs.waterfall import WATERFALL_PALETTE, waterfall_stages


_SD = {
    "gauge_spread_bps": 345.0,
    "she_spread_bps": 0.0,
    "shd_spread_bps": 121.0,
    "property_spread_bps": 0.0,
    "bri_spread_bps": 0.0,
}


class TestWaterfallStages:

    def test_empty_decomposition_returns_empty(self):
        assert waterfall_stages(None) == []
        assert waterfall_stages({}) == []

    def test_four_stages_without_bri(self):
        sd = {k: v for k, v in _SD.items() if k != "bri_spread_bps"}
        stages = waterfall_stages(sd)
        assert [s["key"] for s in stages] == ["gauge", "she", "shd", "property"]

    def test_bri_stage_appended_when_present(self):
        stages = waterfall_stages(_SD)
        assert [s["key"] for s in stages] == ["gauge", "she", "shd", "property", "bri"]

    def test_bps_values_carried(self):
        stages = {s["key"]: s["bps"] for s in waterfall_stages(_SD)}
        assert stages["gauge"] == 345.0
        assert stages["shd"] == 121.0
        assert stages["property"] == 0.0

    def test_effects_relative_to_gauge_then_bri_to_property(self):
        stages = {s["key"]: s["effect"] for s in waterfall_stages(_SD)}
        assert stages["gauge"] is None
        assert stages["she"] == -345.0      # she - gauge
        assert stages["shd"] == -224.0      # shd - gauge
        assert stages["property"] == -345.0  # property - gauge
        assert stages["bri"] == 0.0          # bri - property

    def test_colours_from_palette(self):
        for s in waterfall_stages(_SD):
            assert s["colour"] == WATERFALL_PALETTE[s["key"]]["colour"]
            assert s["muted"] == WATERFALL_PALETTE[s["key"]]["muted"]

    def test_bps_rounded_one_dp(self):
        stages = waterfall_stages({"gauge_spread_bps": 12.3456, "she_spread_bps": 1.0,
                                   "shd_spread_bps": 1.0, "property_spread_bps": 1.0})
        assert stages[0]["bps"] == 12.3
