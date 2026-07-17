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

"""JSON persistence for ensemble + per-event artefacts."""

import json
from pathlib import Path
from typing import Dict, Optional

from models.typhoon.data_structures import WindFieldOutput
from models.typhoon.pipeline.results import TyphoonEventEnsemble


def write_ensemble_json(ensemble: TyphoonEventEnsemble, output_path: Path) -> None:
    """Persist a TyphoonEventEnsemble to JSON. Creates parent dirs as needed."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(ensemble.to_dict(), f, indent=2)


def write_event_windts(
    event_id: str,
    scenario_family,
    property_wind_outputs: Dict[str, "WindFieldOutput"],
    output_path: Path,
    horizon_hours: float,
    dt_hours: float,
) -> None:
    """Persist per-property wind timeseries for one event to JSON.

    The on-disk shape:
        {
          "event_id": "EVT-0001",
          "scenario_family": "moderate",
          "horizon_hours": 168.0,
          "dt_hours": 1.0,
          "property_windts": [<WindFieldOutput.to_dict()>, ...]
        }

    Downstream consumers (flood model, BRI scoring, visual review of
    storm progression alongside flood) read these files. One file per
    event, one WindFieldOutput per property point.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "event_id": event_id,
        "scenario_family": scenario_family.value if hasattr(scenario_family, "value") else scenario_family,
        "horizon_hours": horizon_hours,
        "dt_hours": dt_hours,
        "property_windts": [wf.to_dict() for wf in property_wind_outputs.values()],
    }
    with output_path.open("w") as f:
        json.dump(payload, f, indent=2)


def write_event_trajectory(
    trajectory,
    output_path: Path,
    event_idx: Optional[int] = None,
) -> None:
    """Persist a single TyphoonTrajectory to JSON.

    Used by simulate_typhoon_events when events_output_dir is set: one
    file per event holding the representative particle's full track.
    The JSON shape is the standard TyphoonTrajectory.to_dict() plus a
    small summary header listing peak V_max and time-of-peak for quick
    visual inspection.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = trajectory.to_dict()
    if trajectory.states:
        peak_idx = max(range(len(trajectory.states)),
                       key=lambda i: trajectory.states[i].v_max_ms)
        peak_state = trajectory.states[peak_idx]
        payload["summary"] = {
            "event_idx": event_idx,
            "n_states": len(trajectory.states),
            "horizon_hours": trajectory.horizon_hours,
            "peak_v_max_ms": peak_state.v_max_ms,
            "peak_time_hours": peak_state.time_hours,
            "peak_longitude": peak_state.longitude,
            "peak_latitude": peak_state.latitude,
        }
    with output_path.open("w") as f:
        json.dump(payload, f, indent=2)
