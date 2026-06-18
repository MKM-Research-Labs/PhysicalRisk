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

"""``build_hazard_curves`` — the main hazard-curve build entry point."""

import logging
from pathlib import Path
from typing import Dict

import numpy as np

from ..builder import HazardCurveBuilder
from ._load import load_gauges, load_storms_from_sequences
from ._save import save_gauge_storm_responses, save_hazard_curves

logger = logging.getLogger(__name__)


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
