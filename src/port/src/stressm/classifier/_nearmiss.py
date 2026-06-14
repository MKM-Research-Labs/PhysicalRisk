# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Near-miss hydrograph augmentation for transition-zone gradient data."""

import math

import numpy as np

# Log-transform & near-miss constants — centralised in config/port.py
from config.port import (
    LOG_END as _LOG_END,
    LOG_EPS as _LOG_EPS,
    NUM_CLASSIFIER_HOURS as _NUM_HOURS,
    NEARMISS_COUNT as _NEARMISS_COUNT,
    NEARMISS_LOW as _NEARMISS_LOW,
    NEARMISS_HIGH as _NEARMISS_HIGH,
)


def _generate_nearmiss_vectors(
    severe_l: float,
    base_level: float,
    rng,
) -> list:
    """Synthesise near-miss hydrographs that peak at 80–99% of severe.

    Each hydrograph uses a sin(rise) + exp(decay) shape — the same physical
    model as the real storm response — but scaled so the peak sits just below
    the severe threshold.  All 168 hours carry flood_flag=0.

    This provides the GBM with gradient data in the transition zone so P(flood)
    rises smoothly (e.g. 10% → 30% → 60% → 80%) rather than jumping 5% → 95%.
    """
    vectors = []
    for _ in range(_NEARMISS_COUNT):
        # Peak at a random fraction of severe level (80–99%)
        peak_frac = rng.uniform(_NEARMISS_LOW, _NEARMISS_HIGH)
        peak_level = severe_l * peak_frac

        # Random rise time (10–50 hours) and decay rate
        rise_hours = rng.randint(10, 50)
        decay_rate = rng.uniform(0.02, 0.08)

        # Build 168-hour hydrograph: sin rise → peak → exp decay
        levels = np.full(_NUM_HOURS, base_level, dtype=float)
        for h in range(_NUM_HOURS):
            if h < rise_hours:
                # Rising limb — sinusoidal
                phase = (h / rise_hours) * (math.pi / 2)
                levels[h] = base_level + (peak_level - base_level) * math.sin(phase)
            else:
                # Falling limb — exponential decay back to base
                dt = h - rise_hours
                levels[h] = base_level + (peak_level - base_level) * math.exp(-decay_rate * dt)

        # Convert to log-space features (same as real sequences)
        log_hs = [math.log(max(lv / severe_l, _LOG_EPS)) for lv in levels]

        for h in range(_NUM_HOURS):
            log_t = math.log((h + 1) / _LOG_END)
            delta = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
            prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
            delta2 = delta - prev_delta

            # ALL near-miss vectors are label=0 — peak is below severe
            vectors.append([
                round(log_hs[h], 6),
                round(log_t, 6),
                round(delta, 6),
                round(delta2, 6),
                0,  # flood_flag = 0 (never breaches severe)
            ])

    return vectors
