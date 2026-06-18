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

"""The peril timeseries generator must clear stale per-asset files from its
output dir before writing, so a smaller portfolio doesn't leave leftovers from
a previous larger run (the hazard-curve stage globs the dir directly).

Mirrors the base flood-ts generator, which already self-cleans.
"""

import json

from port.src.peril.peril_ts import PerilTimeseriesGenerator
from port.utils.asset_config import RESIDENTIAL_CONFIG as RC


def _write(path, obj):
    path.write_text(json.dumps(obj))


def test_peril_ts_removes_stale_files(tmp_path):
    cfg = RC
    # Typhoon damage present so generate() proceeds (doesn't early-return).
    dmg = tmp_path / "typhoon" / "damage"
    dmg.mkdir(parents=True)
    _write(dmg / "EVT-00001.json", {"damages": [
        {"property_id": "PROP-A", "peak_sustained_ms": 60.0,
         "threshold_ms": 50.0, "v_50_eff_ms": 50.0}]})

    # Base ("normal") flood ts dir with the CURRENT two properties.
    base = tmp_path / cfg.ts_dirs["normal"]
    base.mkdir()
    for pid in ("PROP-A", "PROP-B"):
        _write(base / f"{pid}.json", {
            "property_id": pid,
            "flood_events": [{"storm_id": "SEQ-1", "flooded": True,
                              "exceeded_severe": True}]})

    # A stale leftover in the win output dir from a previous larger run.
    win = tmp_path / cfg.ts_dirs["win"]
    win.mkdir()
    _write(win / "PROP-STALE.json", {"property_id": "PROP-STALE"})

    PerilTimeseriesGenerator(output_dir=tmp_path, verbose=False).generate()

    names = {p.name for p in win.glob(cfg.id_glob)}
    assert "PROP-STALE.json" not in names          # stale removed
    assert names == {"PROP-A.json", "PROP-B.json"}  # only the current set
