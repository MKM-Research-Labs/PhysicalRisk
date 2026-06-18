# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Zero-event wind-peril placeholders for no-typhoon runs.

When the typhoon ensemble hasn't run, write_peril_placeholders projects the
degenerate peril fan already embedded in the hazard curves into the standalone
scenario files (propertywin/faw/fow/bow/baw.json etc.) so the wind UI routes
serve consistent zero-event data instead of 404."""

import json

from app.commands.port.stages.windhazard._placeholders import (
    write_peril_placeholders,
)


def _curve(severe_spread, perils):
    return {
        "property_id": "PROP-1",
        "term_structure": {
            "tenors": [1, 2, 3, 4, 5],
            "severe": {"prs_spread_bps": [severe_spread] * 5},
            "perils": {k: {"prs_spread_bps": [v] * 5} for k, v in perils.items()},
        },
        "prs_perils": {
            "flood_only": {"count": 8, "spread_bps": 80.0},
            "wind_only": {"count": 0, "spread_bps": 0.0},
            "flood_or_wind": {"count": 8, "spread_bps": 80.0},
            "flood_and_wind": {"count": 0, "spread_bps": 0.0},
        },
    }


def _write_hc(path, severe, perils):
    path.write_text(json.dumps({
        "metadata": {"catchment_id": "test", "num_storms": 100},
        "property_hazard_curves": {"PROP-1": _curve(severe, perils)},
    }))


# No-wind degenerate fan: wind_only/flood_and_wind = 0, flood_or_wind = flood.
_FAN = {"flood_only": 80.0, "wind_only": 0.0,
        "flood_or_wind": 80.0, "flood_and_wind": 0.0}


def _setup(tmp_path):
    _write_hc(tmp_path / "propertyhc.json", 80.0, _FAN)
    # BRI flood is a touch lower; its no-wind fan mirrors the structure.
    _write_hc(tmp_path / "propertybri.json", 70.0,
              {"flood_only": 70.0, "wind_only": 0.0,
               "flood_or_wind": 70.0, "flood_and_wind": 0.0})


class TestWritePerilPlaceholders:
    def test_writes_all_five_modes(self, tmp_path):
        _setup(tmp_path)
        written = write_peril_placeholders(tmp_path, "property", log=lambda *_: None)
        assert written == ["win", "faw", "fow", "bow", "baw"]
        for mode in written:
            assert (tmp_path / f"property{mode}.json").exists()

    def test_zero_event_modes_have_zero_severe(self, tmp_path):
        _setup(tmp_path)
        write_peril_placeholders(tmp_path, "property", log=lambda *_: None)
        for mode in ("win", "faw", "baw"):
            d = json.loads((tmp_path / f"property{mode}.json").read_text())
            pc = d["property_hazard_curves"]["PROP-1"]
            assert pc["term_structure"]["severe"]["prs_spread_bps"] == [0.0] * 5
            assert pc["prs_peril_count"] == 0
            assert d["metadata"]["placeholder_no_typhoon"] is True
            assert d["metadata"]["wind_coupled"] is False

    def test_or_modes_carry_flood_leg(self, tmp_path):
        _setup(tmp_path)
        write_peril_placeholders(tmp_path, "property", log=lambda *_: None)
        # fow == normal flood (80); bow == BRI flood (70).
        fow = json.loads((tmp_path / "propertyfow.json").read_text())
        bow = json.loads((tmp_path / "propertybow.json").read_text())
        assert fow["property_hazard_curves"]["PROP-1"][
            "term_structure"]["severe"]["prs_spread_bps"] == [80.0] * 5
        assert bow["property_hazard_curves"]["PROP-1"][
            "term_structure"]["severe"]["prs_spread_bps"] == [70.0] * 5

    def test_missing_source_is_noop(self, tmp_path):
        # No propertyhc.json / propertybri.json present -> nothing written.
        written = write_peril_placeholders(tmp_path, "property", log=lambda *_: None)
        assert written == []

    def test_corrupt_source_is_skipped_not_raised(self, tmp_path):
        (tmp_path / "propertyhc.json").write_text("{ not json")
        (tmp_path / "propertybri.json").write_text("{ not json")
        # Must not raise; just skips.
        assert write_peril_placeholders(tmp_path, "property", log=lambda *_: None) == []
