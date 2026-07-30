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

"""What-if sensitivity for the stress-test pipeline (MKM-ST-001).

The pipeline's flood decision runs through ``FloodPoly`` — a logistic surrogate
for the per-gauge GBM classifier — whose flood probability is

    P(flood) = σ(a·h + b·t + c·h·t + d·h² + e·t² + f)

on two gauge-independent log features: ``h = ln(w / s)`` (water level ``w``
against the severe threshold ``s``) and ``t = ln((hour+1) / T)`` (storm time).
The pipeline's single most material uncertain input is the **severe-threshold
calibration** ``s``: it is a per-gauge number, unvalidated on synthetic data, and
it enters only through ``h``, so a relative error in ``s`` (or, symmetrically, in
the stress water level ``w``) shifts ``h`` and moves every downstream flood label.

The response is a saturating logistic, so it has one sharp regime and two flat
ones — surfaced here in closed form:

* **Transition band** (``w ≈ s``, ``h ≈ 0``): the slope ``∂P/∂h`` is at its
  maximum. A one-percent error in the threshold or water level moves the flood
  probability by several percentage points — this is where the classifier, and
  therefore the whole stress catalogue, is most fragile.

* **Saturated tails** (``|h|`` large — water far below or far above threshold):
  ``σ'(z) → 0`` so the response collapses to near-zero. Well-separated events are
  robust to threshold error; the model's own card notes it over-predicts in the
  alert→severe transition and under-predicts at the tails.

This module is pure and data-free. It composes the calibrated ``FloodPoly``
coefficients (``config.models.flood_poly_coeffs``) over a grid of candidate
threshold/water-level errors and reports the flood-probability response and its
closed-form slope ``∂P/∂h = σ'(z)·(a + c·t + 2d·h)``. Nothing here is wired into
the pipeline; it is a diagnostic a validation report or the MRC calls.
"""
import math
from typing import Dict, Mapping, Sequence

from config.models import flood_poly_coeffs, flood_poly_exp_clamp, flood_poly_storm_hours


def _sigmoid(z: float) -> float:
    """Logistic sigmoid with the model's overflow clamp."""
    clamp = flood_poly_exp_clamp
    z = max(-clamp, min(clamp, z))
    return 1.0 / (1.0 + math.exp(-z))


def _log_time(hour: int) -> float:
    """Log normalised storm time ``t = ln((hour+1) / T)`` (T = storm hours)."""
    return math.log((hour + 1) / flood_poly_storm_hours)


def flood_probability(log_margin: float, log_time: float) -> float:
    """``FloodPoly`` probability at log-margin ``h`` and log-time ``t``.

    ``P = σ(a·h + b·t + c·h·t + d·h² + e·t² + f)`` with the calibrated
    coefficients. ``h = ln(w/s)`` is 0 at the severe threshold; ``t`` is 0 at the
    final storm hour.
    """
    k = flood_poly_coeffs
    z = (k.a * log_margin + k.b * log_time + k.c * log_margin * log_time
         + k.d * log_margin ** 2 + k.e * log_time ** 2 + k.f)
    return _sigmoid(z)


def flood_probability_slope(log_margin: float, log_time: float) -> float:
    """Closed-form ``∂P/∂h = σ'(z)·(a + c·t + 2d·h)`` — probability per unit ``h``.

    Since ``h = ln(w/s)``, a small fractional change ε in the water level (or −ε
    in the threshold) shifts ``h`` by ≈ ε, so ``ε·∂P/∂h`` is the probability move
    for an ε-fractional calibration error.
    """
    k = flood_poly_coeffs
    z = (k.a * log_margin + k.b * log_time + k.c * log_margin * log_time
         + k.d * log_margin ** 2 + k.e * log_time ** 2 + k.f)
    s = _sigmoid(z)
    return s * (1.0 - s) * (k.a + k.c * log_time + 2.0 * k.d * log_margin)


def threshold_sensitivity(
    water_level: float,
    severe_level: float,
    hour: int,
    factors: Sequence[float],
) -> Dict:
    """Quantify how P(flood) responds to a multiplicative severe-threshold error.

    For each ``factor`` on the severe threshold ``s`` (a factor >1 = threshold
    calibrated too high, so the event looks less severe), recomputes
    ``h = ln(w / (s·factor))`` and reports the flood probability, its change
    against the base, and the closed-form slope ``∂P/∂h``.

    Args:
        water_level:  Peak/stress water level ``w`` (m AOD).
        severe_level: Base severe threshold ``s`` (m AOD).
        hour:         Storm hour index (0..T-1); the time feature is held fixed.
        factors:      Multiplicative errors on the threshold to probe.

    Returns:
        ``{"base_log_margin", "base_prob", "log_time", "rows": [...]}`` with each
        row carrying ``factor``, ``severe_level``, ``log_margin``, ``prob``,
        ``prob_change`` and ``slope_dP_dh``.
    """
    t = _log_time(hour)
    base_h = math.log(water_level / severe_level)
    base_p = flood_probability(base_h, t)
    rows = []
    for factor in factors:
        s = severe_level * factor
        h = math.log(water_level / s)
        p = flood_probability(h, t)
        rows.append({
            "factor": factor,
            "severe_level": s,
            "log_margin": h,
            "prob": p,
            "prob_change": p - base_p,
            "slope_dP_dh": flood_probability_slope(h, t),
        })
    return {"base_log_margin": base_h, "base_prob": base_p, "log_time": t, "rows": rows}


def flood_probability_distribution(
    water_level: float,
    severe_level: float,
    hour: int,
    threshold_percentiles: Mapping[str, float],
) -> Dict:
    """Propagate an uncertain severe threshold to the induced P(flood) band.

    ``P`` is monotone decreasing in the threshold, so an uncertain ``s`` given by
    percentile multipliers maps exactly (no Monte-Carlo noise) onto flood-
    probability percentiles. Reports the absolute probability move against the
    median at each percentile — the honest width of the flood label's uncertainty
    for one gauge's calibration error.

    Args:
        water_level:           Stress water level ``w`` (m AOD).
        severe_level:          Base severe threshold ``s`` (m AOD).
        hour:                  Storm hour index; time feature held fixed.
        threshold_percentiles: Percentile label → multiplicative threshold factor,
                               e.g. ``{"p05": 0.95, "p50": 1.0, "p95": 1.05}``.

    Returns:
        ``{"median_prob", "log_time", "rows": [...]}`` with each row carrying
        ``percentile``, ``threshold_factor``, ``severe_level``, ``log_margin``,
        ``prob`` and ``prob_minus_median``.
    """
    t = _log_time(hour)
    median_factor = threshold_percentiles.get("p50", 1.0)
    median_p = flood_probability(math.log(water_level / (severe_level * median_factor)), t)
    rows = []
    for label, factor in threshold_percentiles.items():
        s = severe_level * factor
        h = math.log(water_level / s)
        p = flood_probability(h, t)
        rows.append({
            "percentile": label,
            "threshold_factor": factor,
            "severe_level": s,
            "log_margin": h,
            "prob": p,
            "prob_minus_median": p - median_p,
        })
    return {"median_prob": median_p, "log_time": t, "rows": rows}
