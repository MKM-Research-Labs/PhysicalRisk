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

"""GHD-001's document, tested as stated (``gaugehd_synthetic.pdf`` v1.0).

* s7.1(1) -- the lag-1 autocorrelation of a non-tidal series is about phi = 0.85.
* s7.1(3), s8.4 -- days above FloodAlert about 6 max(n3, 1); single-day flood spikes.
* s5.6 -- January and July means about A_s above and below the annual mean.
* s4.5 -- each history reproduces the observed severe-event frequency.
* s5.4, s7.3 -- regeneration is byte-identical, from seed = hash(gauge_id) mod 2^32.
* s6.1 -- lag-7 autocorrelations of 0.32 and 0.028.
* s3.5 -- the spring-neap phase, taken from the day of the year.
"""

import os
import subprocess
import sys

from config.models import (
    ORACLE_GHD_CLAIM_ALERT_PER_EVENT,
    ORACLE_GHD_CLAIM_LAG1,
    ORACLE_GHD_CLAIM_LAG7,
    ORACLE_GHD_CLAIM_SEASONAL_TOL,
    ORACLE_GHD_N3_WINDOW_YEARS,
    ORACLE_GHD_SPRING_NEAP,
    ORACLE_GHD_TABLE1,
    ORACLE_GHD_THRESHOLDS,
    ORACLE_GHD_YEARS,
)


def _hash_in_fresh_process(text, hashseed):
    env = {**os.environ, "PYTHONHASHSEED": str(hashseed)}
    out = subprocess.run([sys.executable, "-c", f"print(hash({text!r}) % (2**32))"],
                         capture_output=True, text=True, env=env, check=True)
    return int(out.stdout.strip())


def assess(rows):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    by = {r["id"]: r for r in rows}
    nt0, nt8 = by["Non-tidal/n3=0"], by["Non-tidal/n3=8"]
    per_event = {r["regime"]: r["days_FloodAlert_exact"] / r["floods_exact"] for r in rows if r["n3"] == 8}
    seasonal = []
    for r in rows:
        a_s = ORACLE_GHD_TABLE1[r["regime"]][1] * r["mu0_mean"]
        seasonal += [r["jan_minus_mean_exact"] / a_s, -r["jul_minus_mean_exact"] / a_s]
    seeds = [_hash_in_fresh_process("GAUGE-0001", s) for s in (1, 2)]
    lag7 = [(phi, stated, phi ** 7) for phi, stated in ORACLE_GHD_CLAIM_LAG7]
    jump = 365 % ORACLE_GHD_SPRING_NEAP
    return [
        {"claim": "s7.1 lag-1", "stated": ORACLE_GHD_CLAIM_LAG1, "flood_free": nt0["lag1_flood_free"],
         "model": [nt0["lag1_model"], nt8["lag1_model"]],
         "met": abs(nt0["lag1_flood_free"] - ORACLE_GHD_CLAIM_LAG1) <= 0.05},
        {"claim": "s7.1 alert days", "stated": [6 * max(r["n3"], 1) for r in (nt0, nt8)],
         "exact": [r["days_FloodAlert_exact"] for r in (nt0, nt8)],
         "met": all(abs(r["days_FloodAlert_exact"] / (6 * max(r["n3"], 1)) - 1) <= 0.25 for r in (nt0, nt8))},
        {"claim": "s8.4 single-day spikes", "per_event": per_event,
         "met": all(v <= ORACLE_GHD_CLAIM_ALERT_PER_EVENT + 0.25 for v in per_event.values())},
        {"claim": "s5.6 seasonal means", "low": min(seasonal), "high": max(seasonal),
         "met": all(abs(x - 1) <= ORACLE_GHD_CLAIM_SEASONAL_TOL for x in seasonal)},
        {"claim": "s4.5 severe frequency", "observed_per_5y": 8,
         "model_per_5y": 8 * ORACLE_GHD_N3_WINDOW_YEARS / ORACLE_GHD_YEARS,
         "factor": ORACLE_GHD_YEARS / ORACLE_GHD_N3_WINDOW_YEARS, "met": False},
        {"claim": "s5.4 reproducibility", "seeds": seeds, "met": seeds[0] == seeds[1]},
        {"claim": "s6.1 lag-7", "values": lag7, "met": all(round(v, len(str(s).split(".")[1])) == s
                                                          for _, s, v in lag7)},
        {"claim": "s3.5 spring-neap phase", "jump_days": jump, "met": None},
        {"claim": "s7.2 mean below alert", "worst": max(r["mean_exact"] for r in rows),
         "alert": ORACLE_GHD_THRESHOLDS["FloodAlert"],
         "met": max(r["mean_exact"] for r in rows) < ORACLE_GHD_THRESHOLDS["FloodAlert"]},
    ]
