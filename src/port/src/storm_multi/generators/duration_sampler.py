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
Extended duration sampler for Storm Generator v2.0.

Supports up to 240-hour durations for individual storms within sequences.
Uses triangular distribution (min, mode, max) per intensity category.
"""

import numpy as np

# Extended duration parameters — spec Section 3.1
# (min_hours, mode_hours, max_hours) — triangular distribution
DURATION_PARAMS = {
    "minimal": (2, 6, 12),
    "baseline": (6, 12, 24),
    "moderate": (12, 30, 60),        # 2.5 day max
    "severe": (24, 48, 96),          # 4 day max
    "extreme": (36, 72, 144),        # 6 day max
    "catastrophic": (48, 120, 240),  # 10 day max
}


def sample_duration(
    intensity_category: str,
    rng: np.random.RandomState = None,
) -> float:
    """Sample storm duration from triangular distribution.

    Args:
        intensity_category: One of minimal, baseline, moderate,
            severe, extreme, catastrophic.
        rng: Random state for reproducibility. If None, uses numpy default.

    Returns:
        Duration in hours (float, rounded to nearest integer).

    Raises:
        ValueError: If intensity_category is not recognized.
    """
    if intensity_category not in DURATION_PARAMS:
        raise ValueError(
            f"Unknown intensity category: {intensity_category}. "
            f"Expected one of {list(DURATION_PARAMS.keys())}"
        )

    low, mode, high = DURATION_PARAMS[intensity_category]

    if rng is None:
        rng = np.random.RandomState()

    duration = rng.triangular(low, mode, high)
    return round(duration)


def get_max_duration(intensity_category: str) -> float:
    """Return the maximum possible duration for a category."""
    return DURATION_PARAMS[intensity_category][2]


def get_duration_range(intensity_category: str) -> tuple:
    """Return (min, mode, max) duration tuple for a category."""
    return DURATION_PARAMS[intensity_category]
