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
Flood depth-damage calculations.

Public interface:
    is_prs_flood          — event filter for PRS pricing
    scalar_depth_damage   — piecewise-linear damage ratio (baseline, no BRI)
    bri_stilt             — signed depth offset derived from BRI scores
    bri_depth_damage      — damage ratio with floor level + BRI stilt applied
"""

import math

from config.damage import (
    BRI_COMPOSITE_BETA_M,
    BRI_COMPOSITE_REFERENCE,
    BRI_FLOOD_ALPHA_M,
    BRI_FLOOD_REFERENCE,
    BRI_STILT_MAX_M,
    DAMAGE_POINTS,
    DD_POLY_COEFFS,
    DEPTH_POINTS,
)

# Small floor to prevent ln(0); scores below this are treated as effectively zero.
_LN_FLOOR = 1e-6


def is_prs_flood(event: dict) -> bool:
    """True if the flood event counts toward PRS pricing.

    Requires both:
    - The property actually flooded (flood_depth > 0)
    - The controlling gauge exceeded the severe threshold
    """
    return event.get('flooded', False) and event.get('exceeded_severe', False)


def scalar_depth_damage(depth: float) -> float:
    """Piecewise-linear depth-damage lookup (baseline — no floor level, no BRI).

    Args:
        depth: Flood depth in metres above floor level.

    Returns:
        Damage ratio in [0, 1].
    """
    if depth <= 0:
        return 0.0
    if depth >= DEPTH_POINTS[-1]:
        return 1.0
    for i in range(len(DEPTH_POINTS) - 1):
        if DEPTH_POINTS[i] <= depth < DEPTH_POINTS[i + 1]:
            t = (depth - DEPTH_POINTS[i]) / (DEPTH_POINTS[i + 1] - DEPTH_POINTS[i])
            return DAMAGE_POINTS[i] + t * (DAMAGE_POINTS[i + 1] - DAMAGE_POINTS[i])
    return 0.0


def bri_stilt(bri_flood_score: float, bri_composite_score: float) -> float:
    """Signed depth offset (metres) derived from BRI scores.

    Positive stilt → property is hardened; effective flood depth is reduced.
    Negative stilt → property is more vulnerable than baseline; depth is increased.
    No clamp on the stilt itself — the signed aggregate is returned directly.
    The max(0, …) is applied by the caller on effective depth, not here.

    The stilt is capped at ±BRI_STILT_MAX_M to prevent extreme log values at
    very high or very low BRI scores from producing implausible depth shifts.

    Args:
        bri_flood_score:     BRIFloodScore in [0, 1].
        bri_composite_score: BRIScore (composite) in [0, 1].

    Returns:
        Signed stilt in metres.
    """
    flood_term = BRI_FLOOD_ALPHA_M * math.log(
        max(bri_flood_score, _LN_FLOOR) / BRI_FLOOD_REFERENCE
    )
    composite_term = BRI_COMPOSITE_BETA_M * math.log(
        max(bri_composite_score, _LN_FLOOR) / BRI_COMPOSITE_REFERENCE
    )
    raw = flood_term + composite_term
    return max(-BRI_STILT_MAX_M, min(BRI_STILT_MAX_M, raw))


def bri_depth_damage(
    depth: float,
    floor_level: float,
    bri_flood_score: float,
    bri_composite_score: float,
) -> float:
    """Damage ratio using the degree-5 polynomial with floor level and BRI stilt.

    Effective depth = max(0,  depth  −  floor_level  −  stilt)

    The stilt is a signed weighted aggregate of two log-differential terms:
        α · ln(bri_flood / μ_flood) + β · ln(bri_composite / μ_composite)

    Below-reference BRI scores produce a negative stilt, increasing effective
    depth (more damage than baseline). Above-reference scores reduce it.

    Args:
        depth:               Raw flood depth in metres at the property.
        floor_level:         Height of lowest occupied floor above ground (m).
        bri_flood_score:     BRIFloodScore in [0, 1].
        bri_composite_score: BRIScore (composite) in [0, 1].

    Returns:
        Damage ratio in [0, 1].
    """
    stilt = bri_stilt(bri_flood_score, bri_composite_score)
    effective = max(0.0, depth - floor_level - stilt)
    if effective <= 0.0:
        return 0.0
    raw = sum(c * effective ** (i + 1) for i, c in enumerate(DD_POLY_COEFFS))
    return min(1.0, max(0.0, raw))
