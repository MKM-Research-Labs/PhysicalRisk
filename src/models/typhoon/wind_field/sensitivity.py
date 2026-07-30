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

"""What-if sensitivity for the tropical-cyclone wind-field (MKM-TC-001).

The model prices a per-location **peak wind**, and that quantity has two
materially uncertain drivers, both surfaced here in closed form over the model's
own radial profile (``symmetric_profile`` with ``calibrate_outer_decay_length``):

* **Storm intensity ``V_max``** — the whole field scales with it, but the outer
  decay length ``L`` is re-anchored to the gale radius as ``V_max`` moves, so a
  property in the outer field grows *slightly sub-linearly* with ``V_max`` rather
  than one-for-one. The passthrough to local wind is near one; the material
  amplification happens downstream, where the wind-damage curve (MKM-WD-001) is a
  steep sigmoid in gust speed, turning a few-percent wind error into a much larger
  loss error.

* **Track offset ``r``** (closest approach of the eye to the property) — this is
  the dominant *geometric* uncertainty the Bayesian particle filter produces. The
  profile is steepest on the eyewall ramp: local wind climbs from ``α_eye·V_max``
  at the centre to ``V_max`` at ``R_max`` (a factor ``1/α_eye`` over ``R_max``
  km), then decays gently once the gale radius is far out. So whether the eyewall
  band (``r ≈ R_max``) sweeps over a property, versus passing tens of km away,
  swings its peak wind far more than a plausible intensity error does.

This module is pure and data-free: it composes the calibrated wind-field
functions and default ``WindFieldParams`` over grids of candidate intensity and
track errors, reporting the peak-wind response and its local gradient. Nothing
here is wired into the pipeline; it is a diagnostic a validation report or the
MRC calls.
"""
from typing import Dict, Mapping, Sequence

from config.typhoon._field import WindFieldParams
from models.typhoon.wind_field.radial import (
    calibrate_outer_decay_length,
    symmetric_profile,
)

_DEFAULTS = WindFieldParams()


def local_peak_wind(
    offset_km: float,
    v_max_ms: float,
    r_max_km: float,
    r_outer_km: float,
    alpha_eye: float = _DEFAULTS.alpha_eye,
    outer_shape_p: float = _DEFAULTS.outer_shape_p,
    v_outer_ref_ms: float = _DEFAULTS.v_outer_ref_ms,
) -> float:
    """Symmetric peak wind (m/s) at radial ``offset_km`` from the eye.

    Calibrates the outer-decay length ``L`` from the gale-radius anchor exactly as
    the production path does, then evaluates the piecewise radial profile. This is
    the model's own two-step wind-field evaluation, composed for what-if use.
    """
    length = calibrate_outer_decay_length(
        v_max_ms, r_max_km, r_outer_km, v_outer_ref_ms, outer_shape_p)
    return symmetric_profile(
        offset_km, r_max_km, v_max_ms, alpha_eye, length, outer_shape_p)


def intensity_sensitivity(
    offset_km: float,
    base_v_max_ms: float,
    r_max_km: float,
    r_outer_km: float,
    factors: Sequence[float],
    alpha_eye: float = _DEFAULTS.alpha_eye,
    outer_shape_p: float = _DEFAULTS.outer_shape_p,
    v_outer_ref_ms: float = _DEFAULTS.v_outer_ref_ms,
) -> Dict:
    """How the local peak wind responds to a multiplicative ``V_max`` error.

    For each ``factor`` on ``V_max`` the outer length is re-calibrated (as in
    production) before the profile is read at ``offset_km``. Reports the resulting
    wind, its ratio to the base, and a local elasticity estimated by central
    difference over the factor grid — closed form is unavailable because ``L``
    itself depends on ``V_max``.

    Returns ``{"offset_km", "base_wind", "rows": [...]}`` with each row carrying
    ``factor``, ``v_max``, ``wind`` and ``wind_rel_to_base``.
    """
    base_wind = local_peak_wind(
        offset_km, base_v_max_ms, r_max_km, r_outer_km,
        alpha_eye, outer_shape_p, v_outer_ref_ms)
    rows = []
    for factor in factors:
        v_max = base_v_max_ms * factor
        wind = local_peak_wind(
            offset_km, v_max, r_max_km, r_outer_km,
            alpha_eye, outer_shape_p, v_outer_ref_ms)
        rows.append({
            "factor": factor,
            "v_max": v_max,
            "wind": wind,
            "wind_rel_to_base": (wind / base_wind) if base_wind > 0 else float("nan"),
        })
    return {"offset_km": offset_km, "base_wind": base_wind, "rows": rows}


def track_offset_sensitivity(
    base_offset_km: float,
    v_max_ms: float,
    r_max_km: float,
    r_outer_km: float,
    offsets_km: Sequence[float],
    alpha_eye: float = _DEFAULTS.alpha_eye,
    outer_shape_p: float = _DEFAULTS.outer_shape_p,
    v_outer_ref_ms: float = _DEFAULTS.v_outer_ref_ms,
) -> Dict:
    """How the local peak wind responds to the eye's closest-approach offset.

    Evaluates the profile at each candidate ``offset_km`` (fixed intensity/size)
    and reports the wind together with the local spatial gradient ``dV/dr``
    (m/s per km, central difference), so the steep eyewall ramp shows up against
    the gentle outer decay.

    Returns ``{"base_offset_km", "base_wind", "rows": [...]}`` with each row
    carrying ``offset_km``, ``wind``, ``wind_change`` and ``gradient_ms_per_km``.
    """
    length = calibrate_outer_decay_length(
        v_max_ms, r_max_km, r_outer_km, v_outer_ref_ms, outer_shape_p)

    def _wind(r: float) -> float:
        return symmetric_profile(r, r_max_km, v_max_ms, alpha_eye, length, outer_shape_p)

    base_wind = _wind(base_offset_km)
    rows = []
    step = 1.0  # km, for the gradient central difference
    for offset in offsets_km:
        wind = _wind(offset)
        lo = _wind(max(0.0, offset - step))
        hi = _wind(offset + step)
        span = (offset + step) - max(0.0, offset - step)
        gradient = (hi - lo) / span if span > 0 else 0.0
        rows.append({
            "offset_km": offset,
            "wind": wind,
            "wind_change": wind - base_wind,
            "gradient_ms_per_km": gradient,
        })
    return {"base_offset_km": base_offset_km, "base_wind": base_wind, "rows": rows}


def peak_wind_distribution(
    v_max_ms: float,
    r_max_km: float,
    r_outer_km: float,
    offset_percentiles: Mapping[str, float],
    alpha_eye: float = _DEFAULTS.alpha_eye,
    outer_shape_p: float = _DEFAULTS.outer_shape_p,
    v_outer_ref_ms: float = _DEFAULTS.v_outer_ref_ms,
) -> Dict:
    """Propagate an uncertain closest-approach offset to the peak-wind band.

    The particle filter yields a distribution over where the eye passes; because
    peak wind is monotone in offset (outside the eyewall), an offset given by
    percentiles maps directly onto a peak-wind band. Reports the wind at each
    percentile and its move against the median — the honest width of one
    property's peak-wind estimate from track uncertainty alone.

    Args:
        offset_percentiles: Percentile label → closest-approach offset in km, e.g.
                            ``{"p05": 10, "p50": 45, "p95": 90}``.

    Returns ``{"median_wind", "rows": [...]}`` with each row carrying
    ``percentile``, ``offset_km``, ``wind`` and ``wind_minus_median``.
    """
    length = calibrate_outer_decay_length(
        v_max_ms, r_max_km, r_outer_km, v_outer_ref_ms, outer_shape_p)

    def _wind(r: float) -> float:
        return symmetric_profile(r, r_max_km, v_max_ms, alpha_eye, length, outer_shape_p)

    median_offset = offset_percentiles.get("p50")
    median_wind = _wind(median_offset) if median_offset is not None else float("nan")
    rows = []
    for label, offset in offset_percentiles.items():
        wind = _wind(offset)
        rows.append({
            "percentile": label,
            "offset_km": offset,
            "wind": wind,
            "wind_minus_median": wind - median_wind,
        })
    return {"median_wind": median_wind, "rows": rows}
