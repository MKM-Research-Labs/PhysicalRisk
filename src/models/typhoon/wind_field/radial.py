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

"""Symmetric radial wind profile — spec eqs. (22), (23), and (25).

Piecewise profile:

    Inner core   (0 <= r < R_max):
        V_sym(r) = V_max * [alpha_eye + (1 - alpha_eye) * (r / R_max)]

    Outer        (r >= R_max):
        V_sym(r) = V_max * exp(-((r - R_max) / L)^p)

The outer-decay length scale L is determined by anchoring the profile at
the outer radius:

    V_sym(R_outer) = V_outer_ref       (gale-force by default)

    => L = (R_outer - R_max) / (-ln(V_outer_ref / V_max))^(1/p)

When V_max <= V_outer_ref the calibration is undefined (the storm is at
or below the reference wind speed at its eyewall). A geometric fallback
L = R_outer - R_max is used; the profile is no longer physically
realistic for sub-gale storms but the model remains evaluable.

A future phase can swap a Holland-style backend in here without changing
the calling interface (see plan, Phase 1 non-goals).
"""

import math


__all__ = [
    "calibrate_outer_decay_length",
    "symmetric_profile",
]


def calibrate_outer_decay_length(
    v_max_ms: float,
    r_max_km: float,
    r_outer_km: float,
    v_outer_ref_ms: float,
    outer_shape_p: float,
) -> float:
    """Solve V_sym(R_outer) = v_outer_ref for the outer-decay length L.

    See module docstring. Falls back to L = R_outer - R_max when the
    calibration is undefined (V_max <= v_outer_ref) or when inputs would
    produce a non-positive L.
    """
    delta_r = r_outer_km - r_max_km
    if delta_r <= 0.0:
        # Pathological geometry — invariant R_max < R_outer is enforced by
        # the transition layer, but be defensive: use 1 km as a safe floor.
        return 1.0

    if v_max_ms <= v_outer_ref_ms or v_max_ms <= 0.0:
        return delta_r

    ratio = v_outer_ref_ms / v_max_ms
    neg_ln = -math.log(ratio)   # > 0 because ratio in (0, 1)
    if neg_ln <= 0.0:
        return delta_r

    denom = neg_ln ** (1.0 / outer_shape_p)
    if denom <= 0.0:
        return delta_r

    return delta_r / denom


def symmetric_profile(
    r_km: float,
    r_max_km: float,
    v_max_ms: float,
    alpha_eye: float,
    outer_decay_length_km: float,
    outer_shape_p: float,
) -> float:
    """Symmetric V_sym(r) in m/s. Spec eq. (23), piecewise.

    Args:
        r_km: radial distance from storm center (km), must be >= 0
        r_max_km: radius of maximum wind (km), > 0
        v_max_ms: peak sustained wind (m/s)
        alpha_eye: inner-core floor ratio (0..1) — V at the center is
            alpha_eye * V_max
        outer_decay_length_km: L (km), pre-calibrated via
            calibrate_outer_decay_length
        outer_shape_p: exponent p in the outer decay envelope
    """
    if r_max_km <= 0.0:
        return 0.0
    if r_km < 0.0:
        r_km = 0.0

    if r_km < r_max_km:
        # Linear ramp from alpha_eye * V_max at the center to V_max at R_max.
        return v_max_ms * (alpha_eye + (1.0 - alpha_eye) * (r_km / r_max_km))

    # Outer decay.
    if outer_decay_length_km <= 0.0:
        return v_max_ms   # degenerate; flat at V_max
    z = (r_km - r_max_km) / outer_decay_length_km
    return v_max_ms * math.exp(-(z ** outer_shape_p))
