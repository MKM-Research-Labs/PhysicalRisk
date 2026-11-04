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
"""Fit the v2.0 coefficients and report them with their held-out accuracy."""

import argparse
import json

from config.models import flood_poly_fit_storms
from tools.flood_poly_fit import fit as f


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.flood_poly_fit")
    ap.add_argument("--storms", type=int, default=flood_poly_fit_storms)
    ap.add_argument("--out", help="write the result as JSON here")
    args = ap.parse_args(argv)
    h, t, g, gauge, is_fit = f.states(args.storms)
    coeffs, min_slope = f.fit(h[is_fit], t[is_fit], g[is_fit])
    result = {"coefficients": [round(float(x), 6) for x in coeffs], "min_dz_dh": min_slope,
              "fit_states": int(is_fit.sum()), "test_states": int((~is_fit).sum()),
              "test": f.metrics(coeffs, h[~is_fit], t[~is_fit], g[~is_fit], gauge[~is_fit])}
    text = json.dumps(result, indent=1)
    if args.out:
        open(args.out, "w").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
