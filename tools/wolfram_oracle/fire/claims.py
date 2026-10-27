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

"""FIRE-001's document, tested as stated (``fire_resilience.pdf`` v0.40).

* s7, Tables 1-12 -- the code reproduces every printed figure at the generator's
  seed, and every printed figure is the exact credit within sampling error.
* s7.1 -- the chain absorbs in about 3 steps; latent intensity climbs about 0.8 a step.
* Table 12, s8 -- a non-combustible frame with no effective suppression realises a
  sub-bp residual, "single-digit bps in very tall non-combustible assets".
* Table 2 -- the reach cliff, 203 bp, against the exact 1 - exp(-lambda), and the
  sampling error of the spread at the production draw count.
* Table 13 -- the construction levers, from the documented formulae.
* s3.3, s3.5 -- when suppression becomes active, and whether S6 is absorbing.
* Tables 4, 5, 9 -- condition, type and occupancy move only the ignition rate, so
  the containment rate they print differences in cannot depend on them.
"""

import mpmath as mp

from config.models import (
    ORACLE_FIRE_BASELINE,
    ORACLE_FIRE_CLAIM_ABSORB_STEPS,
    ORACLE_FIRE_CLAIM_GROWTH,
    ORACLE_FIRE_CLAIM_RESIDUAL_BPS,
    ORACLE_FIRE_LEVELS,
    ORACLE_FIRE_PRODUCTION_N_SIM,
    ORACLE_FIRE_TABLE13,
    ORACLE_FIRE_TALL_STOREYS,
    ORACLE_FIRE_Z_LIMIT,
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle.fire import exact
from tools.wolfram_oracle.fire.cases import METRICS, printed_match

_NON_COMBUSTIBLE = ("Reinforced concrete", "Concrete frame", "Steel frame", "Brick and block",
                    "Modern methods")


def _row(rows, cid):
    return next(r for r in rows if r["id"] == cid)


def _tall_residual(m):
    """The no-suppression residual of a reinforced-concrete frame at the tallest height."""
    cfg = m["config"]
    feat = {**ORACLE_FIRE_BASELINE, "construction_type": "Reinforced concrete",
            "number_of_storeys": ORACLE_FIRE_TALL_STOREYS, "suppression_systems_level": "Not assessed"}
    lam = m["initiation"].asset_lambda(m["features"](**feat), cfg.initiation)
    with mp.workdps(ORACLE_REFERENCE_DPS):
        ref = exact.profile(feat, cfg.progression, ORACLE_FIRE_LEVELS)
        c = exact.credit(ref, cfg.progression.transition_matrices, cfg.progression.race_jitter,
                         cfg.run.max_steps, lam, cfg.run.horizon_years)
    return float(c["spread_bps"])


def _table13(m):
    """How many of Table 13's printed levers the documented formulae reproduce, of how many."""
    prog = m["config"].progression
    hits = total = 0
    for ctype, gamma, scale, i_max, w_struct in ORACLE_FIRE_TABLE13:
        with mp.workdps(ORACLE_REFERENCE_DPS):
            ref = exact.profile({**ORACLE_FIRE_BASELINE, "construction_type": ctype}, prog,
                                ORACLE_FIRE_LEVELS)
            lo, hi = prog.construction["growth_combustibility_scale"]
            kappa = mp.mpf(prog.construction["structural_containment_weight"])
            got = (ref["combustibility"], lo + ref["combustibility"] * (hi - lo),
                   ref["intensity_ceiling"], min(max(kappa * (1 - ref["combustibility"]), 0), 1))
        for g, p in zip(got, (gamma, scale, i_max, w_struct)):     # printed to 3 s.f.
            hits += printed_match(float(g), p)
            total += 1
    return hits, total


def assess(rows, m):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    printed = [(r, k) for r in rows for k in METRICS if f"{k}_printed" in r]
    reproduced = sum(r[f"{k}_reproduced"] for r, k in printed)
    z_printed = max(abs(r[f"{k}_printed_z"]) for r, k in printed)
    base, none_ = _row(rows, "T1/Meets minimum"), _row(rows, "T1/Not assessed")
    cliff = _row(rows, "T2/12 storeys")
    residual = max(_row(rows, f"T12/{t}")["spread_bps_exact"] for t in _NON_COMBUSTIBLE)
    tall = _tall_residual(m)
    prog = m["config"].progression
    s6 = {k: v[6][7] for k, v in prog.transition_matrices.items() if not k.startswith("_")}
    levers = _table13(m)
    rate_only = [r for r in rows if r["table"] in (4, 5, 9)]       # inputs that move lambda only
    return [
        {"claim": "s7 tables reproduced", "reproduced": reproduced, "of": len(printed),
         "met": reproduced == len(printed)},
        {"claim": "s7 tables vs exact", "worst_z": z_printed, "met": z_printed <= ORACLE_FIRE_Z_LIMIT},
        {"claim": "s7.1 absorption", "exact": base["mean_steps"],
         "met": round(base["mean_steps"]) == ORACLE_FIRE_CLAIM_ABSORB_STEPS},
        {"claim": "s7.1 growth", "exact": base["growth"],
         "met": round(base["growth"], 1) == ORACLE_FIRE_CLAIM_GROWTH},
        {"claim": "T12 residual", "exact": residual, "met": residual < ORACLE_FIRE_CLAIM_RESIDUAL_BPS},
        {"claim": "T12 tall residual", "exact": tall, "storeys": ORACLE_FIRE_TALL_STOREYS,
         "met": tall >= ORACLE_FIRE_CLAIM_RESIDUAL_BPS},
        {"claim": "T2 cliff", "exact": cliff["spread_bps_exact"], "printed": cliff["spread_bps_printed"],
         "z": cliff["spread_bps_printed_z"], "production_se": cliff["spread_se_production"],
         "production_n": ORACLE_FIRE_PRODUCTION_N_SIM, "met": abs(cliff["spread_bps_printed_z"]) <= ORACLE_FIRE_Z_LIMIT},
        {"claim": "T13 levers", "reproduced": levers[0], "of": levers[1], "met": levers[0] == levers[1]},
        {"claim": "FIRE-L3 race", "race_lost": none_["pnr_step"], "recorded": none_["pnr_recorded"],
         "met": None},
        {"claim": "s3.5 S6 absorbing", "escalation": s6, "met": None},
        {"claim": "s3.3 suppression timing", "met": None},
        {"claim": "T4, T5, T9 containment", "exact_low": min(r["containment_exact"] for r in rate_only),
         "exact_high": max(r["containment_exact"] for r in rate_only),
         "printed_low": min(r["containment_printed"] for r in rate_only),
         "printed_high": max(r["containment_printed"] for r in rate_only), "met": None},
    ]
