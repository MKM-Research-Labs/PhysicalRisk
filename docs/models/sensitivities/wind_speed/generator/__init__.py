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

"""Event Wind Lookup (MKM-WS-001) sensitivity analysis.

Exercises the wind-at-point query along its three axes: radial distance from
the storm centre, azimuth relative to the direction of motion (asymmetry), and
the surface class of the evaluation point. A fourth table covers the temporal
axis --- linear state interpolation between stored hours.
"""

from docs.models.sensitivities import latex_table, write_tables


# Reference storm used throughout: a mature category-3 system with a
# 30 km eyewall and a 250 km gale radius, tracking north-west at 18 km/h.
_REF = {
    'v_max_ms': 50.0,
    'r_max_km': 30.0,
    'r_outer_km': 250.0,
    'translation_speed_kmh': 18.0,
    'heading_deg': 315.0,
}


def _state(**overrides):
    """Build a TyphoonState from the reference storm with overrides applied."""
    from config.typhoon import RegimeClass
    from models.typhoon.data_structures import TyphoonState

    fields = dict(_REF)
    fields.update(overrides)
    return TyphoonState(
        longitude=fields.pop('longitude', 106.0),
        latitude=fields.pop('latitude', 20.0),
        translation_speed_kmh=fields['translation_speed_kmh'],
        heading_deg=fields['heading_deg'],
        v_max_ms=fields['v_max_ms'],
        r_max_km=fields['r_max_km'],
        r_outer_km=fields['r_outer_km'],
        regime=fields.pop('regime', RegimeClass.NW_RECURVER),
        land_flag=fields.pop('land_flag', False),
        time_hours=fields.pop('time_hours', 0.0),
    )


def generate():
    """Generate Event Wind Lookup sensitivity tables."""
    from config.typhoon import WindFieldParams
    from models.typhoon.wind_field import (
        calibrate_outer_decay_length,
        symmetric_profile,
    )
    from models.typhoon.wind_field.asymmetry import asymmetry_factor, compute_epsilon
    from models.typhoon.wind_field.point import evaluate_point
    from models.windspeed.interpolation import interpolate_state_at_hour

    params = WindFieldParams()

    # -- Table 1: symmetric radial profile ---------------------------------
    # V_sym(r) for three storm intensities. The inner-core ramp
    # (alpha_eye -> 1) and the exponential outer decay are both visible.
    radii = [0, 10, 20, 30, 50, 75, 100, 150, 200, 250, 300, 400]
    v_maxes = [35.0, 50.0, 65.0]
    headers = ['$r$ (km)'] + [f'$V_{{sym}}$ at $V_{{max}}={v:.0f}$' for v in v_maxes]
    rows = []
    for r in radii:
        cells = []
        for v_max in v_maxes:
            decay = calibrate_outer_decay_length(
                v_max_ms=v_max,
                r_max_km=_REF['r_max_km'],
                r_outer_km=_REF['r_outer_km'],
                v_outer_ref_ms=params.v_outer_ref_ms,
                outer_shape_p=params.outer_shape_p,
            )
            cells.append(round(symmetric_profile(
                r_km=float(r),
                r_max_km=_REF['r_max_km'],
                v_max_ms=v_max,
                alpha_eye=params.alpha_eye,
                outer_decay_length_km=decay,
                outer_shape_p=params.outer_shape_p,
            ), 2))
        rows.append([r] + cells)

    t1 = latex_table(
        'Symmetric radial profile $V_{sym}(r)$ in m/s by distance from the storm '
        f"centre ($R_{{max}}={_REF['r_max_km']:.0f}$~km, "
        f"$R_{{outer}}={_REF['r_outer_km']:.0f}$~km).",
        'sens_ws_radial', headers, rows,
    )

    # -- Table 2: outer-decay length calibration ---------------------------
    # L solves V_sym(R_outer) = v_outer_ref. Weak storms (V_max <= 17.5 m/s)
    # fall back to the geometric L = R_outer - R_max.
    rows = []
    for v_max in [15.0, 17.5, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]:
        decay = calibrate_outer_decay_length(
            v_max_ms=v_max,
            r_max_km=_REF['r_max_km'],
            r_outer_km=_REF['r_outer_km'],
            v_outer_ref_ms=params.v_outer_ref_ms,
            outer_shape_p=params.outer_shape_p,
        )
        fallback = 'yes' if v_max <= params.v_outer_ref_ms else 'no'
        rows.append([v_max, round(decay, 2), fallback])

    t2 = latex_table(
        'Outer-decay length $L$ (km) by peak wind, anchored at '
        f'$V_{{outer,ref}}={params.v_outer_ref_ms}$~m/s with $p={params.outer_shape_p}$. '
        'The geometric fallback applies when the eyewall wind is at or below the anchor.',
        'sens_ws_decay',
        ['$V_{max}$ (m/s)', '$L$ (km)', 'Fallback'], rows,
    )

    # -- Table 3: motion-linked asymmetry ----------------------------------
    # epsilon grows with translation speed and shrinks with V_max; the
    # multiplier peaks at theta = phi (right of motion under the NH convention).
    speeds = [0.0, 5.0, 10.0, 18.0, 25.0, 35.0, 50.0]
    azimuths = [0, 45, 90, 135, 180, 270]
    phi = (_REF['heading_deg'] + params.asymmetry_phase_offset_deg) % 360.0
    headers = ['$u$ (km/h)', r'$\epsilon$'] + [rf'$\theta={a}^\circ$' for a in azimuths]
    rows = []
    for u in speeds:
        eps = compute_epsilon(
            translation_speed_kmh=u,
            v_max_ms=_REF['v_max_ms'],
            eps_max=params.eps_max,
            c_eps=params.c_eps,
            eta_ms=params.eta_ms,
        )
        factors = [round(asymmetry_factor(float(a), phi, eps), 4) for a in azimuths]
        rows.append([u, round(eps, 4)] + factors)

    t3 = latex_table(
        'Asymmetry multiplier $1 + \\epsilon\\cos(\\theta - \\phi)$ by translation '
        f"speed and azimuth ($V_{{max}}={_REF['v_max_ms']:.0f}$~m/s, heading "
        f"${_REF['heading_deg']:.0f}^\\circ$, $\\phi={phi:.0f}^\\circ$, "
        f'$\\epsilon_{{max}}={params.eps_max}$).',
        'sens_ws_asymmetry', headers, rows,
    )

    # -- Table 4: end-to-end point evaluation, land vs sea ------------------
    # evaluate_point composes geometry + profile + asymmetry + surface. The
    # query point is displaced due north of the centre by the given distance.
    state = _state()
    deg_per_km = 1.0 / 111.195
    rows = []
    for dist_km in [0, 25, 50, 100, 150, 250]:
        lat = state.latitude + dist_km * deg_per_km
        sea = evaluate_point(state, state.longitude, lat, params, lambda lon, la: False)
        land = evaluate_point(state, state.longitude, lat, params, lambda lon, la: True)
        rows.append([dist_km, round(sea, 2), round(land, 2),
                     round(land - sea, 2)])

    t4 = latex_table(
        'End-to-end point wind (m/s) due north of the storm centre, over sea vs '
        f'over land ($\\rho_{{sea}}={params.rho_surf_sea}$, '
        f'$\\rho_{{land}}={params.rho_surf_land}$).',
        'sens_ws_surface',
        ['Distance (km)', 'Sea (m/s)', 'Land (m/s)', 'Difference'], rows,
    )

    # -- Table 5: temporal interpolation and clamping ----------------------
    # Two stored states 6 h apart; queries outside the range clamp rather
    # than extrapolate.
    states = [
        _state(v_max_ms=40.0, r_max_km=40.0, time_hours=12.0),
        _state(v_max_ms=60.0, r_max_km=25.0, time_hours=18.0),
    ]
    rows = []
    for hour in [6.0, 12.0, 13.5, 15.0, 16.5, 18.0, 24.0]:
        interp = interpolate_state_at_hour(states, hour)
        clamped = 'yes' if hour < 12.0 or hour > 18.0 else 'no'
        rows.append([hour, round(interp.v_max_ms, 2), round(interp.r_max_km, 2), clamped])

    t5 = latex_table(
        'Linear state interpolation between stored hours 12 and 18. Queries '
        'outside the trajectory range clamp to the first / last stored state.',
        'sens_ws_interpolation',
        ['Hour', '$V_{max}$ (m/s)', '$R_{max}$ (km)', 'Clamped'], rows,
    )

    write_tables('wind_speed', '\n\n'.join([t1, t2, t3, t4, t5]))
