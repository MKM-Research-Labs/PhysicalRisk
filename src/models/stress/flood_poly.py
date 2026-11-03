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
"""
Polynomial Flood Probability Model (FloodPoly) v2.0 -- MKM-FPO-001
==================================================================

A closed-form approximation of the per-gauge GBM flood classifiers (MKM-FC-001),
so that stress scenarios can price P(flood) without a trained model per gauge.

Features
--------
  h = ln(w / s)           -- water level relative to the severe threshold
  t = ln((hour + 1) / T)  -- storm time, T = 168 hours

Model
-----
  P(flood) = 1                                   if w >= s
           = sigma( sum_k c_k h^i t^j )           otherwise

over the cubic terms (i, j) of ``config.models.flood_poly_terms``. At or above the
severe level a flood has happened -- that is the classifiers' label -- so P = 1.
Below it the kernel is fitted (``python -m tools.flood_poly_fit``) to every gauge's
GBM on the real storm states the classifiers are trained on, pooled, and constrained
to rise with the level from ``flood_poly_level_floor`` (20% of severe) up to it;
below the floor the model holds its value there, effectively zero.

The kernel is only fitted where storms go. No storm reaches 40% of severe before hour
4.7, or severe before hour 37.4 (``config.models.flood_poly_envelope``); earlier than
that the GBMs have never been shown a state, and the polynomial is extrapolating. So
the model holds the hour at that envelope: a level reached sooner than any storm
reached it is priced as the earliest storm that did. The fit also constrains P to rise
along the envelope, so rising water never lowers P, held or not.

The GBMs also see the rate of rise; a function of (h, t) can at best give their
average over the states sharing a level and an hour. v1.0 (a quadratic kernel
fitted to one gauge) fell as the level rose early in a storm and fell back to 0.29
at the severe level late in it; see MKM-FPO-001_wolfram_benchmark.

``p_flood_simple`` is not a probability: it is the ratio w/s capped at 1, the
proximity measure portfolio stress uses where only the peak level is known.
"""

import math
from typing import List, Tuple

from config.models import (
    flood_poly_coeffs,
    flood_poly_envelope,
    flood_poly_exp_clamp,
    flood_poly_fit,
    flood_poly_level_floor,
    flood_poly_storm_hours,
    flood_poly_terms,
)


def _log_features(water_level: float, hour: int, severe_level: float) -> Tuple[float, float]:
    """(h, t) = (ln(w/s), ln((hour+1)/T)), the level held at ``flood_poly_level_floor``
    of severe below it."""
    h = math.log(max(water_level / severe_level, flood_poly_level_floor))
    t = math.log((hour + 1) / flood_poly_storm_hours)
    return h, t


_H_FLOOR = math.log(flood_poly_level_floor)
_ENV_H = [math.log(r) for r, _ in flood_poly_envelope]
_ENV_T = [math.log((hour + 1) / flood_poly_storm_hours) for _, hour in flood_poly_envelope]


def _envelope_segment(h: float):
    """The envelope segment holding log level h, or None below its first knot."""
    if h <= _ENV_H[0]:
        return None
    for a in range(len(_ENV_H) - 1):
        if h <= _ENV_H[a + 1]:
            return a
    return len(_ENV_H) - 2


def envelope_t(h: float) -> float:
    """The earliest supported log time at log level h; -inf where every hour is."""
    a = _envelope_segment(h)
    if a is None:
        return -math.inf
    f = min(1.0, (h - _ENV_H[a]) / (_ENV_H[a + 1] - _ENV_H[a]))
    return _ENV_T[a] + f * (_ENV_T[a + 1] - _ENV_T[a])


def envelope_slope(h: float) -> float:
    """d(envelope_t)/dh at log level h."""
    a = _envelope_segment(h)
    if a is None or h > _ENV_H[-1]:
        return 0.0
    return (_ENV_T[a + 1] - _ENV_T[a]) / (_ENV_H[a + 1] - _ENV_H[a])


def _sigmoid(z: float) -> float:
    """Logistic sigmoid with overflow protection."""
    z = max(-flood_poly_exp_clamp, min(flood_poly_exp_clamp, z))
    return 1.0 / (1.0 + math.exp(-z))


def kernel(h: float, t: float) -> float:
    """The log-odds below severe: sum of c_k h^i t^j."""
    return sum(c * h ** i * t ** j for (i, j), c in zip(flood_poly_terms, flood_poly_coeffs))


def kernel_dh(h: float, t: float) -> float:
    """d(kernel)/dh, term by term."""
    return sum(c * i * h ** (i - 1) * t ** j for (i, j), c in zip(flood_poly_terms, flood_poly_coeffs) if i)


def kernel_dt(h: float, t: float) -> float:
    """d(kernel)/dt, term by term."""
    return sum(c * j * h ** i * t ** (j - 1) for (i, j), c in zip(flood_poly_terms, flood_poly_coeffs) if j)


def p_from_features(h: float, t: float) -> float:
    """P(flood) at log level h and log time t: 1 at or above severe (h >= 0); below
    it h held at the level floor and t at the support envelope."""
    if h >= 0:
        return 1.0
    h = max(h, _H_FLOOR)
    return _sigmoid(kernel(h, max(t, envelope_t(h))))


def slope_from_features(h: float, t: float) -> float:
    """dP/dh at a fixed hour: zero at or above severe and below the floor; between,
    sigma'(z) dz/dh, plus dz/dt along the envelope where the hour is held there."""
    if h >= 0 or h < _H_FLOOR:
        return 0.0
    held = envelope_t(h)
    if t < held:
        dz = kernel_dh(h, held) + kernel_dt(h, held) * envelope_slope(h)
        t = held
    else:
        dz = kernel_dh(h, t)
    z = kernel(h, t)
    return _sigmoid(z) * _sigmoid(-z) * dz          # sigma'(z), without 1 - p cancelling near P = 1


def p_flood_poly(water_level: float, hour: int, severe_level: float) -> float:
    """P(flood) from the water level, the storm hour (0..167) and the severe threshold."""
    if severe_level <= 0:
        return 0.0
    return p_from_features(*_log_features(water_level, hour, severe_level))


def p_flood_simple(water_level: float, severe_level: float) -> float:
    """The ratio w/s capped at 1 -- a proximity measure, not a probability.

    Portfolio stress uses it where only a gauge's peak level is known.
    """
    if severe_level <= 0:
        return 0.0
    return min(1.0, water_level / severe_level)


def p_flood_series(water_levels: List[float], severe_level: float) -> List[float]:
    """``p_flood_poly`` for an hourly hydrograph (hour = position)."""
    return [p_flood_poly(wl, h, severe_level) for h, wl in enumerate(water_levels)]


def model_card() -> dict:
    """Model metadata for audit and documentation."""
    return {
        "model_id": flood_poly_fit["model_id"],
        "version": flood_poly_fit["version"],
        "type": "logistic_sigmoid_polynomial",
        "features": ["ln(w/s)", "ln((t+1)/T)"],
        "num_parameters": len(flood_poly_coeffs),
        "coefficients": {f"h^{i} t^{j}": c for (i, j), c in zip(flood_poly_terms, flood_poly_coeffs)},
        "fitted_to": flood_poly_fit["fitted_to"],
        "fit_quality": flood_poly_fit["fit_quality"],
        "storm_hours": flood_poly_storm_hours,
        "support_envelope": [list(knot) for knot in flood_poly_envelope],
    }


def client_params() -> dict:
    """What a browser needs to evaluate the model itself, served rather than copied.

    The port-stress screen draws P(flood) hour by hour client-side. It used to carry
    its own copy of v1.0's coefficients, which a refit would have left behind; it now
    fetches these, so the screen and the server are one model.
    """
    return {
        "model_id": flood_poly_fit["model_id"],
        "version": flood_poly_fit["version"],
        "terms": [list(term) for term in flood_poly_terms],
        "coeffs": list(flood_poly_coeffs),
        "level_floor": flood_poly_level_floor,
        "envelope": [list(knot) for knot in flood_poly_envelope],
        "storm_hours": flood_poly_storm_hours,
        "exp_clamp": flood_poly_exp_clamp,
    }
