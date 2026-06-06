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

"""Systematic resampling for the particle filter."""

import numpy as np


def systematic_resample(weights: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Systematic resampling: pick N samples on a uniform grid offset by U.

    Returns indices into the original particle list. Each weight w_i is
    proportional to the expected number of times its index appears.

    Properties of systematic resampling vs multinomial:
    - Lower Monte Carlo variance for the same N.
    - Indices stay sorted (cheap memory access on contiguous arrays).
    - Reproducible under a single uniform draw.
    """
    n = len(weights)
    if n == 0:
        return np.empty(0, dtype=int)

    # Normalise defensively in case the caller passed unnormalised weights.
    total = float(np.sum(weights))
    if total <= 0.0:
        raise ValueError("systematic_resample requires positive total weight")
    w = np.asarray(weights, dtype=float) / total

    cum = np.cumsum(w)
    # Floating-point guard: ensure the last cumulant is exactly 1.0 so the
    # while-loop below cannot run off the end.
    cum[-1] = 1.0

    u0 = float(rng.uniform()) / n
    indices = np.zeros(n, dtype=int)
    j = 0
    for i in range(n):
        u = u0 + i / n
        while u > cum[j] and j < n - 1:
            j += 1
        indices[i] = j
    return indices
