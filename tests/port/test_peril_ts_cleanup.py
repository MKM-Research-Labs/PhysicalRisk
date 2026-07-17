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

"""The peril timeseries generator must clear stale per-asset files from its
output dir before writing, so a smaller portfolio doesn't leave leftovers from
a previous larger run (the hazard-curve stage globs the dir directly).

Mirrors the base flood-ts generator, which already self-cleans.
"""

import json

import pytest
from db_helpers import tmp_catchment

from port.src.peril.peril_ts import PerilTimeseriesGenerator
from port.utils.asset_config import RESIDENTIAL_CONFIG as RC


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend rooted at tmp_path — the peril ts loader reads
    typhoon events + storm sequences through the database seam."""
    with tmp_catchment(tmp_path, "thames"):
        yield


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
