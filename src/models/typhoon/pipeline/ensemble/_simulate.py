# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Top-level ensemble simulator — loops over events, aggregates per-property."""

import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from config.typhoon import CatchmentTyphoonConfig
from models.typhoon.data_structures import WindFieldOutput
from models.typhoon.genesis import coupled_genesis_wind
from models.typhoon.pipeline.aggregation import aggregate_property_winds
from models.typhoon.pipeline.event import (
    pick_representative_index,
    pick_representative_trajectory,
    simulate_one_event,
)
from models.typhoon.pipeline.results import (
    PropertyPeakWindSummary,
    TyphoonEventEnsemble,
)

from ._io import write_event_trajectory, write_event_windts


def simulate_typhoon_events(
    config: CatchmentTyphoonConfig,
    n_events: int,
    n_particles: int,
    rng: np.random.Generator,
    horizon_hours: Optional[float] = None,
    dt_hours: float = 1.0,
    use_plausibility: bool = True,
    events_output_dir: Optional[Path] = None,
    windts_output_dir: Optional[Path] = None,
    event_ids: Optional[List[str]] = None,
    event_severity_q: Optional[List[float]] = None,
    event_seeds: Optional[List[int]] = None,
    coupling_beta: float = 0.5,
    progress_every: int = 100,
) -> TyphoonEventEnsemble:
    """Simulate n_events typhoons and aggregate per-property statistics.

    Each event runs an independent particle filter; the wind-field is
    evaluated along every particle trajectory at every property point.
    Per-property statistics aggregate across all (n_events * n_particles)
    realizations.

    Args:
        config: catchment configuration
        n_events: number of typhoon events to simulate. Ignored when
            ``event_ids`` is supplied (then ``len(event_ids)`` governs).
        n_particles: particles per event
        rng: random generator (advanced by the call)
        horizon_hours: simulation horizon; defaults to config.horizon_hours
        dt_hours: step length (hours)
        use_plausibility: if True, wire the plausibility adapter into the filter
        event_ids: optional caller-supplied event identifiers, one per event.
            When provided, the typhoon count is slaved to ``len(event_ids)``
            and per-event artefacts are named by these ids (the shared 1:1
            storm<->typhoon key, e.g. "EVT-00001") rather than a local index.
            When None, falls back to ``n_events`` with index naming
            ``EVT-{idx:04d}`` (standalone / flood-only-fallback behaviour).
        event_severity_q: optional per-event storm-severity quantiles
            (q_i = rank(z_i)/(N+1), see coupling_spec.md §3-§4). When supplied,
            genesis peak wind is COUPLED to the paired storm: the §4 band-draw
            map fixes one Vmax per event (shared across that event's particles)
            instead of sampling marginally per particle. When None, genesis is
            standalone (each particle draws its own Vmax). Length must match the
            event count.
        event_seeds: optional per-event seeds (the shared 1:1 storm<->typhoon
            ``seed`` field). When supplied, each event reseeds a private RNG
            ``np.random.default_rng(event_seeds[i])`` so coupled genesis is
            reproducible per event regardless of loop order. When None, the
            shared ``rng`` is advanced sequentially (legacy behaviour).
        coupling_beta: coupling-strength knob β for the §4 floor
            ``f(q)=1−(1−q)^β``. β→0 = pure ceiling (no tail pull), β=1 =
            deterministic comonotone. Only consulted when event_severity_q
            is supplied.
        progress_every: emit an interim progress line every this many events
            (and once more at the final event). The line reports events done,
            elapsed time, throughput, an ETA, and running peak-wind statistics
            across the events simulated so far. Set to 0 to disable.

    Returns:
        TyphoonEventEnsemble with per-property PropertyPeakWindSummary
        entries plus metadata (timings, configuration knobs).
    """
    if event_ids is not None:
        n_events = len(event_ids)
    if n_events < 0:
        raise ValueError(f"n_events must be non-negative, got {n_events}")
    if n_particles <= 0:
        raise ValueError(f"n_particles must be positive, got {n_particles}")
    if event_severity_q is not None and len(event_severity_q) != n_events:
        raise ValueError(
            f"event_severity_q has length {len(event_severity_q)}, "
            f"expected {n_events} (one per event)"
        )
    if event_seeds is not None and len(event_seeds) != n_events:
        raise ValueError(
            f"event_seeds has length {len(event_seeds)}, "
            f"expected {n_events} (one per event)"
        )
    if horizon_hours is None:
        horizon_hours = config.horizon_hours

    coupled_genesis = event_severity_q is not None

    def _event_label(idx: int) -> str:
        """Shared storm<->typhoon key when supplied, else local index name."""
        if event_ids is not None:
            return event_ids[idx]
        return f"EVT-{idx:04d}"

    # Accumulator: property_id -> list of WindFieldOutput across all events.
    by_property: Dict[str, List[WindFieldOutput]] = {
        p.property_id: [] for p in config.property_points
    }

    if events_output_dir is not None:
        events_output_dir = Path(events_output_dir)
        events_output_dir.mkdir(parents=True, exist_ok=True)
    if windts_output_dir is not None:
        windts_output_dir = Path(windts_output_dir)
        windts_output_dir.mkdir(parents=True, exist_ok=True)

    # Running interim-result accumulators (cheap scalars updated per event)
    # so the progress line can report partial results without rescanning the
    # full by_property accumulator.
    run_peak_max = 0.0      # largest per-event peak sustained wind so far
    run_peak_sum = 0.0      # sum of per-event peaks (for a running mean)
    run_peak_n = 0          # number of events contributing a peak

    t_start = time.perf_counter()
    for event_idx in range(n_events):
        # Per-event RNG: when seeds are supplied (coupled mode), reseed a
        # private generator so each event's genesis is reproducible from its
        # shared storm<->typhoon seed irrespective of loop order. Otherwise
        # advance the shared rng sequentially (legacy standalone behaviour).
        ev_rng = (
            np.random.default_rng(event_seeds[event_idx])
            if event_seeds is not None
            else rng
        )

        # Coupled genesis: the §4 band-draw map fixes ONE genesis Vmax for the
        # whole event (all particles share it); the SMC engine still explores
        # track/size/location/regime and step() evolves Vmax over time, so
        # trajectory diversity persists. Standalone: leave overrides None and
        # each particle samples its own genesis Vmax.
        genesis_v_max = None
        genesis_scenario = None
        if coupled_genesis:
            genesis_v_max, genesis_scenario = coupled_genesis_wind(
                q=event_severity_q[event_idx],
                beta=coupling_beta,
                peak_wind=config.peak_wind,
                scenario_mix=config.genesis_prior.scenario_mix,
                rng=ev_rng,
            )

        event_result = simulate_one_event(
            config=config,
            n_particles=n_particles,
            rng=ev_rng,
            horizon_hours=horizon_hours,
            dt_hours=dt_hours,
            use_plausibility=use_plausibility,
            genesis_v_max=genesis_v_max,
            genesis_scenario=genesis_scenario,
        )
        for pid, outputs in event_result.by_property.items():
            by_property[pid].extend(outputs)

        # Interim result: peak sustained wind reached anywhere in this event
        # (max across its particles and property points). Cheap — operates on
        # this event's outputs only.
        ev_peak = 0.0
        for outputs in event_result.by_property.values():
            for o in outputs:
                if o.peak_sustained_ms > ev_peak:
                    ev_peak = o.peak_sustained_ms
        if event_result.by_property:
            run_peak_max = max(run_peak_max, ev_peak)
            run_peak_sum += ev_peak
            run_peak_n += 1

        # Pick a single representative particle for per-event artefacts so
        # the storm track (events/EVT-NNNN.json) and the per-property wind
        # timeseries (windts/EVT-NNNN.json) come from the same realization.
        rep_idx = (
            pick_representative_index(event_result.trajectories)
            if (events_output_dir is not None or windts_output_dir is not None)
            else None
        )

        event_label = _event_label(event_idx)

        if events_output_dir is not None and rep_idx is not None:
            rep_traj = event_result.trajectories[rep_idx]
            write_event_trajectory(
                rep_traj,
                events_output_dir / f"{event_label}.json",
                event_idx=event_idx,
            )

        if windts_output_dir is not None and rep_idx is not None:
            rep_wind_outputs = {
                pid: outputs[rep_idx]
                for pid, outputs in event_result.by_property.items()
            }
            scenario = event_result.trajectories[rep_idx].scenario_family
            write_event_windts(
                event_id=event_label,
                scenario_family=scenario,
                property_wind_outputs=rep_wind_outputs,
                output_path=windts_output_dir / f"{event_label}.json",
                horizon_hours=horizon_hours,
                dt_hours=dt_hours,
            )

        # Interim progress: every `progress_every` events and at the final
        # event, print a one-line update with throughput, ETA, and the
        # running peak-wind result so a long run shows steady signs of life.
        done = event_idx + 1
        is_block = progress_every > 0 and done % progress_every == 0
        is_last = done == n_events
        if progress_every > 0 and (is_block or is_last):
            since = time.perf_counter() - t_start
            rate = done / since if since > 0 else 0.0
            remaining = (n_events - done) / rate if rate > 0 else 0.0
            pct = 100.0 * done / n_events if n_events else 100.0
            if run_peak_n:
                peak_str = (
                    f"peak wind so far: max {run_peak_max:.1f} m/s, "
                    f"mean {run_peak_sum / run_peak_n:.1f} m/s"
                )
            else:
                peak_str = "peak wind so far: n/a (no property points)"
            print(
                f"   [typhoon] {done:,}/{n_events:,} events ({pct:4.1f}%)  |  "
                f"{since:6.1f}s elapsed, {rate:5.1f} ev/s, "
                f"~{remaining:6.1f}s remaining  |  {peak_str}",
                flush=True,
            )
    elapsed = time.perf_counter() - t_start

    summaries: List[PropertyPeakWindSummary] = []
    for prop in config.property_points:
        summaries.append(aggregate_property_winds(
            property_point=prop,
            realizations=by_property[prop.property_id],
            thresholds_ms=config.output_thresholds_ms,
        ))

    metadata = {
        "elapsed_seconds": elapsed,
        "use_plausibility": use_plausibility,
        "ess_threshold_frac": config.filter.ess_threshold_frac,
        "n_property_points": len(config.property_points),
        "n_realizations_per_property": n_events * n_particles,
        "coupled_genesis": coupled_genesis,
        "coupling_beta": coupling_beta if coupled_genesis else None,
    }

    return TyphoonEventEnsemble(
        catchment_id=config.catchment_id,
        n_events=n_events,
        n_particles=n_particles,
        horizon_hours=horizon_hours,
        dt_hours=dt_hours,
        properties=summaries,
        metadata=metadata,
    )
