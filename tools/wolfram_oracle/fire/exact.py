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

"""FIRE-001's credit, exactly, from its document (``fire_resilience.pdf`` v0.40, s3).

Model C is evaluated from the formulae of s3.2 at 50 digits. For Models B and D,
the per-fire lognormal jitter of s3.3 makes the point-of-no-return (PNR) step a
random variable with an exact distribution: before suppression the intensity is
min(t g, C), so PNR latches at the first t with t g > I_crit, provided C > I_crit
and suppression has not bitten (t < detection + bite). Given that step k, the
chain marches the pre-PNR blend for steps 1..k-1 and the PNR matrix from k, and a
PNR is recorded only if the chain has not absorbed before step k. Summing over k
gives the outcome probabilities exactly; the model estimates them by Monte Carlo.
"""

import mpmath as mp

from config.models import ORACLE_REFERENCE_DPS

TERMINAL = (5, 6, 7)


def _lerp(lo, hi, f):
    f = min(max(f, mp.mpf(0)), mp.mpf(1))
    return mp.mpf(lo) + f * (mp.mpf(hi) - mp.mpf(lo))


def profile(feat, prog, levels):
    """Model C (s3.2): the quantities Models B and D consume."""
    idx = {lv: i for i, lv in enumerate(levels)}
    k = lambda lv: idx.get(lv, 0)          # unknown -> worst
    frac = lambda lv: mp.mpf(k(lv)) / (len(levels) - 1)
    worst = levels[0]

    def group(ranges, attrs):
        vals = [_lerp(*ranges[name], frac(feat[attr])) for name, attr in attrs]
        return mp.fsum(vals) / len(vals)

    passive = group(prog.passive_effectiveness_ranges, (
        ("StructuralFireResistanceAdequate", "structural_fire_resistance_level"),
        ("CompartmentsProvided", "compartments_level"),
        ("FireStoppingAtPenetrations", "fire_stopping_level"),
        ("ExternalMaterialsFireResistant", "external_materials_level")))
    response = group(prog.response_effectiveness_ranges, (
        ("AccessRouteResilient", "access_route_level"),
        ("EmergencyProceduresTested", "emergency_procedures_level"),
        ("BusinessContinuityPlanInPlace", "business_continuity_level")))
    sup = feat["suppression_systems_level"] or worst
    storeys = feat["number_of_storeys"] or 1
    timing, reach, cons = prog.timing, prog.fire_service_reach, prog.construction
    det = mp.mpf(timing["detection_base_steps"]) * mp.mpf(
        prog.detection_time_multiplier_by_level.get(feat["automatic_detection_level"] or worst, 1.0))
    pen = prog.upper_floor_penalty_per_storey
    p = _lerp(*pen["range"], mp.mpf(storeys - 1) / (pen["max_storeys"] - 1))
    reachable = k(sup) >= reach["internal_suppression_threshold"] or storeys <= reach["reach_storeys"]
    bite = (mp.mpf(timing["suppression_bite_base_steps"]) * p
            * mp.mpf(prog.suppression_bite_multiplier_by_level.get(sup, 1.0))
            if reachable else mp.mpf(reach["no_reach_bite_steps"]))
    gamma = mp.mpf(cons["combustibility_by_type"].get(feat.get("construction_type"),
                                                      cons["default_combustibility"]))
    thr = mp.mpf(cons["combustible_threshold"])
    q = (k(feat["compartments_level"]) + k(feat["fire_stopping_level"])) / mp.mpf(2)
    key = ("well_compartmented" if q >= prog.intensity_dynamics["compartmentation_well_threshold"]
           else "poorly_compartmented")
    g_base = mp.mpf(prog.growth_per_step_intensity[key]) * _lerp(*cons["growth_combustibility_scale"], gamma)
    g0 = max(g_base * (1 - mp.mpf(prog.intensity_dynamics["passive_damp_weight"]) * passive), mp.mpf(0))
    lo, hi = cons["intensity_ceiling"]
    ceiling = mp.mpf(lo) if gamma <= thr else _lerp(lo, hi, (gamma - thr) / (1 - thr))
    ctl = prog.controllability
    w = ctl["weights"]
    score = ((w["passive"] * passive + w["response"] * response + w["suppression"] * frac(sup))
             / (w["passive"] + w["response"] + w["suppression"]))
    w_active = _lerp(0, 1, (score - ctl["blend_floor"]) / (mp.mpf(ctl["blend_ceiling"]) - ctl["blend_floor"]))
    w_struct = _lerp(0, 1, mp.mpf(cons["structural_containment_weight"]) * (1 - gamma))
    return {"detection_steps": det, "suppression_bite_steps": bite, "growth": g0,
            "growth_per_step": g_base, "i_crit": mp.mpf(prog.i_crit_by_level.get(sup, prog.i_crit_by_level[worst])),
            "passive_effectiveness": passive, "response_effectiveness": response,
            "height_penalty": p, "controllability": score, "suppression_reachable": reachable,
            "combustibility": gamma, "intensity_ceiling": ceiling,
            "structure_combustible": gamma >= thr, "blend_weight": max(w_active, w_struct)}


def _phi(x):
    return mp.erfc(-x / mp.sqrt(2)) / 2


def _sf(x):
    """1 - Phi(x), from erfc so the upper tail keeps its digits."""
    return mp.erfc(x / mp.sqrt(2)) / 2


def _between(a, b):
    """Phi(b) - Phi(a), from whichever tail avoids cancellation (a < b)."""
    return _sf(a) - _sf(b) if a > 0 else _phi(b) - _phi(a)


def pnr_step_law(prof, jitter, max_steps):
    """P(PNR latches at step k), k = 1..max_steps (s3.3-3.4)."""
    if not prof["suppression_reachable"] and prof["structure_combustible"]:
        return [mp.mpf(1)] + [mp.mpf(0)] * (max_steps - 1)
    g0, ic, det, bite = prof["growth"], prof["i_crit"], prof["detection_steps"], prof["suppression_bite_steps"]
    if g0 <= 0:
        return [mp.mpf(0)] * max_steps
    sg, st, sc = (mp.mpf(jitter[k]) for k in ("growth_sigma", "timing_sigma", "ceiling_sigma"))
    z = lambda x: mp.log(x / g0) / sg                      # P(g' <= x) = Phi(z(x))
    ceil_ok = _sf(mp.log(ic / prof["intensity_ceiling"]) / sc)
    out = []
    for t in range(1, max_steps + 1):
        # floor(I_crit/g') + 1 == t, i.e. I_crit/t < g' <= I_crit/(t-1)
        grow = _sf(z(ic / t)) if t == 1 else _between(z(ic / t), z(ic / (t - 1)))
        room = t - det
        unbitten = 1 if room <= 0 else _sf(mp.log(room / bite) / st)
        out.append(grow * unbitten * ceil_ok)
    return out


def _step(v, m):
    return [mp.fsum(v[i] * m[i][j] for i in range(8)) for j in range(8)]


def _mul(a, b):
    return [_step(row, b) for row in a]


def _powers(m, n):
    """[m^0, m^1, ..., m^n]."""
    out = [[[mp.mpf(int(i == j)) for j in range(8)] for i in range(8)]]
    for _ in range(n):
        out.append(_mul(out[-1], m))
    return out


def _absorbing(m):
    return [[mp.mpf(int(i == j)) if i in TERMINAL else mp.mpf(x) for j, x in enumerate(row)]
            for i, row in enumerate(m)]


def outcome(prof, mats, jitter, max_steps):
    """Exact fire-conditional probabilities: contained, partial, total, unresolved,
    PNR recorded; and the mean steps to absorption without PNR."""
    w = prof["blend_weight"]
    pre = _absorbing([[w * mp.mpf(a) + (1 - w) * mp.mpf(b) for a, b in zip(ra, rb)]
                      for ra, rb in zip(mats["AA_controllable"], mats["weak_controllable"])])
    pnr = _absorbing(mats["point_of_no_return"])
    law = pnr_step_law(prof, jitter, max_steps)
    u = [[mp.mpf(1)] + [mp.mpf(0)] * 7]
    for _ in range(max_steps):
        u.append(_step(u[-1], pre))
    after = _powers(pnr, max_steps)                         # PNR matrix, j steps
    res = [mp.mpf(0)] * 8
    recorded = mp.mpf(0)
    for k in range(max_steps, 0, -1):
        if law[k - 1] == 0:
            continue
        v = _step(u[k - 1], after[max_steps - k + 1])
        res = [r + law[k - 1] * x for r, x in zip(res, v)]
        recorded += law[k - 1] * (1 - mp.fsum(u[k - 1][i] for i in TERMINAL))
    none = 1 - mp.fsum(law)
    res = [r + none * x for r, x in zip(res, u[-1])]
    mean_steps = mp.fsum(1 - mp.fsum(x[i] for i in TERMINAL) for x in u[:-1])
    return {"contained": res[5], "partial": res[6], "total": res[7],
            "unresolved": 1 - res[5] - res[6] - res[7], "pnr": recorded,
            "p_pnr_step": mp.fsum(law), "mean_steps": mean_steps}


def credit(prof, mats, jitter, max_steps, lam, horizon):
    """The resilience-credit currency of s3.6, exactly: the draw-level fire
    probability q = 1 - exp(-lambda h), then containment (fire-conditional), loss
    frequency and the spread (per draw)."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        o = outcome(prof, mats, jitter, max_steps)
        q = -mp.expm1(-mp.mpf(lam) * mp.mpf(horizon))
        return {**o, "q": q, "containment": o["contained"], "loss": q * (o["partial"] + o["total"]),
                "spread_bps": 10_000 * q * o["pnr"]}
