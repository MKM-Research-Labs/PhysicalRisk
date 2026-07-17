#!/usr/bin/env python3

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

"""Stage 8 β-sensitivity analysis for the halong coupled PRS study.

Reads the per-β snapshots written by ``beta_sweep_halong.sh`` under
``data/input/halong/.beta_study/beta_<β>/`` and reports, for each β:

  * Upper-tail dependence λ_U — the share of high-severity storms (top quantile
    of the storm severity latent) whose paired typhoon is also high-wind. This
    is the quantity β controls (the coupling floor pull), and the user's chosen
    anchor for picking β.
  * PRS pricing — portfolio mean/median of the four peril spreads
    (flood / wind / flood-OR-wind union / flood-AND-wind joint), in bps.
  * Basis — the incremental wind leg the loan coupon now charges
    (union − flood), i.e. how much combined-peril pricing moves the spread
    above flood-only.

The flood leg is β-invariant (β only moves typhoon genesis), so it is reported
once as a baseline; everything wind/union/joint moves with β.

Usage:
    python scripts/beta_sweep_analyze.py            # betas 0.3 0.5 0.7
    python scripts/beta_sweep_analyze.py 0.3 0.5 0.7
"""

import glob
import json
import os
import statistics as st
import sys

STUDY = "data/input/halong/.beta_study"


def _ranks_to_quantiles(values):
    """Average-rank quantiles q_i = rank(x_i)/(n+1), ties averaged."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-based average rank
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return [r / (n + 1) for r in ranks]


def load_event_table(beta_dir):
    """Join storm severity latent (base_intensity → quantile q) with the
    paired typhoon peak wind (peak_v_max_ms), keyed by event_id.

    Returns list of dicts {event_id, q, vmax} for events present in both.
    """
    # Storm severity latents live in the shared (β-independent) sequences file.
    seqs_path = "data/input/halong/storm_sequences.json"
    with open(seqs_path) as f:
        sd = json.load(f)
    seqs = None
    if isinstance(sd, dict):
        for v in sd.values():
            if isinstance(v, list):
                seqs = v
                break
    elif isinstance(sd, list):
        seqs = sd
    base_by_id = {
        s["event_id"]: s["base_intensity"]
        for s in (seqs or [])
        if s.get("event_id") and "base_intensity" in s
    }

    vmax_by_id = {}
    for fp in glob.glob(os.path.join(beta_dir, "events", "*.json")):
        with open(fp) as f:
            ev = json.load(f)
        eid = ev.get("event_id")
        summ = ev.get("summary", {}) or {}
        vm = summ.get("peak_v_max_ms")
        if eid and vm is not None:
            vmax_by_id[eid] = vm

    ids = [e for e in base_by_id if e in vmax_by_id]
    ids.sort()
    bases = [base_by_id[e] for e in ids]
    qs = _ranks_to_quantiles(bases)
    return [{"event_id": e, "q": q, "vmax": vmax_by_id[e]}
            for e, q in zip(ids, qs)]


def upper_tail_dependence(rows, t=0.90):
    """λ_U(t) = P(Vmax-rank > t | q > t): share of top-(1-t) severity storms
    whose paired typhoon is also in the top-(1-t) of peak wind."""
    n = len(rows)
    if n == 0:
        return float("nan"), 0
    vmaxes = [r["vmax"] for r in rows]
    vq = _ranks_to_quantiles(vmaxes)
    hi_sev = [i for i in range(n) if rows[i]["q"] > t]
    if not hi_sev:
        return float("nan"), 0
    both = sum(1 for i in hi_sev if vq[i] > t)
    return both / len(hi_sev), len(hi_sev)


def peril_spreads(propertyhc_path):
    """Collect per-property peril spreads (bps) from prs_perils."""
    with open(propertyhc_path) as f:
        hc = json.load(f)
    curves = hc.get("property_hazard_curves", hc)
    out = {"flood": [], "wind": [], "union": [], "joint": [], "incr_wind": []}
    for pc in curves.values():
        if not isinstance(pc, dict):
            continue
        perils = pc.get("prs_perils")
        if not perils:
            continue
        f = perils.get("flood_only", {}).get("spread_bps", 0.0)
        w = perils.get("wind_only", {}).get("spread_bps", 0.0)
        u = perils.get("flood_or_wind", {}).get("spread_bps", 0.0)
        j = perils.get("flood_and_wind", {}).get("spread_bps", 0.0)
        out["flood"].append(f)
        out["wind"].append(w)
        out["union"].append(u)
        out["joint"].append(j)
        out["incr_wind"].append(max(0.0, u - f))  # the loan's wind leg
    return out


def _mean(xs):
    return st.mean(xs) if xs else float("nan")


def _median(xs):
    return st.median(xs) if xs else float("nan")


def main():
    betas = sys.argv[1:] or ["0.3", "0.5", "0.7"]
    print(f"\n{'='*78}")
    print("Stage 8 — β coupling-strength sensitivity (halong, coupled PRS)")
    print(f"{'='*78}")

    rows_hdr = (f"{'β':>5} {'λ_U(.90)':>9} {'n_tail':>7} "
                f"{'union μ':>9} {'wind μ':>8} {'joint μ':>8} "
                f"{'incrWind μ':>11} {'union med':>10}")
    print("\nPRS pricing & upper-tail dependence (spreads in bps):")
    print(rows_hdr)
    print("-" * len(rows_hdr))

    flood_baseline = None
    for b in betas:
        bdir = os.path.join(STUDY, f"beta_{b}")
        hc_path = os.path.join(bdir, "propertyhc.json")
        if not os.path.exists(hc_path):
            print(f"{b:>5}  (missing snapshot at {bdir})")
            continue
        rows = load_event_table(bdir)
        lam, n_tail = upper_tail_dependence(rows, t=0.90)
        ps = peril_spreads(hc_path)
        if flood_baseline is None:
            flood_baseline = _mean(ps["flood"])
        print(f"{b:>5} {lam:>9.3f} {n_tail:>7d} "
              f"{_mean(ps['union']):>9.1f} {_mean(ps['wind']):>8.1f} "
              f"{_mean(ps['joint']):>8.1f} {_mean(ps['incr_wind']):>11.1f} "
              f"{_median(ps['union']):>10.1f}")

    print(f"\nFlood leg (β-invariant baseline): mean {flood_baseline:.1f} bps")
    print("\nReading: λ_U rises with β (stronger comonotone pull → high-rain")
    print("storms paired with high-wind typhoons). 'incrWind μ' is the mean")
    print("incremental wind spread the loan coupon now charges on top of flood")
    print("(union − flood); it is the combined-peril basis over flood-only.\n")


if __name__ == "__main__":
    main()
