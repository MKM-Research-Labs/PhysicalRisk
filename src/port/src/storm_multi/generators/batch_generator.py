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
Batch generator for Storm Generator v2.0.

Generates large event sets (default 10,000 sequences) across all
intensity categories using configurable weights.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

from config.port import DEFAULT_INTENSITY_WEIGHTS
from ..core.data_structures import StormSequence
from .sequence_generator import SequenceGenerator

logger = logging.getLogger(__name__)

# DEFAULT_INTENSITY_WEIGHTS imported from config/port.py (Spec Section 4.3)

# Base intensity parameters per category (mean, std) — aligned with storm.py
BASE_INTENSITY_PARAMS = {
    "minimal":      (0.3, 0.10),
    "baseline":     (0.6, 0.15),
    "moderate":     (1.0, 0.20),
    "severe":       (1.8, 0.30),
    "extreme":      (3.0, 0.50),
    "catastrophic": (5.0, 0.80),
}


def generate_event_set(
    count: int = 10000,
    catchment_id: str = "thames",
    intensity_weights: Optional[Dict[str, float]] = None,
    force_sequence_type: Optional[str] = None,
    seed: int = 42,
) -> List[StormSequence]:
    """Generate N storm sequences across intensity categories.

    Each sequence is independently sampled: intensity category drawn from
    weights, base_intensity drawn from a Normal distribution per category,
    then SequenceGenerator assembles the full StormSequence.

    Args:
        count: Number of sequences to generate.
        catchment_id: Catchment identifier (e.g. "thames").
        intensity_weights: Dict mapping category name → probability weight.
            Must sum to 1.0. Defaults to spec Section 4.3 weights
            (moderate 40%, severe 35%, extreme 20%, catastrophic 5%).
        force_sequence_type: If set, all sequences have this type
            (isolated / doublet / cluster / persistent). Useful for testing.
        seed: Random seed for reproducibility.

    Returns:
        List of StormSequence objects, length == count.
    """
    weights = intensity_weights or DEFAULT_INTENSITY_WEIGHTS

    # Normalise weights in case they don't sum to exactly 1.0
    categories = list(weights.keys())
    raw_weights = np.array([weights[c] for c in categories], dtype=float)
    probs = raw_weights / raw_weights.sum()

    rng = np.random.RandomState(seed)
    gen = SequenceGenerator(catchment_id=catchment_id, seed=seed)

    # Pre-draw all category assignments
    category_draws = rng.choice(len(categories), size=count, p=probs)

    sequences: List[StormSequence] = []
    for i, cat_idx in enumerate(category_draws):
        category = categories[cat_idx]
        mean, std = BASE_INTENSITY_PARAMS.get(category, (1.0, 0.20))
        base_intensity = max(0.1, rng.normal(mean, std))

        seq = gen.generate(
            intensity_category=category,
            base_intensity=base_intensity,
            force_sequence_type=force_sequence_type,
        )
        sequences.append(seq)

        if (i + 1) % 1000 == 0:
            logger.info("Generated %d / %d sequences", i + 1, count)

    logger.info(
        "Batch complete: %d sequences for catchment '%s'", count, catchment_id
    )
    return sequences
