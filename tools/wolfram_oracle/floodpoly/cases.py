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
"""FPO-001's code against its document, case by case.

``p_flood_poly`` over thresholds, levels from zero to half again above severe, and
the storm's hours -- through the floor, the envelope and the step at severe;
``p_flood_series``; ``p_flood_simple``; the model as ``stress.sensitivity`` evaluates
it, with its closed-form slope; what the server sends the port stress screen; and the
screen's JavaScript itself, run under node on the model the server sends.
"""

import importlib
import json
import re
import shutil
import subprocess

import mpmath as mp

from config import config
from config.models import (
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_ENVELOPE,
    ORACLE_FPO_HOURS,
    ORACLE_FPO_JS,
    ORACLE_FPO_MODULES,
    ORACLE_FPO_NODE,
    ORACLE_FPO_RATIOS,
    ORACLE_FPO_SEVERE,
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle._wl import rel_err
from tools.wolfram_oracle.floodpoly import reference as ref


SERIES = [4.0 + 0.02 * k for k in range(168)]


def load():
    return {k: importlib.import_module(m) for k, m in ORACLE_FPO_MODULES.items()}


def grid():
    return [(r * s, hr, s) for s in ORACLE_FPO_SEVERE for r in ORACLE_FPO_RATIOS for hr in ORACLE_FPO_HOURS]


def _err(a, b):
    """Relative error, absolute below 1e-300 (sigma underflows to zero in double)."""
    return float(abs(mp.mpf(a) - b)) if abs(b) < 1e-300 else rel_err(a, b)


def _on_knot(w, s):
    """At an envelope knot the held slope has a kink: no derivative to compare."""
    return any(abs(w / s - float(r)) < 1e-9 for r, _ in ORACLE_FPO_DOC_ENVELOPE)


def _held_kernel(w, hour, s):
    h, t = ref.features(w, hour, s)
    return ref.kernel(h, max(t, ref.tau(h)))


def js_function(text=None):
    """The screen's evaluation of the model: from its envelope helper to the end of
    ``_fpPFlood``. None if it is not there."""
    text = text if text is not None else (config.get_project_root() / ORACLE_FPO_JS).read_text()
    m = re.search(r"function _fpEnvelopeT.*?\n            function _fpPFlood.*?\n            }\n", text, re.S)
    return m.group(0) if m else None


def js_literal_coefficients(text=None):
    """Whether the screen still carries coefficients of its own."""
    text = text if text is not None else (config.get_project_root() / ORACLE_FPO_JS).read_text()
    return re.search(r"_fpCoeffs\s*=", text) is not None


def run_js(params, cases, fn=None, node=ORACLE_FPO_NODE):
    """``_fpPFlood`` at each (w, hour, s), run under node on the served model; None
    without node."""
    fn = fn if fn is not None else js_function()
    if fn is None or shutil.which(node) is None:
        return None
    script = (f"var _fpModel = {json.dumps(params)};\n{fn}\n"
              f"console.log(JSON.stringify({json.dumps(cases)}.map(c => _fpPFlood(c[0], c[1], c[2]))));")
    return json.loads(subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout)


def served(poly):
    """Whether what the server sends the screen is the document's model."""
    p = poly.client_params()
    return (p["coeffs"] == [float(c) for c in ORACLE_FPO_DOC_COEFFS]
            and p["envelope"] == [[float(r), float(h)] for r, h in ORACLE_FPO_DOC_ENVELOPE])


def run(m):
    """Each family's worst error, code against reference."""
    poly, sens = m["poly"], m["sensitivity"]
    with mp.workdps(ORACLE_REFERENCE_DPS):
        cases = grid()
        refs = [ref.p_flood(w, hr, s) for w, hr, s in cases]
        out = {
            "poly": max(_err(poly.p_flood_poly(w, hr, s), r) for (w, hr, s), r in zip(cases, refs)),
            "zero_threshold": poly.p_flood_poly(5.0, 10, 0.0) == 0 and poly.p_flood_simple(5.0, 0.0) == 0,
            "series": max(abs(p - poly.p_flood_poly(w, hr, 6.58)) for hr, (w, p) in enumerate(
                zip(SERIES, poly.p_flood_series(SERIES, 6.58)))),
            "simple": max(_err(poly.p_flood_simple(w, s), ref.p_simple(w, s)) for w, _, s in cases),
            "copy": max(_err(sens.flood_probability(*map(float, ref.features(w, hr, s))), r)
                        for (w, hr, s), r in zip(cases, refs) if 0 < w < s),
            "slope": max(_err(sens.flood_probability_slope(*map(float, ref.features(w, hr, s))),
                              ref.slope(*ref.features(w, hr, s)))
                         for w, hr, s in cases
                         if 0 < w < s and not _on_knot(w, s) and abs(_held_kernel(w, hr, s)) < 30),
        }
        js = run_js(poly.client_params(), cases)
        out["js"] = None if js is None else max(_err(a, r) for a, r in zip(js, refs))
    out["js_own_coefficients"] = js_literal_coefficients()
    out["served"] = served(poly)
    return out
