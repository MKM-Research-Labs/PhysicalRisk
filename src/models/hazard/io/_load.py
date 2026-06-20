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

"""Loaders for storms, storm sequences and gauge portfolios."""

import json
from pathlib import Path

from port.cdm.gauge import FloodGaugeCDM


def load_storms(input_path: Path) -> list:
    """Load storms from JSON file (legacy storms.json format)."""
    with open(input_path) as f:
        data = json.load(f)
    return data['storms']


def load_storms_from_sequences(sequences_data: dict) -> list:
    """Flatten a storm-sequences document into individual storm dicts for the hazard model.

    Each SequenceStorm is extracted from its parent sequence and mapped to the
    legacy storm dict schema expected by GaugeResponseModel:
      - storm_id
      - effective_precipitation_mm  (from precipitation_mm)
      - duration_hours
      - intensity_factor
      - intensity_category
      - peak_position

    Args:
        sequences_data: the parsed ``storm_sequences`` document (``{"sequences": [...]}``).
    """
    storms = []
    for seq in sequences_data.get("sequences", []):
        for storm in seq.get("storms", []):
            storms.append({
                "storm_id": storm["storm_id"],
                "effective_precipitation_mm": storm["precipitation_mm"],
                "duration_hours": storm["duration_hours"],
                "intensity_factor": storm["intensity_factor"],
                "intensity_category": storm.get("intensity_category", ""),
                "peak_position": storm.get("peak_position", 0.5),
            })
    return storms


def load_gauges(gauge_portfolio: dict) -> list:
    """
    Map a gauge-portfolio document to flat gauge dicts using the CDM.

    The gauge portfolio structure (from the gauge generator):
    {
        "flood_gauges": [{FloodGauge: {...}}, ...],
        "generation_metadata": {...}
    }

    Uses FloodGaugeCDM.create_mapping() to flatten the nested CDM structure
    into a consistent flat dictionary format.
    """
    raw_gauges = gauge_portfolio.get('flood_gauges', [])

    if not raw_gauges:
        raise ValueError(
            "No gauges found in the portfolio. "
            f"Expected 'flood_gauges' key. Found keys: {list(gauge_portfolio.keys())}"
        )

    cdm = FloodGaugeCDM()
    gauges = []

    for i, raw in enumerate(raw_gauges):
        flat_gauge = cdm.create_mapping(raw)

        if not flat_gauge.get('gauge_id'):
            raise ValueError(
                f"Gauge at index {i} has no gauge_id after CDM mapping. "
                f"Raw data keys: {list(raw.keys())}"
            )

        gauges.append(flat_gauge)

    return gauges
