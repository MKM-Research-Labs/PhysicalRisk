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

"""Motion-linked azimuthal asymmetry — spec eqs. (26), (27), (28).

Real tropical cyclones are not azimuthally symmetric; storm translation
adds vectorially to the rotational flow, enhancing winds on one side of
the storm and suppressing them on the other. The first-order correction:

    V(r, theta) = V_sym(r) * (1 + epsilon * cos(theta - phi))
    epsilon     = min(eps_max, c_eps * U / (V_max + eta))
    phi         = motion_azimuth + asymmetry_phase_offset_deg

Units note: translation speed U enters the epsilon formula in the same
units as V_max — both are wind speeds. The state stores U in km/h and
V_max in m/s, so a unit conversion is applied here (1 km/h = 1/3.6 m/s).

The asymmetry phase offset places the peak relative to the direction of
motion. The NH convention (peak on the right of motion) corresponds to
+90 deg.
"""

import math


__all__ = [
    "KMH_TO_MS",
    "compute_epsilon",
    "compute_phi_deg",
    "asymmetry_factor",
]


# 1 km/h = 1000 m / 3600 s.
KMH_TO_MS: float = 1.0 / 3.6


def compute_epsilon(
    translation_speed_kmh: float,
    v_max_ms: float,
    eps_max: float,
    c_eps: float,
    eta_ms: float,
) -> float:
    """epsilon = min(eps_max, c_eps * U / (V_max + eta)), bounded to [0, 1)."""
    u_ms = translation_speed_kmh * KMH_TO_MS
    eps = c_eps * u_ms / (v_max_ms + eta_ms)
    if eps < 0.0:
        eps = 0.0
    return min(eps_max, eps)


def compute_phi_deg(
    motion_azimuth_deg: float,
    asymmetry_phase_offset_deg: float,
) -> float:
    """phi = motion azimuth + phase offset, wrapped to [0, 360)."""
    return (motion_azimuth_deg + asymmetry_phase_offset_deg) % 360.0


def asymmetry_factor(theta_deg: float, phi_deg: float, epsilon: float) -> float:
    """1 + epsilon * cos(theta - phi). Compass arithmetic handled via
    radian conversion; cosine handles wrap-around naturally.
    """
    delta_rad = math.radians(theta_deg - phi_deg)
    return 1.0 + epsilon * math.cos(delta_rad)
