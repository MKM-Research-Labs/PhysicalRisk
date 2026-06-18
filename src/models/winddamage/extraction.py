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

"""Read per-event wind timeseries (windts/EVT-NNNN.json) and pull out the
per-property peak sustained wind in m/s.

The windts payload comes from the typhoon pipeline (Phase 1.7+) and has
shape:

    {
      "event_id": "EVT-0001",
      "scenario_family": "moderate",
      "horizon_hours": 168.0,
      "dt_hours": 1.0,
      "property_windts": [
        {"point_id": "PROP-...", "peak_sustained_ms": 32.4, ...},
        ...
      ]
    }

The per-property peak drives the severity term; the per-property sustained-wind
time series (``time_hours`` + ``sustained_ms``) lets the composer measure how
long the wind stayed above the property's damage-onset threshold — the
persistence (duration-of-load) input to the damage model.
"""

import json
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple, Union


__all__ = ["EventWindts", "load_event_peaks", "duration_above_threshold"]


def duration_above_threshold(
    time_hours: List[float],
    values: List[float],
    threshold: float,
) -> float:
    """Hours where ``values`` exceed ``threshold`` (left-rectangle rule).

    For each consecutive pair (t_i, v_i) -> (t_{i+1}, v_{i+1}), if v_i is above
    the threshold the interval (t_{i+1} - t_i) is added; the final sample
    contributes nothing. Mirrors
    ``models.typhoon.wind_field.time_series.duration_above_threshold`` so the
    wind-damage package stays decoupled from the typhoon package (it only ever
    reads the windts JSON, never imports typhoon).
    """
    total = 0.0
    for i in range(len(time_hours) - 1):
        if values[i] > threshold:
            total += time_hours[i + 1] - time_hours[i]
    return total


class EventWindts(NamedTuple):
    """Lightweight summary of a windts file.

    ``peaks_by_property`` drives the severity term; ``series_by_property``
    carries each property's sustained-wind series (time_hours, sustained_ms)
    used to measure persistence (duration above the damage-onset threshold).
    ``series_by_property`` may be empty for legacy windts files that stored
    only peaks — the composer then falls back to the single-gust floor.
    """
    event_id: str
    scenario_family: str
    horizon_hours: float
    dt_hours: float
    peaks_by_property: Dict[str, float]
    series_by_property: Dict[str, Tuple[List[float], List[float]]] = {}


def load_event_peaks(source: Union[Path, str]) -> EventWindts:
    """Load a windts/EVT-NNNN.json and return per-property peak winds.

    Args:
        source: path to one EVT-NNNN.json file produced by the pipeline.

    Returns:
        EventWindts with event metadata plus a {property_id: peak_ms} dict.
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Windts file not found: {path}")
    payload = json.loads(path.read_text())

    peaks: Dict[str, float] = {}
    series: Dict[str, Tuple[List[float], List[float]]] = {}
    for entry in payload.get("property_windts", []):
        property_id = entry.get("point_id")
        peak = entry.get("peak_sustained_ms")
        if property_id is None or peak is None:
            continue
        pid = str(property_id)
        peaks[pid] = float(peak)
        # Sustained-wind series for persistence; absent in legacy peak-only files.
        times = entry.get("time_hours")
        sustained = entry.get("sustained_ms")
        if times and sustained and len(times) == len(sustained):
            series[pid] = (
                [float(t) for t in times],
                [float(v) for v in sustained],
            )

    return EventWindts(
        event_id=str(payload.get("event_id", path.stem)),
        scenario_family=str(payload.get("scenario_family", "")),
        horizon_hours=float(payload.get("horizon_hours", 0.0)),
        dt_hours=float(payload.get("dt_hours", 0.0)),
        peaks_by_property=peaks,
        series_by_property=series,
    )
