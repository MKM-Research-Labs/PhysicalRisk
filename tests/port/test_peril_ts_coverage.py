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

"""Coverage tests for port.src.peril.peril_ts — caching, malformed-input
fallbacks, the unknown-mode guard and the missing-base-ts error path."""

import json
import logging

import pytest
from db_helpers import tmp_catchment

from port.src.peril.peril_ts import PerilTimeseriesGenerator


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend rooted at tmp_path — the peril ts loader reads
    typhoon events + storm sequences through the database seam."""
    with tmp_catchment(tmp_path, "thames"):
        yield


def _write(path, obj):
    path.write_text(json.dumps(obj))


class TestPerilTimeseriesCoverage:
    def test_log_emits_when_verbose(self, tmp_path, caplog):
        gen = PerilTimeseriesGenerator(output_dir=tmp_path, verbose=True)
        with caplog.at_level(logging.INFO):
            gen.log("hello peril")
        assert "hello peril" in caplog.text  # line 96

    def test_wind_damage_index_caches_and_skips_bad_file(self, tmp_path):
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        (dmg / "EVT-00001.json").write_text("{ this is not valid json")  # 118,119
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        first = gen._wind_damage_index()
        assert first == {}
        assert gen._wind_damage_index() is first  # cache hit -> line 110

    def test_seq_to_event_map_caches_and_swallows_bad_file(self, tmp_path):
        (tmp_path / "storm_sequences.json").write_text("{ not json")  # line 150
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        first = gen._seq_to_event_map()
        assert first == {}
        assert gen._seq_to_event_map() is first  # cache hit -> line 138

    def test_peril_flag_unknown_mode_raises(self, tmp_path):
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        with pytest.raises(ValueError):
            gen._peril_flag("nope", True, True)  # line 172

    def test_generate_raises_when_base_ts_missing(self, tmp_path):
        # A non-empty wind damage index keeps generate() past its early
        # "no typhoon damage" return so the missing flood-spine dir raises.
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        _write(dmg / "EVT-00001.json", {"damages": [
            {"property_id": "PROP-1", "peak_sustained_ms": 60.0,
             "threshold_ms": 50.0, "v_50_eff_ms": 50.0}]})
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            gen.generate()  # line 190 — normal flood ts dir absent
