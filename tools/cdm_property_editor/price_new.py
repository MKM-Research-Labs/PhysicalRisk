# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Price a newly-added asset that has no timeseries yet (Workstream B / B4).

The instant re-depth shortcut needs a property's stored ``attenuated_wse_m``,
which a brand-new record does not have (it was never propagated). So a new asset
is priced by running the REAL batch generators — timeseries (4 modes) + hazard
curves (4 modes) + spread decomposition — over a scoped 1-asset workspace, in a
fresh subprocess via ``MKM_CATCHMENT_INPUT_OVERRIDE`` (so nothing touches data/).
The gauges/storms are the existing baseline (symlinked, read-only); only the one
new asset's property.json is written. This is the Opt-2 "scoped batch" path —
the same code the portfolio run uses, just narrowed to one record.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Read-only baseline inputs the generators need (everything EXCEPT the asset
# records file, which we write with the single new record).
_INPUT_LINKS = ["gauge.json", "gaugehc.json", "storm_sequences.json",
                "storm_control.json", "gaugets", "sequence_gauge", "gaugehd"]

# Per-asset: the records file, its container key, the generator module + class,
# and the hazard-curve file the result is read back from.
_ASSET = {
    "property": {
        "records_file": "property.json", "container": "properties",
        "ts_import": "from port.src.property import propertyts as _ts",
        "hc_import": "from port.src.property import propertyhc as _hc",
        "ts_cls": "_ts.PropertyTimeSeriesGenerator",
        "hc_cls": "_hc.PropertyHazardCurveGenerator",
        "hc_file": "propertyhc.json", "hc_container": "property_hazard_curves",
    },
    "commercial": {
        "records_file": "commercial.json", "container": "commercial_assets",
        "ts_import": "from port.src.commercial import commercialts as _ts",
        "hc_import": "from port.src import commercial as _hc",
        "ts_cls": "_ts.CommercialTimeSeriesGenerator",
        "hc_cls": "_hc.CommercialHazardCurveGenerator",
        "hc_file": "commercialhc.json", "hc_container": "property_hazard_curves",
    },
}


def _subprocess_code(ws: Path, cfg: dict, src_dir: Path, repo_root: Path) -> str:
    """The fresh-process script: run ts (4 modes) + hc (4 modes) + decomposition."""
    return (
        "import os, sys\n"
        f"os.environ['MKM_CATCHMENT_INPUT_OVERRIDE'] = r'{ws}'\n"
        "os.environ['MKM_CATCHMENT'] = 'thames'\n"
        f"sys.path[:0] = [r'{src_dir}', r'{repo_root}']\n"
        "from config import config\n"
        f"{cfg['ts_import']}\n"
        f"{cfg['hc_import']}\n"
        "out = config.get_input_dir()\n"
        "for _m in ('normal', 'shd', 'she', 'bri'):\n"
        f"    {cfg['ts_cls']}(out, mode=_m, verbose=False).generate()\n"
        f"{cfg['hc_cls']}(out, verbose=False).generate()\n"
        f"{cfg['hc_cls']}(out, mode='shd', verbose=False).generate()\n"
        f"{cfg['hc_cls']}(out, mode='she', verbose=False).generate()\n"
        f"{cfg['hc_cls']}(out, mode='bri', verbose=False).generate()\n"
        f"{cfg['hc_cls']}(out, verbose=False).attach_spread_decomposition()\n"
    )


def price_asset(asset: str, rid: str, record: dict, *, input_dir: Path,
                src_dir: Path, repo_root: Path, timeout: int = 600) -> dict:
    """Generate + price one new asset. Returns the priced hazard-curve entry.

    Result: ``{"ok": bool, "curve": {...}|None, "error": str|None}``. The curve
    carries ``spread_decomposition`` (the waterfall) plus flood_count / flood_zone
    / summary, exactly as the batch produces it.
    """
    cfg = _ASSET.get(asset)
    if cfg is None:
        return {"ok": False, "curve": None, "error": f"Pricing '{asset}' is not supported."}

    work = Path(tempfile.mkdtemp(prefix=f"price_{asset}_"))
    try:
        for name in _INPUT_LINKS:
            src = input_dir / name
            if src.exists():
                (work / name).symlink_to(src)
        # the one new record, in the asset's records file + container
        (work / cfg["records_file"]).write_text(
            json.dumps({cfg["container"]: [record]}))

        code = _subprocess_code(work, cfg, src_dir, repo_root)
        proc = subprocess.run([sys.executable, "-c", code],
                              capture_output=True, text=True, timeout=timeout)
        hc_path = work / cfg["hc_file"]
        if not hc_path.exists():
            return {"ok": False, "curve": None,
                    "error": "generation produced no hazard curve.\n"
                             + proc.stderr[-1500:]}
        curves = json.loads(hc_path.read_text()).get(cfg["hc_container"], {})
        curve = curves.get(rid)
        if curve is None:
            return {"ok": False, "curve": None,
                    "error": "asset not in generated curves (no flood events / "
                             "too few to price, or coordinates outside the catchment)."}
        return {"ok": True, "curve": curve, "error": None}
    except subprocess.TimeoutExpired:
        return {"ok": False, "curve": None, "error": "pricing timed out."}
    finally:
        shutil.rmtree(work, ignore_errors=True)
