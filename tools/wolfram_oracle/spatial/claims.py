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

"""SP-001's model document, tested as stated (``spatial_model_v2.0.pdf``).

Its four sensitivity tables were generated from the code, so each figure is judged as the code's
value printed to the places the table shows. The statements about the model -- what it
accepts and returns, how accurate it is, what uses it, and what tests and validation
exist -- are judged by running the code, which the checks show computes the document's
equations, and by searching the repository.
"""

import inspect
import math
import subprocess

from config import config
from config.models import (
    ORACLE_SP_CODE_TOL,
    ORACLE_SP_EW_STATED,
    ORACLE_SP_NEAREST_TOL,
    ORACLE_SP_PRINTED_T1,
    ORACLE_SP_PRINTED_T2,
    ORACLE_SP_PRINTED_T3,
    ORACLE_SP_PRINTED_T4,
    ORACLE_SP_SOURCES,
    ORACLE_SP_SPHERE_STATED_PCT,
    ORACLE_SP_T1,
    ORACLE_SP_T2_DISTANCES,
    ORACLE_SP_T3_GAUGES,
    ORACLE_SP_TESTS,
    ORACLE_SP_USED_BY,
)

# v2.0 s2.2: retained with no production caller; and used by the property, gauge and seismic code.
RETAINED = ("spatial_interpolate_wse", "idw_interpolate_from_gauges", "build_spatial_index",
            "nearest_gauge", "build_correlation_matrix")
SHARED = ("haversine_distance", "nearest_point_on_polyline", "nearest_point_on_segment")


def _matched(got, want):
    got, want = list(got), list(want)
    return {"matched": sum(a == b for a, b in zip(got, want)), "of": len(want), "met": got == want}


def tables(sp, table4):
    idw = sp.idw_interpolate_from_gauges
    t1 = [f"{idw(list(ORACLE_SP_T1['base']), power=p):.3f}" for p in ORACLE_SP_T1["powers"]]
    t2 = [f"{idw([(float(d), 12.5), (2000.0, 11.8), (5000.0, 10.2)]):.3f}" for d in ORACLE_SP_T2_DISTANCES]
    t3 = [f"{idw(list(ORACLE_SP_T3_GAUGES[:n])):.3f}" for n in range(1, len(ORACLE_SP_T3_GAUGES) + 1)]
    rows = {km: (pct, m) for km, pct, m in table4}
    t4 = [c for km, *_ in ORACLE_SP_PRINTED_T4 for c in rows[km]]
    return {"t1": _matched(t1, ORACLE_SP_PRINTED_T1), "t2": _matched(t2, ORACLE_SP_PRINTED_T2),
            "t3": _matched(t3, ORACLE_SP_PRINTED_T3),
            "t4": _matched(t4, [c for _, *cells in ORACLE_SP_PRINTED_T4 for c in cells])}


def configurable(sp):
    """s3.2: both interpolation paths take the power and the threshold."""
    paths = (sp.spatial_interpolate_wse, sp.idw_interpolate_from_gauges)
    return {"met": all({"power", "min_distance"} <= set(inspect.signature(f).parameters) for f in paths)}


def outputs(sp):
    """s4.2: the index returns the nearest gauge's row and distance."""
    names = sorted(n for n, f in inspect.getmembers(sp, inspect.isfunction) if f.__module__ == sp.__name__)
    return {"functions": names, "met": "nearest_gauge" in names}


def empty(sp):
    """s3.2: with no gauges, both paths return 0.0."""
    return {"met": sp.spatial_interpolate_wse(51.5, -0.1, {}, {}) == 0.0 and sp.idw_interpolate_from_gauges([]) == 0.0}


def east_west():
    """s3.4: the degree conversion overstates east-west separation at 51.5 N by 61%."""
    pct = 100 * (1 / math.cos(math.radians(ORACLE_SP_EW_STATED["latitude"])) - 1)
    return pct, round(pct) == ORACLE_SP_EW_STATED["pct"]


def _grep(pattern, paths, flags=("-lE",)):
    return subprocess.run(["git", "grep", *flags, pattern, "--", *paths], capture_output=True, text=True,
                          cwd=config.get_project_root()).stdout.splitlines()


def _area(path):
    """src/models/<area>/... or src/port/src/<area>/..."""
    return path.split("/")[3] if path.startswith("src/port/src/") else path.split("/")[2]


def lineage():
    """s2.2: nothing calls the retained functions; the shared ones serve the stated areas.
    A caller is a file that imports the module and names the function (other modules
    have functions of their own called ``nearest_gauge``)."""
    src = ORACLE_SP_SOURCES[0]
    importers = set(_grep(r"floodrisk\.spatial|floodrisk import .*\bspatial\b", ["src", "scripts"])) - {src}
    users = {f: sorted(importers & set(_grep(f, ["src", "scripts"], ("-lw",)))) for f in RETAINED + SHARED}
    areas = sorted({_area(p) for f in SHARED for p in users[f]})
    return {"users": users, "areas": areas,
            "met": not any(users[f] for f in RETAINED) and tuple(areas) == ORACLE_SP_USED_BY}


def unit_tests():
    """Q4: the tests query the index for the nearest gauge."""
    found = _grep("nearest_gauge", list(ORACLE_SP_TESTS), ("-lw",))
    return {"met": bool(found)}


def validation():
    """Q5: v2.0 says nothing validates the interpolation against observations -- judged
    as no code calling it outside its unit tests and the benchmarks."""
    callers = [p for p in _grep("idw_interpolate_from_gauges|spatial_interpolate_wse", ["*.py"], ("-lwE",))
               if p != ORACLE_SP_SOURCES[0] and p not in ORACLE_SP_TESTS and not p.startswith("tools/wolfram_oracle")]
    return {"callers": callers, "met": not callers}


def kriging():
    """Q7: v2.0 says no comparison with kriging exists."""
    hits = [p for p in _grep("kriging", ["."], ("-liE",)) if not p.startswith(("tools/wolfram_oracle", "docs/models/spatial_benchmark", "tests/tools/test_wolfram_oracle"))]
    return {"files": hits, "met": not hits}


def ellipsoid(pct):
    """s5: the sphere errs by up to 0.32% against WGS84 for UK pairs under 100 km."""
    if pct is None:
        return {"worst": None, "met": None}
    worst = max(pct, key=abs)
    return {"worst": worst, "met": round(abs(worst), 2) == ORACLE_SP_SPHERE_STATED_PCT}


def assess(sp, proj, tree, det):
    """Each claim as a dict with its figures and ``met``; the sphere's waits for Wolfram."""
    ew, ew_met = east_west()
    return {
        **tables(sp, proj["table4"]),
        "configurable": configurable(sp),
        "index": {**tree, "met": tree["wrong"] == 0 and tree["picked"] == tree["nearest"]
                  and tree["distance_err"] <= ORACLE_SP_NEAREST_TOL},
        "correlation": {"err": det["corr_degrees"], "ew": ew, "met": det["corr_degrees"] <= ORACLE_SP_CODE_TOL and ew_met},
        "outputs": outputs(sp),
        "empty": empty(sp),
        "lineage": lineage(),
        "unit_tests": unit_tests(),
        "validation": validation(),
        "kriging": kriging(),
    }
