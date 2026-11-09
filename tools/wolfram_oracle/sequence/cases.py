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

"""SS-001's code against its document, case by case.

The replay compares every sequence the code generates with the reference's, number for
number. The Monte Carlo compares what the code generates in bulk with the exact law the
document's tables imply, in standard errors. The validator is run on everything generated,
and on sequences broken on purpose.
"""

import copy
import importlib
import math
from fractions import Fraction as Q

import mpmath as mp
import numpy as np
from tools.wolfram_oracle._model import load_module
from tools.wolfram_oracle.sequence import reference as ref

from config.models import (
    ORACLE_SS_BASE,
    ORACLE_SS_CAP_TOL,
    ORACLE_SS_CATEGORIES,
    ORACLE_SS_COUNT,
    ORACLE_SS_FORCED_COUNT,
    ORACLE_SS_FORCED_SEED,
    ORACLE_SS_PACKAGE,
    ORACLE_SS_SEED,
    ORACLE_SS_SEEDS,
    ORACLE_SS_WEIGHTS,
)

TYPES = ("isolated", "doublet", "cluster", "persistent")


class Code:
    """The package's modules, loaded without running its ``__init__``."""

    def __init__(self):
        batch = load_module(f"{ORACLE_SS_PACKAGE}/generators/batch_generator.py", package_root=ORACLE_SS_PACKAGE)
        pkg = batch.__name__.rsplit(".", 2)[0]
        self.batch = batch
        self.seq = importlib.import_module(f"{pkg}.generators.sequence_generator")
        self.duration = importlib.import_module(f"{pkg}.generators.duration_sampler")
        self.gap = importlib.import_module(f"{pkg}.generators.gap_sampler")
        self.intensity = importlib.import_module(f"{pkg}.generators.intensity_sampler")
        self.validation = importlib.import_module(f"{pkg}.utils.validation")
        self.data = importlib.import_module(f"{pkg}.core.data_structures")


def load():
    return Code()


def _err(a, b):
    a, b = mp.mpf(a), (mp.mpf(b.numerator) / b.denominator if isinstance(b, Q) else mp.mpf(b))
    return float(abs(a - b) / abs(b)) if b else float(abs(a))


def compare(code_seq, r):
    """(structure differs, worst relative error) between one code sequence and the reference's."""
    s = code_seq.storms
    if code_seq.sequence_type != r["type"] or len(s) != r["n"]:
        return True, 0.0
    pairs = [(x.duration_hours, y) for x, y in zip(s, r["d"])]
    pairs += list(zip(code_seq.inter_storm_gaps_hours, r["g"]))
    pairs += [(x.start_time_hours, y) for x, y in zip(s, r["start"])]
    pairs += [(x.intensity_factor, y) for x, y in zip(s, r["f"])]
    pairs += [(x.precipitation_mm, y) for x, y in zip(s, r["p"])]
    pairs += [(x.peak_position, y) for x, y in zip(s, r["peak"])]
    pairs += [(code_seq.total_precipitation_mm, r["p_total"]), (code_seq.max_intensity_factor, r["f_max"]),
              (code_seq.avg_intensity_factor, r["f_avg"]), (code_seq.cumulative_intensity_factor, r["f_cum"]),
              (code_seq.total_duration_hours, r["total"]), (code_seq.drainage_window_hours, r["drain"])]
    return False, max(_err(a, b) for a, b in pairs)


def replay(code):
    """The default batch and every category with every forced type, against the reference."""
    pbase = code.seq.SequenceGenerator().base_precipitation
    seqs = code.batch.generate_event_set(ORACLE_SS_COUNT, seed=ORACLE_SS_SEED)
    refs = ref.replay_batch(ORACLE_SS_COUNT, ORACLE_SS_SEED, ORACLE_SS_WEIGHTS, pbase)
    results = [compare(a, b) for a, b in zip(seqs, refs)]
    gen = code.seq.SequenceGenerator(seed=ORACLE_SS_FORCED_SEED)
    rng = np.random.RandomState(ORACLE_SS_FORCED_SEED)
    forced = []
    for cat in ORACLE_SS_CATEGORIES:
        f0 = ORACLE_SS_BASE[cat][0]
        for t in TYPES:
            for _ in range(ORACLE_SS_FORCED_COUNT):
                forced.append(gen.generate(cat, f0, force_sequence_type=t))
                results.append(compare(forced[-1], ref.replay_forced(rng, cat, f0, t, pbase)))
    return {"sequences": len(results), "structure_off": sum(off for off, _ in results),
            "worst": max(e for _, e in results), "batch": seqs, "forced": forced, "pbase": pbase, "seed": ORACLE_SS_SEED}


def _z(k, n, p):
    p = float(p)
    return abs(k / n - p) / math.sqrt(p * (1 - p) / n) if 0 < p < 1 else (0.0 if k == n * p else math.inf)


def pinned(seq):
    """Every storm at Eq. 6's cap, so every gap is held at its minimum."""
    cap = float(ref.cap_of(seq.sequence_type, seq.num_storms))
    return all(abs(s.duration_hours - cap) < ORACLE_SS_CAP_TOL for s in seq.storms)


def _shares(seqs):
    types = {t: sum(s.sequence_type == t for s in seqs) for t in TYPES}
    counts = {n: sum(s.num_storms == n for s in seqs) for n in range(1, 1 + max(s.num_storms for s in seqs))}
    multi = [s for s in seqs if s.num_storms > 1]
    return types, counts, len(multi), sum(pinned(s) for s in multi)


def monte_carlo(code, batch, exact):
    """The code's batches against the exact law: type mix over ORACLE_SS_SEEDS seeds; storm
    counts and sequences with every storm capped in the default batch."""
    seeds = [batch] + [code.batch.generate_event_set(ORACLE_SS_COUNT, seed=ORACLE_SS_SEED + k)
                       for k in range(1, ORACLE_SS_SEEDS)]
    per_seed = [_shares(s)[0] for s in seeds]
    pooled = {t: sum(p[t] for p in per_seed) for t in TYPES}
    total = ORACLE_SS_COUNT * len(seeds)
    z_types = max(_z(pooled[t], total, exact["types"][t]) for t in TYPES)
    types, counts, multi, pin = _shares(batch)
    z_counts = max(_z(counts[n], ORACLE_SS_COUNT, exact["counts"].get(n, 0)) for n in counts | exact["counts"])
    return {"seeds": len(seeds), "per_seed": per_seed, "pooled": pooled, "z_types": z_types,
            "types": types, "counts": counts, "z_counts": z_counts, "multi": multi, "pinned": pin,
            "z_pinned": _z(pin, multi, exact["pinned_share"])}


def _broken(seq, how):
    s = copy.deepcopy(seq)
    if how == "late":
        s.storms[-1].duration_hours += 200
    elif how == "overlap":
        s.storms[1].start_time_hours = s.storms[0].start_time_hours
    elif how == "gaps":
        s.inter_storm_gaps_hours = s.inter_storm_gaps_hours + [1.0]
    elif how == "type":
        s.sequence_type = "tornado"
    elif how == "short":
        s.inter_storm_gaps_hours = [0.5] + s.inter_storm_gaps_hours[1:]
    return s


def validator(code, seqs):
    """validate_event_set on everything generated; and each fault caught when injected."""
    v = code.validation.validate_event_set(seqs)
    sample = next(s for s in seqs if s.num_storms > 1)
    faults = ("late", "overlap", "gaps", "type", "short")
    caught = sum(bool(code.validation.validate_sequence(_broken(sample, f))) for f in faults)
    return {"total": v["total"], "invalid": v["invalid"], "faults": len(faults), "caught": caught}
