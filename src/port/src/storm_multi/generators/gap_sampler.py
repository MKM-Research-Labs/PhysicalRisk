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
Inter-storm gap sampler for Storm Generator v2.0.

Gaps must be long enough to show observable river level decline
between storms. Gap type varies by sequence type to create different
drainage patterns.
"""

import numpy as np

from ..core.data_structures import SEQUENCE_GAP_TYPE, GapType, SequenceType

# Inter-storm gap parameters — spec Section 3.2
# (min_hours, mode_hours, max_hours) — triangular distribution
GAP_PARAMS = {
    GapType.SHORT: (6, 18, 36),      # Minimal drainage
    GapType.MEDIUM: (24, 48, 72),     # Partial drainage
    GapType.LONG: (48, 96, 144),      # Substantial drainage
}


def sample_gap(
    sequence_type: SequenceType,
    rng: np.random.RandomState = None,
) -> float:
    """Sample an inter-storm gap for a given sequence type.

    Physical interpretation:
      - Medium gaps (24-72h): river levels drop 30-60% from Storm 1 peak
      - Short gaps (6-36h): minimal drainage, high compounding risk
      - Long gaps (48-144h): 60-80% recovery toward baseline

    Args:
        sequence_type: Type of sequence (determines gap category).
        rng: Random state for reproducibility.

    Returns:
        Gap duration in hours (rounded to nearest integer).
    """
    if sequence_type == SequenceType.ISOLATED:
        return 0.0

    gap_type = SEQUENCE_GAP_TYPE[sequence_type]
    low, mode, high = GAP_PARAMS[gap_type]

    if rng is None:
        rng = np.random.RandomState()

    return round(rng.triangular(low, mode, high))


def get_gap_range(sequence_type: SequenceType) -> tuple:
    """Return (min, mode, max) gap parameters for a sequence type."""
    if sequence_type == SequenceType.ISOLATED:
        return (0, 0, 0)
    gap_type = SEQUENCE_GAP_TYPE[sequence_type]
    return GAP_PARAMS[gap_type]
