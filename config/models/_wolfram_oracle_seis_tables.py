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

"""MKM-SEIS-001's sensitivity tables (``seismic_resilience.pdf`` v0.10, s7), as printed.

Each table is ``(number, title, rows)``; each row is ``(label, overrides,
figures)`` with ``figures`` a dict over median PGA (g), no-collapse (%), loss
frequency (%) and spread (bp), holding only what the table prints.
"""

from config.models._wolfram_oracle_seis import ORACLE_SEIS_BRI

_ZC = {"Very low": "None", "Low": "Low", "Moderate": "Medium", "High": "High", "Very high": "Extreme"}
_CONS = {"RC pre-code": "RC_PreCode", "Masonry URM": "Masonry_URM", "RC modern": "RC_Modern",
         "Steel MRF": "Steel_MRF"}
_SOIL = {"Rock (A)": (800.0, ()), "Stiff (B)": (450.0, ()), "Soft (D) no GS02": (150.0, ()),
         "Soft (D) GS02": (150.0, ("GS02",))}


def _grid(rows, cols, figures, over):
    return tuple((f"{r} / {c}", over(r, c), {"spread": x})
                 for r, line in zip(rows, figures) for c, x in zip(cols, line))


def _zone(z):
    return {"seismic_hazard_class": _ZC[z]}


ORACLE_SEIS_TABLES = (
    (3, "Distance", tuple(
        (f"{r} km", {"r_jb_km": float(r)}, {"pga": g, "no_collapse": n, "loss": lo, "spread": s})
        for r, g, n, lo, s in ((2, 0.1157, 93.1, 0.1228, 5.0), (5, 0.0835, 94.4, 0.0954, 4.0),
                               (10, 0.0520, 97.9, 0.0526, 1.5), (20, 0.0291, 100.0, 0.0151, 0.0),
                               (50, 0.0129, 100.0, 0.0088, 0.0), (100, 0.0068, 100.0, 0.0083, 0.0)))),
    (4, "Distance x construction", _grid(
        (2, 10, 20, 50), tuple(_CONS),
        ((5.0, 9.5, 3.5, 2.5), (1.5, 3.0, 0.0, 0.0), (0.0, 0.5, 0.0, 0.0), (0.0,) * 4),
        lambda r, c: {"r_jb_km": float(r), "construction_type": _CONS[c]})),
    (5, "Hazard zone", tuple(
        (z, _zone(z), {"no_collapse": n, "loss": lo, "spread": s})
        for z, n, lo, s in (("Very low", 100.0, 0.0012, 0.0), ("Low", 100.0, 0.0061, 0.0),
                            ("Moderate", 100.0, 0.0151, 0.0), ("High", 99.1, 0.1067, 2.5),
                            ("Very high", 99.4, 0.2868, 4.5)))),
    (6, "Zone x soil", _grid(
        ("Low", "Moderate", "High", "Very high"), tuple(_SOIL),
        ((0.0, 0.0, 0.0, 0.5), (0.0, 0.0, 2.5, 2.5), (2.0, 2.5, 9.5, 4.0), (5.0, 4.5, 33.0, 21.5)),
        lambda z, c: {**_zone(z), "soil_vs30_mps": _SOIL[c][0], "measures": _SOIL[c][1]})),
    (7, "BRI level, 5 km", tuple(
        (lv, {"measures": ORACLE_SEIS_BRI[lv], "r_jb_km": 5.0}, {"no_collapse": n, "loss": lo, "spread": s})
        for lv, n, lo, s in (("NR", 94.4, 0.0954, 4.0), ("B", 97.2, 0.0645, 2.0),
                             ("A", 99.3, 0.0445, 0.5), ("AA", 100.0, 0.0226, 0.0)))),
    (8, "Single measure, 5 km", tuple(
        (code or "None", {"measures": (code,) if code else (), "r_jb_km": 5.0},
         {"no_collapse": n, "spread": s})
        for code, n, s in ((None, 94.4, 4.0), ("GS08", 95.8, 3.0), ("GS09", 95.8, 3.0),
                           ("GS12", 97.2, 2.0), ("GS14", 95.1, 3.5), ("GS02", 94.4, 4.0)))),
    (9, "Zone x BRI", _grid(
        ("Very low", "Low", "Moderate", "High", "Very high"), ("NR", "B", "A", "AA"),
        ((0.0,) * 4, (0.0,) * 4, (0.0,) * 4, (2.5, 2.0, 2.0, 0.0), (4.5, 6.0, 3.5, 1.0)),
        lambda z, lv: {**_zone(z), "measures": ORACLE_SEIS_BRI[lv]})),
    (10, "Distance x BRI", _grid(
        (2, 10, 20, 50), ("NR", "B", "A", "AA"),
        ((5.0, 4.0, 2.0, 0.5), (1.5, 0.5, 0.0, 0.0), (0.0,) * 4, (0.0,) * 4),
        lambda r, lv: {"r_jb_km": float(r), "measures": ORACLE_SEIS_BRI[lv]})),
)
