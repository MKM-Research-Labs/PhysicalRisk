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

"""SS-001's model document, tested as stated (``storm_multi.pdf``, v2.0): what the model does.

Its parameter tables are read from the code. Its figures -- the type breakdown (Table 9),
the cap rate (s6.2), the gap-scaling rates (s6.3), the intensity correlation (Table 8) --
are judged against the exact law the tables imply, which the Monte Carlo shows the code
draws from. What the repository holds is judged in ``evidence``.
"""

from fractions import Fraction as Q

from tools.wolfram_oracle.sequence import reference as ref

import config.port as port
from config.models import (
    ORACLE_SS_BASE,
    ORACLE_SS_CAP_ALL_PCT,
    ORACLE_SS_CAP_CAT5_PCT,
    ORACLE_SS_CORR_PROB,
    ORACLE_SS_COUNT,
    ORACLE_SS_DRAIN_H,
    ORACLE_SS_DURATION,
    ORACLE_SS_GAP,
    ORACLE_SS_PBASE,
    ORACLE_SS_SCALE_STATED,
    ORACLE_SS_SEQ_PROB,
    ORACLE_SS_SUBSEQUENT_STATED,
    ORACLE_SS_TABLE9,
    ORACLE_SS_TABLE9_PCT,
    ORACLE_SS_TYPE_WEIGHTS,
    ORACLE_SS_VARIATION,
    ORACLE_SS_WEIGHTS,
    ORACLE_SS_WINDOW_H,
)

TYPES = ("isolated", "doublet", "cluster", "persistent")


def parameters(code):
    """Eq. 4 and Tables 1-6: the code's parameters are the document's."""
    i, d, g, b = code.intensity, code.duration, code.gap, code.batch
    weights = {c: tuple(float(x) for x in i.SEQUENCE_TYPE_WEIGHTS.get(c, port.DEFAULT_TYPE_WEIGHTS))
               for c in ORACLE_SS_TYPE_WEIGHTS}
    gap = {k.name: tuple(v) for k, v in g.GAP_PARAMS.items() if k.name in ORACLE_SS_GAP}
    checks = {
        "Eq. 4": {c: float(p) for c, p in i.SEQUENCE_PROBABILITY.items()} == {c: float(p) for c, p in ORACLE_SS_SEQ_PROB.items()},
        "Table 2": weights == {c: tuple(float(x) for x in w) for c, w in ORACLE_SS_TYPE_WEIGHTS.items()},
        "Table 3": {c: tuple(v) for c, v in d.DURATION_PARAMS.items()} == ORACLE_SS_DURATION,
        "Table 4": gap == ORACLE_SS_GAP,
        "Table 5": {c: tuple(v) for c, v in b.BASE_INTENSITY_PARAMS.items()} == ORACLE_SS_BASE,
        "Table 6": {c: float(w) for c, w in port.DEFAULT_INTENSITY_WEIGHTS.items()} == {c: float(w) for c, w in ORACLE_SS_WEIGHTS.items()},
        "Table 8": (port.EVENT_WINDOW_HOURS, port.MIN_DRAINAGE_WINDOW_HOURS, port.INTENSITY_VARIATION,
                    port.CORRELATION_PROB) == (ORACLE_SS_WINDOW_H, ORACLE_SS_DRAIN_H, float(ORACLE_SS_VARIATION),
                                               float(ORACLE_SS_CORR_PROB)),
    }
    return {"differ": [k for k, ok in checks.items() if not ok], "met": all(checks.values())}


def continuous(replay):
    """Eq. 5 and s3.5: durations and gaps are triangular draws (the document does not round)."""
    durs = [s.duration_hours for q in replay["batch"] for s in q.storms if s.duration_hours != 156 / q.num_storms]
    gaps = [x for q in replay["batch"] for x in q.inter_storm_gaps_hours]
    whole = sum(float(x).is_integer() for x in durs)
    return {"durations": len(durs), "whole": whole, "gaps": len(gaps),
            "whole_gaps": sum(float(x).is_integer() for x in gaps), "met": whole < len(durs)}


def window(replay):
    """s3.1, s3.4.1, s3.5.1: every sequence ends by W_P, leaving at least 12 h to drain."""
    seqs = replay["batch"] + replay["forced"]
    end = max(q.storms[-1].start_time_hours + q.storms[-1].duration_hours for q in seqs)
    drain = min(q.drainage_window_hours for q in seqs)
    return {"end": end, "drain": drain, "met": end <= ref.W_P + 1e-9 and drain >= ORACLE_SS_DRAIN_H - 1e-9}


def recovery(exact, mc):
    """s3.5, Table 4: between storms, a gap of 6-36 h or 24-72 h lets the catchment drain.
    Judged as the share of multi-storm sequences whose gaps are left no room at all."""
    cat = ref.compressed(ORACLE_SS_WEIGHTS, ("catastrophic",), "persistent")
    return {"zero": float(exact["zero_share"]), "seen": mc["zero"] / mc["multi"],
            "compressed": float(exact["compressed_share"]), "cat_persistent": float(cat),
            "met": exact["zero_share"] == 0}


def correlation(replay):
    """Table 8: a subsequent storm is at least as strong as the first with probability 0.70."""
    exact = ref.subsequent_vs_first()
    pairs = [(q.storms[0].intensity_factor, s.intensity_factor) for q in replay["batch"] for s in q.storms[1:]]
    seen = sum(b >= a for a, b in pairs) / len(pairs)
    return {"exact": float(exact), "seen": seen, "storms": len(pairs), "eq13": float(ORACLE_SS_CORR_PROB),
            "met": exact == Q(ORACLE_SS_SUBSEQUENT_STATED)}


def precipitation(code):
    """Table 7: P_base is 35, 40, 45 and 55 mm for the Thames, Rhine, Danube and Mississippi."""
    got = {c: code.seq._load_base_precipitation(c) for c in ORACLE_SS_PBASE}
    return {"got": got, "met": got == ORACLE_SS_PBASE}


def table9(exact):
    """s6.1, Table 9: the default batch's expected type counts (to the nearest hundred)."""
    counts = {t: float(exact["types"][t]) * ORACLE_SS_COUNT for t in TYPES}
    return {"exact": counts, "met": all(round(counts[t], -2) == ORACLE_SS_TABLE9[t] for t in TYPES)}


def seeds(mc):
    """s7.2: over 100 seeds of 10,000, every type is within 2% of Table 9."""
    worst = max(abs(p[t] - ORACLE_SS_TABLE9[t]) / ORACLE_SS_TABLE9[t] for p in mc["per_seed"] for t in TYPES)
    return {"seeds": mc["seeds"], "worst_pct": 100 * worst, "met": 100 * worst <= ORACLE_SS_TABLE9_PCT}


def cap(exact):
    """s6.2: ~99% of catastrophic durations capped in a 5-storm sequence; ~35% of all draws."""
    cat5, share = 100 * float(ref.capped("catastrophic", 5)), 100 * float(exact["cap_share"])
    return {"cat5": cat5, "share": share,
            "met": round(cat5) == ORACLE_SS_CAP_CAT5_PCT and round(share) == ORACLE_SS_CAP_ALL_PCT}


def scaling():
    """s6.3: gaps are scaled in ~20% of moderate-to-severe persistent sequences, ~60% of
    catastrophic ones. Judged as scaled or left no room (either way, shorter than drawn)."""
    ms = 100 * float(ref.compressed(ORACLE_SS_WEIGHTS, ("moderate", "severe"), "persistent"))
    cat = 100 * float(ref.compressed(ORACLE_SS_WEIGHTS, ("catastrophic",), "persistent"))
    stated = list(ORACLE_SS_SCALE_STATED.values())
    return {"modsev": ms, "cat": cat, "met": round(ms, -1) == stated[0] and round(cat, -1) == stated[1]}


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
        "parameters": parameters(code),
        "continuous": continuous(replay),
        "window": window(replay),
        "recovery": recovery(exact, mc),
        "correlation": correlation(replay),
        "precipitation": precipitation(code),
        "table9": table9(exact),
        "seeds": seeds(mc),
        "cap": cap(exact),
        "scaling": scaling(),
        "reproducible": reproducible(code, replay),
    }
