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

"""Gamma-shaped hydrograph template functions."""

import math

import numpy as np


def gamma_shape(u: float, alpha: float) -> float:
    """Dimensionless gamma-like hydrograph shape, normalised to peak = 1.

    Raw formula: f(u) = (u/alpha)^alpha * exp(alpha - u/alpha)
    Peak at u = alpha^2 with raw value alpha^alpha.
    Normalised: phi(u) = f(u) / alpha^alpha.

    Args:
        u: Dimensionless time fraction in [0, 1].
        alpha: Shape parameter (0 < alpha <= 1).
            Small alpha → fast rise, long tail (flashy).
            Large alpha → broad symmetric peak.

    Returns:
        Shape value in [0, 1].  Zero outside (0, 1].
    """
    if u <= 0 or u > 1 or alpha <= 0:
        return 0.0
    ratio = u / alpha
    # f(u) = exp(alpha * ln(u/alpha) + alpha - u/alpha)
    # Normalise by dividing by alpha^alpha = exp(alpha * ln(alpha))
    log_val = alpha * math.log(ratio) + alpha - ratio
    log_norm = alpha * math.log(alpha)  # log of peak value
    return math.exp(log_val - log_norm)


def gamma_shape_array(hours: np.ndarray, start_hour: float,
                      duration_hours: float, alpha: float) -> np.ndarray:
    """Vectorised gamma shape over an array of absolute hours.

    Args:
        hours: 1-D array of hour indices (e.g. 0..167).
        start_hour: Pulse start time (hours).
        duration_hours: Pulse duration (hours, > 0).
        alpha: Gamma shape parameter.

    Returns:
        Array same shape as *hours* with values in [0, 1].
    """
    if duration_hours <= 0 or alpha <= 0:
        return np.zeros_like(hours, dtype=float)

    u = (hours - start_hour) / duration_hours
    result = np.zeros_like(hours, dtype=float)
    mask = (u > 0) & (u <= 1)
    um = u[mask]
    ratio = um / alpha
    log_val = alpha * np.log(ratio) + alpha - ratio
    log_norm = alpha * math.log(alpha)
    result[mask] = np.exp(log_val - log_norm)
    return result
