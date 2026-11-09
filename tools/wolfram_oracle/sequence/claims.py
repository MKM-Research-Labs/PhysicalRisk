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

"""SS-001's model document, tested as stated (``storm_multi_v3.1.pdf``, v3.1): what the model does.

Its parameter tables are read from the code's configuration. Its figures -- the type
breakdown (Table 9), the cap rate (s6.2), the shortening rates (s6.3) and Q6's thresholds, the intensity
correlation (Table 8) -- are judged against the exact law the tables imply, which the
Monte Carlo shows the code draws from. What the repository holds is judged in ``evidence``.
"""

from fractions import Fraction as Q

from tools.wolfram_oracle.sequence import reference as ref

import config.port as port
from config.models import (
    ORACLE_SS_BASE,
    ORACLE_SS_CAP_ALL_PCT,
    ORACLE_SS_CAP_TOL,
    ORACLE_SS_CAP_WORST,
    ORACLE_SS_CORR_PROB,
    ORACLE_SS_COUNT,
    ORACLE_SS_COUNTS,
    ORACLE_SS_DRAIN_H,
    ORACLE_SS_DURATION,
    ORACLE_SS_GAP,
    ORACLE_SS_PBASE,
    ORACLE_SS_PBASE_FALLBACK,
    ORACLE_SS_PINNED_PCT,
    ORACLE_SS_Q6_CAP_PCT,
    ORACLE_SS_Q6_SHORT_PCT,
    ORACLE_SS_SCALE_STATED,
    ORACLE_SS_SEQ_PROB,
    ORACLE_SS_SHORT_BY_TYPE,
    ORACLE_SS_SHORTENED_PCT,
    ORACLE_SS_SUBSEQUENT_STATED,
    ORACLE_SS_TABLE9,
    ORACLE_SS_TABLE9_PCT,
    ORACLE_SS_TYPE_WEIGHTS,
    ORACLE_SS_VARIATION,
    ORACLE_SS_WEIGHTS,
    ORACLE_SS_WINDOW_H,
)

TYPES = ("isolated", "doublet", "cluster", "persistent")


def _floats(d):
    return {k: tuple(float(x) for x in v) if isinstance(v, (list, tuple)) else float(v) for k, v in d.items()}


def parameters():
    """Eq. 4 and Tables 1-6, 8: the parameters in config.port are the document's."""
    weights = {c: port.SEQUENCE_TYPE_WEIGHTS.get(c, port.DEFAULT_TYPE_WEIGHTS) for c in ORACLE_SS_TYPE_WEIGHTS}
    counts = {t: (min(ns), max(ns)) for t, ns in ORACLE_SS_COUNTS.items()}
    checks = {
        "Table 1": {t: tuple(port.SEQUENCE_STORM_COUNTS[t]) for t in counts} == counts,
        "Eq. 4": _floats(port.SEQUENCE_PROBABILITY) == _floats(ORACLE_SS_SEQ_PROB),
        "Table 2": _floats(weights) == _floats(ORACLE_SS_TYPE_WEIGHTS),
        "Table 3": _floats(port.STORM_DURATION_PARAMS) == _floats(ORACLE_SS_DURATION),
        "Table 4": _floats({k: port.STORM_GAP_PARAMS[k] for k in ORACLE_SS_GAP}) == _floats(ORACLE_SS_GAP),
        "Table 5": _floats(port.BASE_INTENSITY_PARAMS) == _floats(ORACLE_SS_BASE),
        "Table 6": _floats(port.DEFAULT_INTENSITY_WEIGHTS) == _floats(ORACLE_SS_WEIGHTS),
        "Table 8": (port.EVENT_WINDOW_HOURS, port.MIN_DRAINAGE_WINDOW_HOURS, port.INTENSITY_VARIATION,
                    port.CORRELATION_PROB) == (ORACLE_SS_WINDOW_H, ORACLE_SS_DRAIN_H, float(ORACLE_SS_VARIATION),
                                               float(ORACLE_SS_CORR_PROB)),
    }
    return {"differ": [k for k, ok in checks.items() if not ok], "met": all(checks.values())}


def whole_hours(replay):
    """Eq. 5, Eq. 8: durations and raw gaps are whole hours; a capped duration takes the cap."""
    seqs = replay["batch"] + replay["forced"]
    durs = [s.duration_hours for q in seqs for s in q.storms
            if abs(s.duration_hours - float(ref.cap_of(q.sequence_type, q.num_storms))) >= ORACLE_SS_CAP_TOL]
    whole = sum(float(x).is_integer() for x in durs)
    return {"durations": len(durs), "whole": whole, "met": whole == len(durs)}


def window(replay):
    """s3.1, s3.4.1, s3.5.1: every sequence ends by W_P, leaving at least 12 h to drain."""
    seqs = replay["batch"] + replay["forced"]
    end = max(q.storms[-1].start_time_hours + q.storms[-1].duration_hours for q in seqs)
    drain = min(q.drainage_window_hours for q in seqs)
    return {"end": end, "drain": drain, "met": end <= ref.W_P + 1e-9 and drain >= ORACLE_SS_DRAIN_H - 1e-9}


def recovery(replay, exact, mc):
    """s3.5, Table 4: every gap is at least its type's minimum, 6 h short or 24 h medium; every
    storm is capped, holding every gap at that minimum, in 3.1% of multi-storm sequences."""
    seqs = [q for q in replay["batch"] + replay["forced"] if q.num_storms > 1]
    least = {t: min(min(q.inter_storm_gaps_hours) for q in seqs if q.sequence_type == t) for t in ref.MULTI}
    pct = 100 * float(exact["pinned_share"])
    ok = all(least[t] >= ref.g_min(t) - 1e-9 for t in ref.MULTI)
    return {"least": least, "pinned": pct, "seen": 100 * mc["pinned"] / mc["multi"],
            "met": ok and round(pct, 1) == ORACLE_SS_PINNED_PCT}


def correlation(replay):
    """Table 8: a subsequent storm is at least as strong as the first with probability 0.85."""
    exact = ref.subsequent_vs_first()
    pairs = [(q.storms[0].intensity_factor, s.intensity_factor) for q in replay["batch"] for s in q.storms[1:]]
    seen = sum(b >= a for a, b in pairs) / len(pairs)
    return {"exact": float(exact), "seen": seen, "storms": len(pairs), "eq13": float(ORACLE_SS_CORR_PROB),
            "met": exact == Q(ORACLE_SS_SUBSEQUENT_STATED)}


def precipitation(code):
    """Table 7: P_base is each catchment's storm module's (Thames 35, Mekong 90, Ha Long
    100 mm); a catchment with no storm module takes the Thames's 35 mm."""
    got = {c: code.seq._load_base_precipitation(c) for c in ORACLE_SS_PBASE}
    name, fallback = ORACLE_SS_PBASE_FALLBACK
    got_fallback = code.seq._load_base_precipitation(name)
    return {"got": got, "fallback": got_fallback, "met": got == ORACLE_SS_PBASE and got_fallback == fallback}


def table9(exact):
    """s6.1, Table 9: the default batch's expected type counts, to the nearest sequence."""
    counts = {t: float(exact["types"][t]) * ORACLE_SS_COUNT for t in TYPES}
    return {"exact": counts, "met": all(round(counts[t]) == ORACLE_SS_TABLE9[t] for t in TYPES)}


def seeds(mc):
    """s7.2: pooled over 100 seeds of 10,000, every type is within 1% of Table 9."""
    worst = max(abs(mc["pooled"][t] / mc["seeds"] - ORACLE_SS_TABLE9[t]) / ORACLE_SS_TABLE9[t] for t in TYPES)
    per_seed = max(abs(p[t] - ORACLE_SS_TABLE9[t]) / ORACLE_SS_TABLE9[t] for p in mc["per_seed"] for t in TYPES)
    return {"seeds": mc["seeds"], "worst_pct": 100 * worst, "per_seed_pct": 100 * per_seed,
            "met": 100 * worst <= ORACLE_SS_TABLE9_PCT}


def cap(exact):
    """s6.2: the cap never binds on an isolated storm; it binds most often on catastrophic
    durations in a persistent sequence, 77.7%; and on 8.6% of all draws."""
    cat, t, n, stated = ORACLE_SS_CAP_WORST
    configs = [(c, tt, nn) for c in ORACLE_SS_WEIGHTS for tt, ns in ORACLE_SS_COUNTS.items() for nn in ns]
    worst = max(configs, key=lambda x: ref.capped(*x))
    isolated = max(100 * float(ref.capped(c, "isolated", 1)) for c in ORACLE_SS_WEIGHTS)
    pct, share = 100 * float(ref.capped(cat, t, n)), 100 * float(exact["cap_share"])
    return {"worst": pct, "share": share, "isolated": isolated,
            "met": worst == (cat, t, n) and round(pct, 1) == stated and isolated == 0
            and round(share, 1) == ORACLE_SS_CAP_ALL_PCT}


def thresholds(exact):
    """Q6: at the baseline, the cap rate is within 50% and every type's shortening rate within
    70%: doublet 0.8%, cluster 52.3%, persistent 47.9%."""
    by_type = {t: 100 * float(ref.compressed(ORACLE_SS_WEIGHTS, tuple(ORACLE_SS_WEIGHTS), t)) for t in ref.MULTI}
    within = 100 * float(exact["cap_share"]) <= ORACLE_SS_Q6_CAP_PCT and max(by_type.values()) <= ORACLE_SS_Q6_SHORT_PCT
    return {"by_type": by_type, "within": within,
            "met": within and all(round(by_type[t], 1) == ORACLE_SS_SHORT_BY_TYPE[t] for t in ref.MULTI)}


def scaling(exact):
    """s6.3: gaps are shortened in 35.4% of multi-storm sequences; in 4.7% of
    moderate-to-severe persistent sequences and 99.7% of catastrophic ones."""
    allp = 100 * float(exact["compressed_share"])
    ms = 100 * float(ref.compressed(ORACLE_SS_WEIGHTS, ("moderate", "severe"), "persistent"))
    cat = 100 * float(ref.compressed(ORACLE_SS_WEIGHTS, ("catastrophic",), "persistent"))
    stated = list(ORACLE_SS_SCALE_STATED.values())
    return {"all": allp, "modsev": ms, "cat": cat,
            "met": round(allp, 1) == ORACLE_SS_SHORTENED_PCT and round(ms, 1) == stated[0]
            and round(cat, 1) == stated[1]}


def reproducible(code, replay):
    """s5.3: a fixed seed reproduces the batch exactly (identifiers and timestamps aside)."""
    again = code.batch.generate_event_set(len(replay["batch"]), seed=replay["seed"])

    def nums(q):
        return ([q.sequence_type, q.intensity_category, *q.inter_storm_gaps_hours]
                + [(s.start_time_hours, s.duration_hours, s.intensity_factor, s.peak_position) for s in q.storms])
    same = all(nums(a) == nums(b) for a, b in zip(replay["batch"], again))
    return {"met": same}


def assess(code, replay, mc, exact):
    return {
        "parameters": parameters(),
        "whole": whole_hours(replay),
        "window": window(replay),
        "recovery": recovery(replay, exact, mc),
        "correlation": correlation(replay),
        "precipitation": precipitation(code),
        "table9": table9(exact),
        "seeds": seeds(mc),
        "cap": cap(exact),
        "scaling": scaling(exact),
        "thresholds": thresholds(exact),
        "reproducible": reproducible(code, replay),
    }
