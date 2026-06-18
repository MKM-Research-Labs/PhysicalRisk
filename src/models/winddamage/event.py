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

"""Per-event composer.

Reads one windts/EVT-NNNN.json + a property portfolio, computes the
BRI-aware damage ratio for every property hit by the event, and writes
the result to damage/EVT-NNNN.json.

Shape of the output mirrors the per-event flood damage report and the
per-event windts file so downstream consumers can treat hazard outputs
uniformly.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from models.winddamage.bri_shift import bri_v50_shift
from models.winddamage.cdm import extract_bri_scores, extract_property_id
from models.winddamage.extraction import (
    EventWindts,
    duration_above_threshold,
    load_event_peaks,
)
from models.winddamage.threshold import resolve_threshold_ms
from models.winddamage.vulnerability import (
    bri_peak_damage,
    bri_wind_damage,
    persistence_factor,
)


__all__ = ["build_event_damage", "run_event", "run_event_directory"]


def build_event_damage(
    windts: EventWindts,
    properties: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compose the event damage payload in memory.

    For each property whose id appears in `windts.peaks_by_property`,
    compute the persistence-aware BRI damage ratio: the peak severity sigmoid
    scaled by the duration-of-load factor, where persistence is measured as the
    hours the property's sustained wind stayed above its BRI-adjusted v_50_eff.
    Properties whose windts file carried no series fall back to the single-gust
    floor. Properties not hit by the event are omitted from the output.
    """
    damages: List[Dict[str, Any]] = []
    for record in properties:
        prop_id = extract_property_id(record)
        if prop_id is None:
            continue
        peak = windts.peaks_by_property.get(prop_id)
        if peak is None:
            continue

        threshold_ms = resolve_threshold_ms(record)
        bri_wind, bri_composite = extract_bri_scores(record)

        # v_50_eff — the BRI-adjusted damage threshold. Drives both the
        # severity sigmoid and the persistence reference level, and is recorded
        # for inspection / regulatory traceability.
        if bri_wind is not None or bri_composite is not None:
            wind = bri_wind if bri_wind is not None else 0.50
            comp = bri_composite if bri_composite is not None else 0.50
            v_50_eff = threshold_ms + bri_v50_shift(wind, comp)
        else:
            v_50_eff = threshold_ms

        # Persistence: hours the sustained wind exceeded v_50_eff. With a
        # series we measure it and apply the duration-of-load factor. Without a
        # series (legacy peak-only windts) duration is unknown, so we fall back
        # to the peak-only saturated bound rather than asserting an unjustified
        # single-gust reduction.
        series = windts.series_by_property.get(prop_id)
        if series is not None:
            times, sustained = series
            duration_above_hours = duration_above_threshold(times, sustained, v_50_eff)
            phi = persistence_factor(duration_above_hours)
            damage = bri_wind_damage(
                peak_sustained_ms=peak,
                duration_above_hours=duration_above_hours,
                threshold_ms=threshold_ms,
                bri_wind_score=bri_wind,
                bri_composite_score=bri_composite,
            )
            duration_field: float | None = float(duration_above_hours)
        else:
            phi = 1.0
            damage = bri_peak_damage(
                peak_sustained_ms=peak,
                threshold_ms=threshold_ms,
                bri_wind_score=bri_wind,
                bri_composite_score=bri_composite,
            )
            duration_field = None  # not measured

        damages.append({
            "property_id": prop_id,
            "peak_sustained_ms": float(peak),
            "threshold_ms": float(threshold_ms),
            "bri_wind_score": bri_wind,
            "bri_composite_score": bri_composite,
            "v_50_eff_ms": float(v_50_eff),
            "duration_above_hours": duration_field,
            "persistence_factor": float(phi),
            "damage_ratio": float(damage),
        })

    return {
        "event_id": windts.event_id,
        "scenario_family": windts.scenario_family,
        "horizon_hours": windts.horizon_hours,
        "dt_hours": windts.dt_hours,
        "damages": damages,
    }


def run_event(
    windts_path: Union[Path, str],
    properties: List[Dict[str, Any]],
    output_path: Union[Path, str],
) -> Dict[str, Any]:
    """Read one windts file, compute damage, write damage/EVT-NNNN.json.

    Returns the in-memory payload so callers can aggregate without
    re-reading from disk.
    """
    windts = load_event_peaks(windts_path)
    payload = build_event_damage(windts, properties)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(payload, f, indent=2)

    return payload


def run_event_directory(
    windts_dir: Union[Path, str],
    damage_dir: Union[Path, str],
    properties: List[Dict[str, Any]],
) -> List[Path]:
    """Run damage for every EVT-NNNN.json in `windts_dir`.

    Returns the list of damage JSON paths written, sorted.
    """
    windts_dir = Path(windts_dir)
    damage_dir = Path(damage_dir)
    written: List[Path] = []
    for windts_path in sorted(windts_dir.glob("EVT-*.json")):
        out_path = damage_dir / windts_path.name
        run_event(windts_path, properties, out_path)
        written.append(out_path)
    return written
