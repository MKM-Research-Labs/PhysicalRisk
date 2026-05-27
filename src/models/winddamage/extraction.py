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

Only the per-property peak is needed for Phase 2 damage (peak-only,
documented in the Phase 2 plan).
"""

import json
from pathlib import Path
from typing import Dict, NamedTuple, Union


__all__ = ["EventWindts", "load_event_peaks"]


class EventWindts(NamedTuple):
    """Lightweight summary of a windts file's per-property peaks."""
    event_id: str
    scenario_family: str
    horizon_hours: float
    dt_hours: float
    peaks_by_property: Dict[str, float]


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
    for entry in payload.get("property_windts", []):
        property_id = entry.get("point_id")
        peak = entry.get("peak_sustained_ms")
        if property_id is None or peak is None:
            continue
        peaks[str(property_id)] = float(peak)

    return EventWindts(
        event_id=str(payload.get("event_id", path.stem)),
        scenario_family=str(payload.get("scenario_family", "")),
        horizon_hours=float(payload.get("horizon_hours", 0.0)),
        dt_hours=float(payload.get("dt_hours", 0.0)),
        peaks_by_property=peaks,
    )
