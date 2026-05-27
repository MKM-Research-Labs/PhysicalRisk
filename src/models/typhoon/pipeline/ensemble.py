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

"""Top-level ensemble simulator — loops over events, aggregates per-property.

Catchment-agnostic. Takes a CatchmentTyphoonConfig and produces a
TyphoonEventEnsemble. No file I/O here; the caller (boundary adapter)
decides where to persist the result.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from config.typhoon import CatchmentTyphoonConfig
from models.typhoon.data_structures import WindFieldOutput
from models.typhoon.pipeline.aggregation import aggregate_property_winds
from models.typhoon.pipeline.event import simulate_one_event
from models.typhoon.pipeline.results import (
    PropertyPeakWindSummary,
    TyphoonEventEnsemble,
)


__all__ = ["simulate_typhoon_events", "write_ensemble_json"]


def simulate_typhoon_events(
    config: CatchmentTyphoonConfig,
    n_events: int,
    n_particles: int,
    rng: np.random.Generator,
    horizon_hours: Optional[float] = None,
    dt_hours: float = 1.0,
    use_plausibility: bool = True,
) -> TyphoonEventEnsemble:
    """Simulate n_events typhoons and aggregate per-property statistics.

    Each event runs an independent particle filter; the wind-field is
    evaluated along every particle trajectory at every property point.
    Per-property statistics aggregate across all (n_events * n_particles)
    realizations.

    Args:
        config: catchment configuration
        n_events: number of typhoon events to simulate
        n_particles: particles per event
        rng: random generator (advanced by the call)
        horizon_hours: simulation horizon; defaults to config.horizon_hours
        dt_hours: step length (hours)
        use_plausibility: if True, wire the plausibility adapter into the filter

    Returns:
        TyphoonEventEnsemble with per-property PropertyPeakWindSummary
        entries plus metadata (timings, configuration knobs).
    """
    if n_events < 0:
        raise ValueError(f"n_events must be non-negative, got {n_events}")
    if n_particles <= 0:
        raise ValueError(f"n_particles must be positive, got {n_particles}")
    if horizon_hours is None:
        horizon_hours = config.horizon_hours

    # Accumulator: property_id -> list of WindFieldOutput across all events.
    by_property: Dict[str, List[WindFieldOutput]] = {
        p.property_id: [] for p in config.property_points
    }

    t_start = time.perf_counter()
    for _ in range(n_events):
        event_outputs = simulate_one_event(
            config=config,
            n_particles=n_particles,
            rng=rng,
            horizon_hours=horizon_hours,
            dt_hours=dt_hours,
            use_plausibility=use_plausibility,
        )
        for pid, outputs in event_outputs.items():
            by_property[pid].extend(outputs)
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


def write_ensemble_json(ensemble: TyphoonEventEnsemble, output_path: Path) -> None:
    """Persist a TyphoonEventEnsemble to JSON. Creates parent dirs as needed."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(ensemble.to_dict(), f, indent=2)
