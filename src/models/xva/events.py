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

"""Correlated trigger times across gauges, from the MKM-EF-001 catalogue.

The catalogue supplies the dependence: one catchment event reaches every gauge,
and its per-event flags say which gauges it takes over Severe. As in
``models.frequency.ylt`` (and the capital package), events arrive at the
catchment rate times the catalogue coverage and are drawn by catalogue weight
with inverse-transform sampling. Two things are added for a multi-year
exposure simulation:

- Arrival is a Cox process: events arrive at lambda_cat Y(t), i.e. at unit
  rate in the factor clock C(t) = int Y. With sigma = 0, C(t) = t.
- Each gauge's marginal must be the market's lambda_g Y + phi_g (the price
  the trade was dealt on), not the catalogue's own rate c_g. Where c_g >
  lambda_g, each flagged event triggers the gauge with probability
  lambda_g / c_g; where c_g < lambda_g, a Y-driven idiosyncratic top-up at
  rate lambda_g - c_g supplies the rest. The CIR++ shift phi_g is a further
  idiosyncratic Poisson in real time.

The result is the first trigger time per gauge per path (inf if none before
the horizon) and the catchment event times, which drive the wrong-way-risk
stress.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np

from .cir import ShiftedTrigger


@dataclass(frozen=True)
class TriggerModel:
    """Catalogue dependence: event rate, weights and Severe flags per gauge."""
    event_rate: float                 # catchment rate x coverage, events / year
    weights: np.ndarray               # per catalogue event, summing to one
    flags: Dict[str, np.ndarray]      # gauge id -> per-event Severe flag

    @classmethod
    def independent(cls) -> "TriggerModel":
        """No catalogue: gauges trigger independently given the factor Y."""
        return cls(0.0, np.zeros(0), {})

    @classmethod
    def from_catalogue(cls, catalogue, thresholds: Dict[str, float],
                       lambda_per_year: float) -> "TriggerModel":
        """From an ``EventCatalogue`` and each gauge's Severe level (metres)."""
        flags = {g: catalogue.flood_flags(g, level) for g, level in thresholds.items()}
        return cls(lambda_per_year * catalogue.coverage, np.asarray(catalogue.weights), flags)

    def catalogue_rate(self, gauge: str) -> float:
        """c_g: the rate at which catalogue events take the gauge over Severe."""
        if gauge not in self.flags or self.event_rate == 0.0:
            return 0.0
        return self.event_rate * float(np.dot(self.weights, self.flags[gauge]))


@dataclass
class EventPaths:
    first_trigger: Dict[str, np.ndarray]   # gauge -> (n_paths,) first trigger time
    event_times: np.ndarray                # catchment event times, flat
    event_paths: np.ndarray                # path index of each event
    event_index: np.ndarray                # catalogue index of each event


def _clock_inverse(clock: np.ndarray, times: np.ndarray, paths: np.ndarray,
                   targets: np.ndarray) -> np.ndarray:
    """Real time at which each path's factor clock reaches its target.

    Vectorised over paths: each row of the (non-decreasing) clock is offset by
    a per-path constant larger than any clock value, so one ``searchsorted`` on
    the flattened array finds every target's interval at once. Beyond the
    path's horizon the answer is inf.
    """
    if targets.size == 0:
        return np.zeros(0)
    n_times = times.size
    offset = float(clock.max()) + 1.0
    flat = (clock + offset * np.arange(clock.shape[0])[:, None]).ravel()
    shifted = targets + offset * paths
    pos = np.searchsorted(flat, shifted, side="left")
    local = np.clip(pos - paths * n_times, 1, n_times - 1)
    hi = paths * n_times + local
    c0, c1 = flat[hi - 1], flat[hi]
    t0, t1 = times[local - 1], times[local]
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(c1 > c0, (shifted - c0) / (c1 - c0), 0.0)
    out = t0 + np.clip(frac, 0.0, 1.0) * (t1 - t0)
    return np.where(targets <= clock[paths, -1], out, np.inf)


def _first_by_path(n_paths: int, paths: np.ndarray, times: np.ndarray) -> np.ndarray:
    first = np.full(n_paths, np.inf)
    np.minimum.at(first, paths, times)
    return first


def simulate(model: TriggerModel, triggers: Dict[str, ShiftedTrigger], times: np.ndarray,
             clock: np.ndarray, rng: np.random.Generator,
             gauges: Optional[Sequence[str]] = None) -> EventPaths:
    """Trigger times per gauge on each path, given the factor clock C on ``times``."""
    n_paths = clock.shape[0]
    horizon_clock = clock[:, -1]
    path_ids = np.arange(n_paths)

    # Catchment events: unit-rate Poisson in the factor clock, scaled by event_rate.
    counts = rng.poisson(model.event_rate * horizon_clock) if model.event_rate > 0 \
        else np.zeros(n_paths, dtype=np.int64)
    ev_paths = np.repeat(path_ids, counts)
    ev_clock = rng.random(ev_paths.size) * horizon_clock[ev_paths]
    ev_times = _clock_inverse(clock, times, ev_paths, ev_clock)
    if ev_paths.size and model.weights.size:
        cumulative = np.cumsum(model.weights)
        cumulative[-1] = 1.0
        ev_index = np.clip(np.searchsorted(cumulative, rng.random(ev_paths.size), side="right"),
                           0, model.weights.size - 1)
    else:
        ev_index = np.zeros(ev_paths.size, dtype=np.int64)

    first = {}
    for gauge in (gauges if gauges is not None else triggers):
        trig = triggers[gauge]
        lam, c_g = trig.scale, model.catalogue_rate(gauge)
        shared = np.full(n_paths, np.inf)
        if c_g > 0 and ev_paths.size:
            keep = model.flags[gauge][ev_index] & (rng.random(ev_paths.size) < min(1.0, lam / c_g))
            shared = _first_by_path(n_paths, ev_paths[keep], ev_times[keep])
        top_up = max(lam - c_g, 0.0)
        idio = np.full(n_paths, np.inf)
        if top_up > 0:
            target = rng.exponential(1.0, n_paths) / top_up
            idio = _clock_inverse(clock, times, path_ids, target)
        # Non-decreasing by construction (phi >= 0); clip float noise for interp.
        shift = np.maximum.accumulate(np.maximum(trig.shift_integral(times), 0.0))
        target = rng.exponential(1.0, n_paths)
        jump = np.where(target <= shift[-1], np.interp(target, shift, times), np.inf) \
            if shift[-1] > 0 else np.full(n_paths, np.inf)
        first[gauge] = np.minimum(np.minimum(shared, idio), jump)
    return EventPaths(first, ev_times, ev_paths, ev_index)
