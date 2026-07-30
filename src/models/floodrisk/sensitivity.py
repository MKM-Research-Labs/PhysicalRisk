# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""What-if sensitivity for the property flood-response model (MKM-PF-001).

The model's single most material uncertain input is the **flood depth** it
estimates at a property: the water-surface elevation is interpolated from a
sparse gauge network (inverse-distance weighting) and differenced against a DEM
ground level, so both an interpolation bias and a DEM error land directly on the
effective depth ``d = max(0, depth - floor_level - stilt)``. Everything the model
prices flows from ``d`` through the calibrated depth-damage curve, so quantifying
how the damage ratio responds to a depth error is the model's key sensitivity.

The response has two distinct regimes, both surfaced here:

* **Intensive margin** (given a flood, how much damage): the depth-damage curve
  ``g(d) = Σ cᵢ·dⁱ`` (``config.damage.DD_POLY_COEFFS``) is concave and saturating,
  so its elasticity ``E(d) = d·g'(d)/g(d)`` is below one everywhere — a depth
  error is *attenuated* into the damage ratio, most so in deep water. This is
  reassuring: intensive-margin loss is robust to modest depth error.

* **Extensive margin** (whether the property floods at all): because ``d`` is a
  thresholded difference, a property sitting just above its floor+BRI threshold
  flips between zero and positive damage under a small depth bias. The marginal
  damage per metre ``g'(d)`` is largest at the toe, so a systematic depth bias
  moves the *flooded count* — the documented inverse-distance dilution failure
  mode — far more than it moves any single property's damage ratio.

This module is pure and data-free. It composes the model's own calibrated curve
(``DD_POLY_COEFFS``) over a grid of candidate depth errors and reports the damage
response, its local elasticity and marginal slope in closed form. Nothing here is
wired into pricing; it is a diagnostic a validation report or the MRC calls.
"""
from typing import Dict, Mapping, Sequence

from config.damage import DD_POLY_COEFFS


def poly_damage(depth: float) -> float:
    """Depth-damage ratio from the calibrated polynomial, clamped to [0, 1].

    ``g(d) = Σ cᵢ·d^(i+1)`` with coefficients ``config.damage.DD_POLY_COEFFS`` —
    the same curve the BRI production path evaluates on effective depth. A
    non-positive depth returns 0 (no flood, no damage).
    """
    if depth <= 0.0:
        return 0.0
    raw = sum(c * depth ** (i + 1) for i, c in enumerate(DD_POLY_COEFFS))
    return min(1.0, max(0.0, raw))


def poly_damage_slope(depth: float) -> float:
    """Marginal damage per metre ``g'(d) = Σ (i+1)·cᵢ·dⁱ`` (unclamped derivative).

    Returns 0 for non-positive depth. Where ``g`` is on its [0, 1] clamp the true
    marginal is 0; callers reading the slope near saturation should note the raw
    polynomial derivative is returned (the interior gradient).
    """
    if depth <= 0.0:
        return 0.0
    return sum((i + 1) * c * depth ** i for i, c in enumerate(DD_POLY_COEFFS))


def damage_elasticity(depth: float) -> float:
    """Elasticity ``E(d) = d·g'(d)/g(d)`` — the intensive-margin passthrough.

    A 1% error in estimated depth maps to an ``E(d)%`` error in the damage ratio.
    Below one everywhere on this concave curve, so depth error is attenuated; it
    rises toward one at the toe (``d → 0``) where the curve is near-linear.
    Returns 0 where damage is 0 (no flood — the extensive-margin regime, which
    ``depth_bias_sensitivity`` handles).
    """
    g = poly_damage(depth)
    if g <= 0.0:
        return 0.0
    return depth * poly_damage_slope(depth) / g


def depth_damage_sensitivity(
    base_depth: float,
    factors: Sequence[float],
) -> Dict:
    """Quantify how the damage ratio responds to a multiplicative depth error.

    For each ``factor`` on the estimated effective depth, reports the repriced
    damage ratio, its change relative to the base, and the local elasticity and
    marginal slope so the response is stated in closed form, not only sampled.

    Args:
        base_depth: Effective flood depth (m) the model estimates at the property.
        factors:    Multiplicative depth errors to probe (e.g. 0.8 = 20% shallow).

    Returns:
        ``{"base_depth", "base_damage", "rows": [...]}`` where each row carries
        ``factor``, ``depth``, ``damage``, ``damage_rel_to_base``, ``elasticity``
        and ``marginal_slope_per_m``.
    """
    base_damage = poly_damage(base_depth)
    rows = []
    for factor in factors:
        depth = base_depth * factor
        damage = poly_damage(depth)
        rows.append({
            "factor": factor,
            "depth": depth,
            "damage": damage,
            "damage_rel_to_base": (damage / base_damage) if base_damage > 0 else float("nan"),
            "elasticity": damage_elasticity(depth),
            "marginal_slope_per_m": poly_damage_slope(depth),
        })
    return {"base_depth": base_depth, "base_damage": base_damage, "rows": rows}


def depth_bias_sensitivity(
    base_depth: float,
    biases_m: Sequence[float],
) -> Dict:
    """Quantify the response to an *additive* depth bias in metres.

    A DEM error or interpolation bias is naturally additive in metres, and near
    the flood threshold it governs the extensive margin (whether the property
    floods). For each signed bias ``Δ`` this reports the damage at ``base + Δ``,
    whether the property floods there (``flooded = depth > 0``), and the change in
    damage — so a bias that flips a property across its threshold shows up as a
    step from zero.

    Args:
        base_depth: Effective flood depth (m) the model estimates.
        biases_m:   Signed additive depth errors in metres (e.g. -0.3 = 0.3 m too
                    shallow).

    Returns:
        ``{"base_depth", "base_damage", "rows": [...]}`` where each row carries
        ``bias_m``, ``depth``, ``flooded``, ``damage`` and ``damage_change``.
    """
    base_damage = poly_damage(base_depth)
    rows = []
    for bias in biases_m:
        depth = base_depth + bias
        damage = poly_damage(depth)
        rows.append({
            "bias_m": bias,
            "depth": depth,
            "flooded": depth > 0.0,
            "damage": damage,
            "damage_change": damage - base_damage,
        })
    return {"base_depth": base_depth, "base_damage": base_damage, "rows": rows}


def damage_distribution(
    base_depth: float,
    depth_percentiles: Mapping[str, float],
) -> Dict:
    """Propagate an uncertain depth to the induced damage-ratio distribution.

    ``g`` is monotone increasing in depth, so an uncertain depth given by
    percentile *multipliers* maps exactly (no Monte-Carlo noise) onto damage
    percentiles. The ``passthrough`` at each percentile is the relative damage
    change divided by the relative depth change — the discrete analogue of the
    elasticity, and below one on this concave curve.

    Args:
        base_depth:        Median effective depth (m); the ``"p50"`` multiplier
                           (or 1.0) anchors the base.
        depth_percentiles: Percentile label → multiplicative depth factor, e.g.
                           ``{"p05": 0.6, "p50": 1.0, "p95": 1.4}``.

    Returns:
        ``{"base_depth", "median_damage", "rows": [...]}`` where each row carries
        ``percentile``, ``depth_factor``, ``depth``, ``damage``,
        ``damage_rel_to_median`` and ``passthrough``.
    """
    median_factor = depth_percentiles.get("p50", 1.0)
    median_depth = base_depth * median_factor
    median_damage = poly_damage(median_depth)
    rows = []
    for label, factor in depth_percentiles.items():
        depth = base_depth * factor
        damage = poly_damage(depth)
        damage_rel = (damage / median_damage) if median_damage > 0 else float("nan")
        depth_rel = (factor / median_factor) if median_factor > 0 else float("nan")
        if depth_rel == 1.0 or depth_rel != depth_rel:  # base row or undefined
            passthrough = float("nan")
        else:
            passthrough = (damage_rel - 1.0) / (depth_rel - 1.0)
        rows.append({
            "percentile": label,
            "depth_factor": factor,
            "depth": depth,
            "damage": damage,
            "damage_rel_to_median": damage_rel,
            "passthrough": passthrough,
        })
    return {"base_depth": base_depth, "median_damage": median_damage, "rows": rows}
