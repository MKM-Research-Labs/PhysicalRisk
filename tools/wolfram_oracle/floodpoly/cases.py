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
the storm's hours; the clamp; ``p_flood_series``; ``p_flood_simple``; the copy in
``stress.sensitivity`` with its closed-form slope; and the coefficients the port
stress screen hard-codes in JavaScript.
"""

import importlib
import re

import mpmath as mp

from config import config
from config.models import (
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_HOURS,
    ORACLE_FPO_JS,
    ORACLE_FPO_MODULES,
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


def js_coefficients(text=None):
    """The coefficients the port stress screen hard-codes, in the document's order."""
    text = text if text is not None else (config.get_project_root() / ORACLE_FPO_JS).read_text()
    m = re.search(r"_fpCoeffs\s*=\s*\{([^}]*)\}", text)
    if m is None:
        return None
    pairs = dict(re.findall(r"(\w+)\s*:\s*(-?[\d.]+)", m.group(1)))
    return [pairs.get(k) for k in "abcdef"]


def run(m):
    """Each family's worst error, code against reference."""
    poly, sens = m["poly"], m["sensitivity"]
    with mp.workdps(ORACLE_REFERENCE_DPS):
        cases = grid()
        out = {
            "poly": max(_err(poly.p_flood_poly(w, hr, s), ref.p_flood(w, hr, s)) for w, hr, s in cases),
            "zero_threshold": poly.p_flood_poly(5.0, 10, 0.0) == 0 and poly.p_flood_simple(5.0, 0.0) == 0,
            "series": max(abs(p - poly.p_flood_poly(w, hr, 6.58)) for hr, (w, p) in enumerate(
                zip(SERIES, poly.p_flood_series(SERIES, 6.58)))),
            "simple": max(_err(poly.p_flood_simple(w, s), ref.p_simple(w, s)) for w, _, s in cases),
            "copy": max(_err(sens.flood_probability(*map(float, ref.features(w, hr, s))), ref.p_flood(w, hr, s))
                        for w, hr, s in cases if w > 0),
            "slope": max(_err(sens.flood_probability_slope(*map(float, ref.features(w, hr, s))),
                              ref.slope(*ref.features(w, hr, s)))
                         for w, hr, s in cases if w > 0 and abs(ref.kernel(*ref.features(w, hr, s))) < 30),
        }
    js = js_coefficients()
    out["js"] = js == list(ORACLE_FPO_DOC_COEFFS) if js else False
    out["js_values"] = js
    return out
