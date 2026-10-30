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

"""Training sets per gauge: from the storm catalogue, or a synthetic catalogue.

Both go through the production vector builder (port.src.stressm.classifier), so
the benchmark scores exactly the features and labels production trains on.
"""

from dataclasses import dataclass

import numpy as np

from config.models import (
    CHALLENGER_SYNTH_BASE_LEVEL,
    CHALLENGER_SYNTH_DECAY,
    CHALLENGER_SYNTH_NOISE,
    CHALLENGER_SYNTH_PEAK_RANGE,
    CHALLENGER_SYNTH_RISE_HOURS,
    CHALLENGER_SYNTH_SEVERE_LEVEL,
)
from config.port import NUM_CLASSIFIER_HOURS


@dataclass
class GaugeSet:
    """One gauge's vectors.  Rows ``[:n_real]`` are real storms; the rest are
    near-miss augmentation (negative groups), used for training only."""
    gauge_id: str
    X: np.ndarray
    y: np.ndarray
    groups: np.ndarray
    n_real: int
    label_name: str

    @classmethod
    def from_training(cls, gauge_id, training):
        v = np.asarray(training["vector"], dtype=float)
        return cls(gauge_id, v[:, :4], v[:, 4].astype(int),
                   np.asarray(training["groups"]), training["n_real"],
                   training["label_name"])


def load_catalogue(gauge_ids, n_storms, seed, max_gauges=None):
    """GaugeSets from the active catchment's storm catalogue.

    ``n_storms`` storms are sampled once (without replacement) and shared by
    every gauge, as in production.  Each gauge uses production's spatial seed.
    """
    from database.config_binding import use_configured_backend
    use_configured_backend()

    import database
    from port.src.storm_multi.utils.serialization import load_sequences
    from port.src.stressm.classifier._core import build_gauge_training_set
    from port.src.stressm.summary import load_gauge_training_context

    if not database.storm_sequences_exists(database.active_catchment()):
        raise FileNotFoundError(
            f"storm_sequences not found for catchment {database.active_catchment()!r} "
            "(is the data drive mounted?)")
    gauges, all_ids, spatial_model = load_gauge_training_context()
    if gauge_ids != "all":
        wanted = set(gauge_ids)
        gauges = [g for g in gauges if g["gauge_id"] in wanted]
        missing = wanted - {g["gauge_id"] for g in gauges}
        if missing:
            raise KeyError(f"gauges not in portfolio: {sorted(missing)}")
    if max_gauges:
        gauges = gauges[:max_gauges]

    sequences = load_sequences()
    rng = np.random.RandomState(seed)
    if n_storms and n_storms < len(sequences):
        keep = np.sort(rng.choice(len(sequences), n_storms, replace=False))
        sequences = [sequences[i] for i in keep]
    print(f"  {len(sequences):,} storms × {len(gauges)} gauges", flush=True)

    for gauge in gauges:
        idx = all_ids.index(gauge["gauge_id"])
        training = build_gauge_training_set(
            sequences, gauge, spatial_model, idx, np.random.RandomState(seed + 1 + idx))
        yield GaugeSet.from_training(gauge["gauge_id"], training)


def synthetic_hydrograph(rng, severe, base):
    """A sin-rise / exp-decay hydrograph with a random peak around ``severe``."""
    peak = severe * rng.uniform(*CHALLENGER_SYNTH_PEAK_RANGE)
    rise = rng.randint(*CHALLENGER_SYNTH_RISE_HOURS)
    decay = rng.uniform(*CHALLENGER_SYNTH_DECAY)
    h = np.arange(NUM_CLASSIFIER_HOURS)
    shape = np.where(h < rise, np.sin(h / rise * np.pi / 2), np.exp(-decay * (h - rise)))
    levels = base + (peak - base) * shape
    levels += rng.normal(0, CHALLENGER_SYNTH_NOISE * severe, len(h))
    return np.maximum(levels, base * 0.5).tolist()


def synthetic_catalogue(n_gauges, n_storms, seed):
    """GaugeSets from a synthetic catalogue (smoke runs and tests; no data)."""
    from port.src.stressm.classifier._core import _nearmiss_groups, hydrograph_vectors
    from port.src.stressm.classifier._nearmiss import _generate_nearmiss_vectors

    base, severe = CHALLENGER_SYNTH_BASE_LEVEL, CHALLENGER_SYNTH_SEVERE_LEVEL
    for g in range(n_gauges):
        rng = np.random.RandomState(seed + g)
        vectors, groups = [], []
        for i in range(n_storms):
            rows = hydrograph_vectors(synthetic_hydrograph(rng, severe, base), severe)
            vectors.extend(rows)
            groups.extend([i] * len(rows))
        n_real = len(vectors)
        nearmiss = _generate_nearmiss_vectors(severe, base, rng)
        vectors.extend(nearmiss)
        groups.extend(_nearmiss_groups(len(nearmiss)))
        yield GaugeSet.from_training(f"SYNTH-{g + 1}", {
            "vector": vectors, "groups": groups, "n_real": n_real,
            "label_name": "severe_warning"})
