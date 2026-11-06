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
"""SP-001's model document, tested as stated (``spatial_model.pdf``, v1.0).

Its three sensitivity tables were generated from the code, so each figure is judged as
the code's value, rounded and formatted as their generator did. The statements about the
model -- what it computes, what it returns, how accurate it is, what uses it, what tests
and validates it -- are judged by running the code, which the checks show computes the
document's IDW and haversine, and by searching the repository.
"""

import inspect
import subprocess

from config import config
from config.models import (
    ORACLE_SP_FLAT_EARTH_KM,
    ORACLE_SP_PRINTED_T1,
    ORACLE_SP_PRINTED_T2,
    ORACLE_SP_PRINTED_T3,
    ORACLE_SP_SOURCES,
    ORACLE_SP_SUFFICIENT_PCT,
    ORACLE_SP_T1,
    ORACLE_SP_T2_DISTANCES,
    ORACLE_SP_T3_GAUGES,
    ORACLE_SP_TESTS,
)

# What the document says the model is for: interpolation, the index and the correlation.
DOCUMENTED = ("spatial_interpolate_wse", "idw_interpolate_from_gauges", "build_spatial_index",
              "build_correlation_matrix")
SHARED = ("haversine_distance", "nearest_point_on_polyline", "nearest_point_on_segment")


def fmt(v):
    """The generator's number format (docs/models/sensitivities latex_table)."""
    return f"{v:.1f}" if abs(v) >= 10 else (f"{v:.2f}" if abs(v) >= 1 else f"{v:.4f}")


def _matched(got, want):
    got, want = list(got), list(want)
    return {"matched": sum(a == b for a, b in zip(got, want)), "of": len(want), "met": got == want}


def tables(sp):
    idw = sp.idw_interpolate_from_gauges
    t1 = [c for p in ORACLE_SP_T1["powers"] for c in (fmt(p), fmt(round(idw(list(ORACLE_SP_T1["base"]), power=p), 3)))]
    t2 = [fmt(round(idw([(float(d), 12.5), (2000.0, 11.8), (5000.0, 10.2)], power=2.0), 3)) for d in ORACLE_SP_T2_DISTANCES]
    t3 = [fmt(round(idw(list(ORACLE_SP_T3_GAUGES[:n]), power=2.0), 3)) for n in range(1, len(ORACLE_SP_T3_GAUGES) + 1)]
    nearest = sum(d <= 2000 for d in ORACLE_SP_T2_DISTANCES)
    return {"t1": _matched(t1, [c for row in ORACLE_SP_PRINTED_T1 for c in row]),
            "t2": _matched(t2, ORACLE_SP_PRINTED_T2), "t3": _matched(t3, ORACLE_SP_PRINTED_T3),
            "t2_label": {"nearest": nearest, "of": len(ORACLE_SP_T2_DISTANCES),
                         "met": nearest == len(ORACLE_SP_T2_DISTANCES)}}


def configurable(sp):
    """s3.1, s4.1: the power and threshold are inputs of the lat/lon interpolation."""
    params = inspect.signature(sp.spatial_interpolate_wse).parameters
    return {"params": list(params), "met": "power" in params and "min_distance" in params}


def outputs(sp):
    """s4.2: something returns the nearest gauge's distance and identity."""
    names = sorted(n for n, f in inspect.getmembers(sp, inspect.isfunction) if f.__module__ == sp.__name__)
    return {"functions": names, "met": any("gauge" in n and "nearest" in n for n in names)}


def _grep(pattern, paths, flags=("-lE",)):
    return subprocess.run(["git", "grep", *flags, pattern, "--", *paths], capture_output=True, text=True,
                          cwd=config.get_project_root()).stdout.splitlines()


def lineage():
    """Who calls each function, outside the module itself (src and scripts)."""
    src = ORACLE_SP_SOURCES[0]
    users = {f: [p for p in _grep(f, ["src", "scripts"], ("-lw",)) if p != src] for f in DOCUMENTED + SHARED}
    return {"users": users, "met": any(users[f] for f in DOCUMENTED)}


def unit_tests():
    """Q4: the tests check haversine accuracy, IDW convergence and KDTree correctness --
    judged on the KDTree, whose tests would have to query it."""
    queried = _grep(r"\.query\(", list(ORACLE_SP_TESTS))
    return {"tree_queried": bool(queried), "met": bool(queried)}


def validation():
    """Q5: something compares an interpolated value with an observation -- any code that
    calls the interpolation, outside its unit tests and the benchmarks."""
    callers = [p for p in _grep("idw_interpolate_from_gauges|spatial_interpolate_wse", ["*.py"], ("-lwE",))
               if p != ORACLE_SP_SOURCES[0] and p not in ORACLE_SP_TESTS and not p.startswith(("tools/wolfram_oracle", "docs/"))]
    return {"callers": callers, "met": bool(callers)}


def kriging():
    """Q7: a comparison with kriging exists anywhere in the repository."""
    hits = [p for p in _grep("kriging", ["."], ("-liE",)) if not p.startswith(("tools/wolfram_oracle", "docs/models/spatial_benchmark"))]
    return {"files": hits, "met": bool(hits)}


def ellipsoid(pct):
    """s5.1(2): sufficient below 100 km; Q2: exact for the Earth's geometry."""
    if pct is None:
        return {"worst": None, "sufficient": None, "exact": None}
    worst = max(pct, key=abs)
    return {"worst": worst, "sufficient": abs(worst) <= ORACLE_SP_SUFFICIENT_PCT, "exact": worst == 0}


def assess(sp, proj, tree, det):
    """Each claim as a dict with its figures and ``met``; the sphere's waits for Wolfram."""
    return {
        **tables(sp),
        "configurable": configurable(sp),
        "tree": {**tree, "met": tree["wrong"] == 0 and tree["picked"] == tree["nearest"]},
        "correlation": {"err": det["corr_doc"], "met": det["corr_doc"] <= 1e-12},
        "outputs": outputs(sp),
        "flat_earth": {"near": proj["near"], "far": proj["far"], "far_m": proj["far_m"],
                       "km": ORACLE_SP_FLAT_EARTH_KM, "met": proj["near"] < 1e-4},
        "lineage": lineage(),
        "unit_tests": unit_tests(),
        "validation": validation(),
        "kriging": kriging(),
    }
