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

"""The CSVs a run writes beside the document: every number behind its tables.

They stay in PhysicalRisk; the PDF is what is filed in ModelRisk.
"""

import csv


def _flat(row, skip=()):
    out = {}
    for k, v in row.items():
        if k in skip:
            continue
        if isinstance(v, dict):
            for T, d in v.items():
                for kk, vv in d.items():
                    out[f"x_{T}_{kk}"] = vv
        elif isinstance(v, (list, tuple)):
            for name, vv in zip(("xi", "loc", "scale"), v):
                out[f"{k.removesuffix('_xi_loc_scale')}_{name}"] = vv
        else:
            out[k] = v
    return out


def write_csv(path, rows, skip=()):
    flat = [_flat(r, skip) for r in rows]
    fields = list(dict.fromkeys(k for r in flat for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(flat)
