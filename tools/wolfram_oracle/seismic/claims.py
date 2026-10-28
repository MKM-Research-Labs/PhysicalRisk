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

"""SEIS-001's document, tested as stated (``seismic_resilience.pdf`` v0.10).

* s7, Tables 3-10 -- the code reproduces every printed figure at the generator's
  seed, and every printed figure is the exact credit within sampling error.
* Table 2 -- the six acceptance gates, on the exact credit rather than on draws.
* s7 -- printed orderings against the exact ones along each swept axis.
* s9.6 -- "stability is adequate at n_sim = 20,000".
* Table 18 -- the stated mean losses of DS0-DS2, and "truncated" lognormals.
* s3.3 -- the GMPE's functional form.
"""

import mpmath as mp

from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SEIS_BASELINE,
    ORACLE_SEIS_BRI,
    ORACLE_SEIS_CLAIM_FLOOR_BPS,
    ORACLE_SEIS_CLAIM_MEAN_LOSS,
    ORACLE_SEIS_FLOOR_CELL,
    ORACLE_SEIS_KM_PER_DEG,
    ORACLE_SEIS_PRODUCTION_N_SIM,
    ORACLE_SEIS_STABLE_REL_SE,
    ORACLE_SEIS_Z_LIMIT,
)
from tools.wolfram_oracle.seismic import exact
from tools.wolfram_oracle.seismic.cases import METRICS

_ZONES = ("Very low", "Low", "Moderate", "High", "Very high")


def _col(rows, table, key, labels, suffix=""):
    by = {r["label"]: r for r in rows if r["table"] == table}
    return [by[f"{lab}{suffix}"][key] for lab in labels]


def _monotone(xs, up):
    return all((b >= a) if up else (b <= a) for a, b in zip(xs, xs[1:]))


def _gates(rows, m):
    sp = "spread_exact"
    with mp.workdps(ORACLE_REFERENCE_DPS):
        floor = 10_000 * exact.credit({**ORACLE_SEIS_BASELINE, **ORACLE_SEIS_FLOOR_CELL},
                                      m["config"], ORACLE_SEIS_KM_PER_DEG)["spread"]
    t9 = {r["label"]: r[sp] for r in rows if r["table"] == 9}
    return {
        "distance": _monotone(_col(rows, 3, sp, ("2 km", "5 km", "10 km", "20 km", "50 km", "100 km")), False),
        "intensity": _monotone(_col(rows, 5, sp, _ZONES), True),
        "res_nocollapse": _monotone(_col(rows, 7, "no_collapse_exact", ("NR", "B", "A", "AA")), True),
        "res_spread": _monotone(_col(rows, 7, sp, ("NR", "B", "A", "AA")), False),
        "interaction": t9["Very high / NR"] > t9["High / AA"] >= t9["Moderate / AA"],
        "floor": float(floor) < ORACLE_SEIS_CLAIM_FLOOR_BPS, "floor_bps": float(floor),
    }


def _reversals(rows):
    """Adjacent printed pairs along a swept axis whose order contradicts the exact one."""
    out = []
    by_table = {}
    for r in rows:
        by_table.setdefault(r["table"], []).append(r)
    for table, rs in by_table.items():
        lines = {}
        for r in rs:
            head, _, tail = r["label"].partition(" / ")
            lines.setdefault(("row", head) if tail else ("one", ""), []).append(r)
            if tail:
                lines.setdefault(("col", tail), []).append(r)
        for line in lines.values():
            for a, b in zip(line, line[1:]):
                for k in ("spread", "no_collapse"):
                    if f"{k}_printed" not in a or f"{k}_printed" not in b:
                        continue
                    de, dp = b[f"{k}_exact"] - a[f"{k}_exact"], b[f"{k}_printed"] - a[f"{k}_printed"]
                    if de * dp < 0:
                        out.append((a["id"], b["id"], k))
    return out


def _table18(cfg):
    lg = cfg.fragility.loss_given_damage_state
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return {ds: float(exact.clipped_mean(mp.mpf(lg[ds]["mean"]), mp.mpf(lg[ds]["logstd"])))
                for ds in ORACLE_SEIS_CLAIM_MEAN_LOSS}


def assess(rows, m):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    printed = [(r, k) for r in rows for k in METRICS if f"{k}_printed" in r]
    reproduced = sum(r[f"{k}_reproduced"] for r, k in printed)
    z = max(abs(r[f"{k}_printed_z"]) for r, k in printed)
    gates = _gates(rows, m)
    live = [r for r in rows if r["spread_exact"] >= 1.0]
    worst = max(live, key=lambda r: r["spread_se"] / r["spread_exact"])
    means = _table18(m["config"])
    prod = max(rows, key=lambda r: r["spread_se_production"])
    return [
        {"claim": "s7 tables reproduced", "reproduced": reproduced, "of": len(printed),
         "met": reproduced == len(printed)},
        {"claim": "s7 tables vs exact", "worst_z": z, "met": z <= ORACLE_SEIS_Z_LIMIT},
        {"claim": "Table 2 gates", **gates, "met": all(v for k, v in gates.items() if k != "floor_bps")},
        {"claim": "s7 orderings", "reversals": _reversals(rows), "met": None},
        {"claim": "s9.6 stability", "worst_rel_se": worst["spread_se"] / worst["spread_exact"],
         "at": worst["id"], "exact": worst["spread_exact"], "se": worst["spread_se"],
         "met": worst["spread_se"] / worst["spread_exact"] <= ORACLE_SEIS_STABLE_REL_SE},
        {"claim": "production spread", "at": prod["id"], "exact": prod["spread_exact"],
         "se": prod["spread_se_production"], "n": ORACLE_SEIS_PRODUCTION_N_SIM, "met": None},
        {"claim": "Table 18 means", "stated": ORACLE_SEIS_CLAIM_MEAN_LOSS, "exact": means,
         "met": all(abs(means[k] - v) <= 0.005 for k, v in ORACLE_SEIS_CLAIM_MEAN_LOSS.items())},
        {"claim": "s3.3 GMPE form", "met": None},
    ]
