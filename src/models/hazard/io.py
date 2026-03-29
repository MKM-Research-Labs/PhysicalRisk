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

"""
I/O functions for hazard curve data — loading storms/gauges,
saving hazard curves, and the main build_hazard_curves() entry point.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)

from port.cdm.gauge import FloodGaugeCDM

from .builder import HazardCurveBuilder
from .data_structures import GaugeHazardCurve


def load_storms(input_path: Path) -> list:
    """Load storms from JSON file (legacy storms.json format)."""
    with open(input_path) as f:
        data = json.load(f)
    return data['storms']


def load_storms_from_sequences(sequences_path: Path) -> list:
    """Flatten storm sequences into individual storm dicts for the hazard model.

    Each SequenceStorm is extracted from its parent sequence and mapped to the
    legacy storm dict schema expected by GaugeResponseModel:
      - storm_id
      - effective_precipitation_mm  (from precipitation_mm)
      - duration_hours
      - intensity_factor
      - intensity_category
      - peak_position
    """
    with open(sequences_path) as f:
        data = json.load(f)

    storms = []
    for seq in data.get("sequences", []):
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


def load_gauges(input_path: Path) -> list:
    """
    Load gauges from portfolio JSON file using CDM for proper mapping.

    The gauge portfolio JSON structure (from gauge.py):
    {
        "flood_gauges": [{FloodGauge: {...}}, ...],
        "generation_metadata": {...}
    }

    Uses FloodGaugeCDM.create_mapping() to flatten the nested CDM structure
    into a consistent flat dictionary format.
    """
    with open(input_path) as f:
        data = json.load(f)

    raw_gauges = data.get('flood_gauges', [])

    if not raw_gauges:
        raise ValueError(
            f"No gauges found in {input_path}. "
            f"Expected 'flood_gauges' key. Found keys: {list(data.keys())}"
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


def save_hazard_curves(
    hazard_curves: Dict[str, GaugeHazardCurve],
    output_path: Path,
    catchment_id: str,
    metadata: Dict = None
) -> Path:
    """Save hazard curves to JSON file."""
    output_data = {
        'metadata': {
            'catchment_id': catchment_id,
            'generated_at': datetime.now().isoformat(),
            'num_gauges': len(hazard_curves),
            'schema_version': '2.0',
            **(metadata or {})
        },
        'hazard_curves': {}
    }

    for gauge_id, curve in hazard_curves.items():
        curve_dict = asdict(curve)
        curve_dict['curve_points'] = [asdict(p) for p in curve.curve_points]
        curve_dict['term_structure_alert'] = [asdict(p) for p in curve.term_structure_alert]
        curve_dict['term_structure_warning'] = [asdict(p) for p in curve.term_structure_warning]
        curve_dict['term_structure_severe'] = [asdict(p) for p in curve.term_structure_severe]
        output_data['hazard_curves'][gauge_id] = curve_dict

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return output_path


def save_gauge_storm_responses(
    responses: Dict[str, list],
    gaugets_dir: Path,
    catchment_id: str
) -> Path:
    """
    Save gauge storm responses into per-gauge files in the gaugets/ directory.

    Merges storm_responses into existing per-gauge files created by
    GaugeTimeSeriesGenerator, or creates new files if they don't exist.

    Args:
        responses: Dict mapping gauge_id → list of GaugeResponse objects
        gaugets_dir: Path to gaugets/ directory
        catchment_id: Catchment identifier
    """
    gaugets_dir.mkdir(parents=True, exist_ok=True)
    num_storms = len(next(iter(responses.values()), []))

    for gauge_id, gauge_responses in responses.items():
        gauge_file = gaugets_dir / f"{gauge_id}.json"

        # Load existing per-gauge file if it exists
        if gauge_file.exists():
            with open(gauge_file) as f:
                gauge_data = json.load(f)
        else:
            gauge_data = {
                "gauge_id": gauge_id,
                "metadata": {
                    "catchment": catchment_id,
                    "generated_at": datetime.now().isoformat(),
                },
            }

        # Add/update storm responses section
        gauge_data['storm_responses'] = {
            'num_storms': num_storms,
            'responses': [
                {
                    'storm_id': r.storm_id,
                    'base_level_m': round(r.base_level_m, 4),
                    'level_change_m': round(r.level_change_m, 4),
                    'peak_level_m': round(r.peak_level_m, 4),
                    'exceeded_alert': r.exceeded_alert,
                    'exceeded_warning': r.exceeded_warning,
                    'exceeded_severe': r.exceeded_severe,
                }
                for r in gauge_responses
            ]
        }

        with open(gauge_file, 'w') as f:
            json.dump(gauge_data, f, indent=2)

    return gaugets_dir


def build_hazard_curves(
    output_dir: Path,
    catchment_id: str,
    distribution: str = 'gev',
    verbose: bool = True
) -> Dict:
    """
    Build hazard curves from storm sequences and gauge data.

    Expects:
        - output_dir/storm_sequences.json (from storm_multi via --stressm)
        - output_dir/gauge.json (from gauge.py)

    Args:
        output_dir: Input/output directory
        catchment_id: Catchment identifier
        distribution: 'gev' or 'gumbel'
        verbose: Print progress

    Returns:
        Dictionary with results
    """
    sequences_path = output_dir / "storm_sequences.json"
    if not sequences_path.exists():
        raise FileNotFoundError(
            f"storm_sequences.json not found in {output_dir}. "
            "Run 'python app.py port --stressm' first."
        )

    storms = load_storms_from_sequences(sequences_path)
    if verbose:
        logger.info("Loaded %d individual storms from sequences at %s",
                    len(storms), sequences_path)

    gauges_path = output_dir / "gauge.json"
    if not gauges_path.exists():
        raise FileNotFoundError(
            f"gauge.json not found in {output_dir}. "
            "Run 'python port.py --gauges' first."
        )

    gauges = load_gauges(gauges_path)
    if verbose:
        logger.info("Loaded %d gauges from %s", len(gauges), gauges_path)

    builder = HazardCurveBuilder(
        gauges=gauges,
        storms=storms,
        force_gumbel=(distribution == 'gumbel'),
        verbose=verbose
    )

    hazard_curves, responses = builder.build()

    output_path = output_dir / "gaugehc.json"
    metadata = {
        'num_storms': len(storms),
        'distribution': distribution
    }
    save_hazard_curves(hazard_curves, output_path, catchment_id, metadata)

    if verbose:
        logger.info("Saved hazard curves to: %s", output_path)

    # Save gauge storm responses into per-gauge files
    gaugets_dir = output_dir / "gaugets"
    save_gauge_storm_responses(responses, gaugets_dir, catchment_id)

    if verbose:
        total_responses = sum(len(r) for r in responses.values())
        logger.info("Saved %d gauge storm responses to: %s", total_responses, gaugets_dir)

    avg_alert = np.mean([c.annual_flood_prob_alert for c in hazard_curves.values()])
    avg_warning = np.mean([c.annual_flood_prob_warning for c in hazard_curves.values()])
    avg_severe = np.mean([c.annual_flood_prob_severe for c in hazard_curves.values()])

    if verbose:
        logger.info("Average annual flood probabilities: Alert=%.2f%%, Warning=%.2f%%, Severe=%.2f%%",
                    avg_alert * 100, avg_warning * 100, avg_severe * 100)

    return {
        'hazard_curves': hazard_curves,
        'output_path': output_path,
        'summary': {
            'num_gauges': len(hazard_curves),
            'num_storms': len(storms),
            'avg_annual_prob_alert': avg_alert,
            'avg_annual_prob_warning': avg_warning,
            'avg_annual_prob_severe': avg_severe
        }
    }
