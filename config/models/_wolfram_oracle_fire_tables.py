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

"""MKM-FIRE-001's sensitivity tables (``fire_resilience.pdf`` v0.40, s7), as printed.

Each table is ``(number, title, base overrides, rows)``; each row is
``(label, overrides, containment %, loss frequency %, spread bps)``, with None
where the table does not print that metric. The generator varied one input at a
time about the baseline in ``_wolfram_oracle_fire``.
"""

_TYPES = ("Reinforced concrete", "Concrete frame", "Steel frame", "Brick and block",
          "Modern methods", "Mixed construction", "Timber frame")
_LV = ("Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified")
_SUP = _LV[1:]


def _one_way(field, values, figures, fmt=str):
    return tuple((fmt(v), {field: v}, *f) for v, f in zip(values, figures))


def _grid(row_field, rows, col_field, cols, figures, metric):
    out = []
    for r, line in zip(rows, figures):
        for c, x in zip(cols, line):
            cell = [None, None, None]
            cell[metric] = x
            out.append((f"{r} / {c}", {row_field: r, col_field: c}, *cell))
    return tuple(out)


ORACLE_FIRE_TABLES = (
    (1, "Suppression level", {}, _one_way("suppression_systems_level", _LV, (
        (47.0, 1.15, 8.5), (63.1, 0.75, 0.0), (66.7, 0.675, 0.0), (78.1, 0.445, 0.0),
        (86.8, 0.26, 0.0)))),
    (2, "Storeys, Partial suppression", {"suppression_systems_level": "Partial"},
     _one_way("number_of_storeys", (1, 3, 4, 5, 8, 12, 20), (
         (63.1, 0.75, 0.0), (63.1, 0.75, 0.0), (63.1, 0.75, 0.0), (0.0, 2.03, 203.0),
         (0.0, 2.03, 203.0), (0.0, 2.03, 203.0), (0.0, 2.03, 203.0)),
         fmt=lambda n: f"{n} storeys")),
    (3, "Compartmentation level", {}, _one_way("compartments_level", _LV, (
        (63.5, 0.74, 4.5), (63.5, 0.74, 5.0), (66.7, 0.675, 0.0), (66.0, 0.69, 0.0),
        (66.3, 0.685, 0.0)))),
    (4, "Property condition", {}, _one_way(
        "property_condition", ("Excellent", "Good", "Fair", "Poor", "Very poor"), (
            (68.3, 0.525, 0.0), (67.0, 0.625, 0.0), (66.7, 0.675, 0.0), (66.5, 0.79, 0.0),
            (64.6, 0.97, 0.0)))),
    (5, "Commercial type", {}, _one_way("commercial_type", (
        "Office", "Retail", "Hotel", "Leisure", "Healthcare", "MultiFamily", "MixedUse", "Other"), (
        (66.7, 0.675, 0.0), (64.6, 1.19, 0.0), (66.8, 1.43, 0.0), (66.4, 1.25, 0.0),
        (65.4, 0.975, 0.0), (64.0, 1.16, 0.0), (66.4, 1.52, 0.0), (66.4, 1.52, 0.0)))),
    (6, "Storeys x suppression: spread", {}, _grid(
        "number_of_storeys", (3, 5, 8, 20), "suppression_systems_level", _SUP,
        ((0.0,) * 4, (203.0, 0.0, 0.0, 0.0), (203.0, 0.0, 0.0, 0.0), (203.0, 0.0, 0.0, 0.0)), 2)),
    (7, "Construction, 12 storeys, Partial", {"number_of_storeys": 12,
                                              "suppression_systems_level": "Partial"},
     _one_way("construction_type", _TYPES, (
         (87.7, 0.25, 0.0), (83.5, 0.335, 0.0), (78.8, 0.43, 0.0), (78.8, 0.43, 0.0),
         (63.8, 0.735, 0.0), (0.0, 2.03, 203.0), (0.0, 2.03, 203.0)))),
    (8, "Detection level", {}, _one_way("automatic_detection_level", _LV, (
        (66.9, 0.715, 0.0), (66.7, 0.675, 0.0), (66.7, 0.675, 0.0), (66.7, 0.675, 0.0),
        (67.3, 0.645, 0.0)))),
    (9, "Occupancy", {}, _one_way(
        "occupancy_status", ("Fully occupied", "Partially vacant", "Vacant"), (
            (66.7, 0.675, 0.0), (67.3, 0.615, 0.0), (67.4, 0.575, 0.0)))),
    (10, "Construction x storeys: spread", {"suppression_systems_level": "Partial"}, _grid(
        "construction_type", (_TYPES[0], _TYPES[2], _TYPES[4], _TYPES[5], _TYPES[6]),
        "number_of_storeys", (3, 5, 8, 20),
        ((0.0,) * 4, (0.0,) * 4, (0.0,) * 4, (0.0, 203.0, 203.0, 203.0),
         (3.5, 203.0, 203.0, 203.0)), 2)),
    (11, "Construction x suppression: containment", {"number_of_storeys": 12}, _grid(
        "construction_type", (_TYPES[0], _TYPES[2], _TYPES[4], _TYPES[5], _TYPES[6]),
        "suppression_systems_level", _SUP,
        ((87.7, 87.7, 87.7, 87.1), (78.8, 78.8, 78.8, 86.8), (63.8, 66.7, 78.1, 86.8),
         (0.0, 66.7, 78.1, 86.8), (0.0, 66.5, 78.1, 86.8)), 0)),
    (12, "Construction, 12 storeys, no suppression", {
        "number_of_storeys": 12, "suppression_systems_level": "Not assessed"},
     _one_way("construction_type", _TYPES, (
         (87.5, 0.27, 0.0), (83.3, 0.36, 0.0), (78.7, 0.46, 0.0), (78.7, 0.46, 0.0),
         (63.9, 0.78, 0.0), (0.0, 2.16, 216.0), (0.0, 2.16, 216.0)))),
)

# Table 13, the deterministic config explainer: (type, gamma, growth scale, I_max,
# w_struct), to the precision printed.
ORACLE_FIRE_TABLE13 = (
    ("Reinforced concrete", 0.0, 0.5, 5.0, 1.0), ("Concrete frame", 0.05, 0.55, 5.0, 0.95),
    ("Steel frame", 0.1, 0.6, 5.0, 0.9), ("Brick and block", 0.1, 0.6, 5.0, 0.9),
    ("Modern methods", 0.25, 0.75, 5.0, 0.75), ("Mixed construction", 0.5, 1.0, 37.9, 0.5),
    ("Timber frame", 1.0, 1.5, 120.0, 0.0),
)
