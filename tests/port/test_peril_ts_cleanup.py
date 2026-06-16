# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
