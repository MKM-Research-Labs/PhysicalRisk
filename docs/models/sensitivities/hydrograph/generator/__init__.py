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

"""Hydrograph superposition v2.2 sensitivity analysis.

Runs synthetic scenarios for a single property at varying distance/elevation
from a flooding gauge.  Axes of variation:

  - Gauge peak WSE (low → extreme)
  - Distance from gauge (100 m → 5 km)
  - Elevation above gauge (0.5 m → 5 m)
  - Pulse duration (short → long)
  - Sequence type: isolated (1 pulse) vs doublet (2 pulses)

Outputs LaTeX tables consumed by the hydrograph sensitivity document.
"""

import math
from typing import List

import numpy as np

from docs.models.sensitivities import latex_table, write_tables


# ── synthetic property / gauge config ────────────────────────────────────
BASE_LEVEL = 3.0        # gauge base water level (m AOD)
GAUGE_ELEV = 5.0        # gauge ground elevation (m AOD)
FLOOR_LEVEL = 0.3       # property floor step (m)
ROUGHNESS = 0.04        # Manning's n


def _run_scenario(peak_m, distance_m, elev_above_gauge, duration_hours,
                  sequence_type, pulse_peaks_override=None):
    """Run a single compound hydrograph scenario and return metrics."""
    from models.floodrisk.hydrograph import build_compound_property_hydrograph
    from models.floodrisk.velocity import compute_retention, compute_slope, compute_travel_time

    prop_elev = GAUGE_ELEV + elev_above_gauge
    slope = compute_slope(GAUGE_ELEV, prop_elev, distance_m)
    retention = compute_retention(distance_m)

    # Estimate travel time from peak
    water_above = max(0.0, peak_m - GAUGE_ELEV)
    water_at = water_above * retention
    threshold = elev_above_gauge + FLOOR_LEVEL
    est_depth = max(0.01, water_at - threshold)
    tt = compute_travel_time(distance_m, est_depth, slope)
    if tt == float('inf'):
        tt = 0.0

    if pulse_peaks_override is not None:
        pulses = pulse_peaks_override
    elif sequence_type == 'doublet':
        # Two pulses: first at 80% of peak, second at full peak
        gap = max(12.0, duration_hours * 0.5)
        pulses = [
            {"storm_index": 0, "peak_m": peak_m * 0.8,
             "start_hour": 10.0, "duration_hours": duration_hours,
             "precip_mm": 60.0},
            {"storm_index": 1, "peak_m": peak_m,
             "start_hour": 10.0 + duration_hours + gap,
             "duration_hours": duration_hours, "precip_mm": 80.0},
        ]
    else:
        pulses = [
            {"storm_index": 0, "peak_m": peak_m,
             "start_hour": 10.0, "duration_hours": duration_hours,
             "precip_mm": 70.0},
        ]

    readings = build_compound_property_hydrograph(
        pulse_peaks=pulses,
        sequence_type=sequence_type,
        base_level=BASE_LEVEL,
        gauge_elevation=GAUGE_ELEV,
        prop_elevation=prop_elev,
        floor_level=FLOOR_LEVEL,
        travel_time_hrs=tt,
        retention=retention,
    )

    max_depth = max(r['depth_m'] for r in readings)
    flooded_hrs = sum(1 for r in readings if r['flooded'])
    arrival = next((r['hour'] for r in readings if r['flooded']), None)
    peak_hr = max(readings, key=lambda r: r['depth_m'])['hour'] if max_depth > 0 else None

    from models.floodrisk.depth_damage import scalar_depth_damage
    damage = scalar_depth_damage(max_depth)

    return {
        'max_depth': max_depth,
        'flooded_hrs': flooded_hrs,
        'arrival_hr': arrival,
        'peak_hr': peak_hr,
        'damage': damage,
        'travel_time': tt,
        'retention': retention,
    }


def generate():
    """Generate hydrograph sensitivity tables."""

    tables = []

    # ── Table 1: Peak WSE sensitivity (isolated) ──────────────────────
    peaks = [6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0]
    distance = 636.0
    elev_above = 1.42
    duration = 36.0

    headers = ['Peak WSE (m)', 'Depth (m)', 'Duration (hrs)',
               'Arrival (hr)', 'Damage (\\%)']
    rows = []
    for p in peaks:
        r = _run_scenario(p, distance, elev_above, duration, 'isolated')
        rows.append([p, r['max_depth'], r['flooded_hrs'],
                     r['arrival_hr'] if r['arrival_hr'] is not None else '---',
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        'Isolated storm: peak WSE sensitivity '
        f'($d={distance}$m, $\\Delta z={elev_above}$m, $D={int(duration)}$h).',
        'sens_hydro_peak_iso', headers, rows,
    ))

    # ── Table 2: Peak WSE sensitivity (doublet) ──────────────────────
    rows = []
    for p in peaks:
        r = _run_scenario(p, distance, elev_above, duration, 'doublet')
        rows.append([p, r['max_depth'], r['flooded_hrs'],
                     r['arrival_hr'] if r['arrival_hr'] is not None else '---',
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        'Doublet storm: peak WSE sensitivity '
        f'($d={distance}$m, $\\Delta z={elev_above}$m, $D={int(duration)}$h per pulse).',
        'sens_hydro_peak_dbl', headers, rows,
    ))

    # ── Table 3: Distance sensitivity (isolated) ─────────────────────
    distances = [100, 250, 500, 1000, 2000, 3000, 5000]
    peak = 10.0

    headers = ['Distance (m)', 'Retention', 'Travel (hrs)',
               'Depth (m)', 'Duration (hrs)', 'Damage (\\%)']
    rows = []
    for d in distances:
        r = _run_scenario(peak, d, elev_above, duration, 'isolated')
        rows.append([d, r['retention'], round(r['travel_time'], 2),
                     r['max_depth'], r['flooded_hrs'],
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        f'Isolated storm: distance sensitivity (peak$={peak}$m, '
        f'$\\Delta z={elev_above}$m).',
        'sens_hydro_dist_iso', headers, rows,
    ))

    # ── Table 4: Distance sensitivity (doublet) ──────────────────────
    rows = []
    for d in distances:
        r = _run_scenario(peak, d, elev_above, duration, 'doublet')
        rows.append([d, r['retention'], round(r['travel_time'], 2),
                     r['max_depth'], r['flooded_hrs'],
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        f'Doublet storm: distance sensitivity (peak$={peak}$m, '
        f'$\\Delta z={elev_above}$m).',
        'sens_hydro_dist_dbl', headers, rows,
    ))

    # ── Table 5: Elevation sensitivity (isolated) ────────────────────
    elevations = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]

    headers = ['$\\Delta z$ (m)', 'Threshold (m)',
               'Depth (m)', 'Duration (hrs)', 'Damage (\\%)']
    rows = []
    for ez in elevations:
        r = _run_scenario(peak, distance, ez, duration, 'isolated')
        rows.append([ez, round(ez + FLOOR_LEVEL, 2),
                     r['max_depth'], r['flooded_hrs'],
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        f'Isolated storm: elevation sensitivity (peak$={peak}$m, '
        f'$d={distance}$m).',
        'sens_hydro_elev_iso', headers, rows,
    ))

    # ── Table 6: Elevation sensitivity (doublet) ─────────────────────
    rows = []
    for ez in elevations:
        r = _run_scenario(peak, distance, ez, duration, 'doublet')
        rows.append([ez, round(ez + FLOOR_LEVEL, 2),
                     r['max_depth'], r['flooded_hrs'],
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        f'Doublet storm: elevation sensitivity (peak$={peak}$m, '
        f'$d={distance}$m).',
        'sens_hydro_elev_dbl', headers, rows,
    ))

    # ── Table 7: Duration sensitivity (isolated) ─────────────────────
    durations = [12, 24, 36, 48, 72, 96, 120]

    headers = ['Duration (hrs)', 'Depth (m)', 'Flooded (hrs)',
               'Arrival (hr)', 'Peak (hr)', 'Damage (\\%)']
    rows = []
    for dur in durations:
        r = _run_scenario(peak, distance, elev_above, dur, 'isolated')
        rows.append([dur, r['max_depth'], r['flooded_hrs'],
                     r['arrival_hr'] if r['arrival_hr'] is not None else '---',
                     r['peak_hr'] if r['peak_hr'] is not None else '---',
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        f'Isolated storm: pulse duration sensitivity (peak$={peak}$m, '
        f'$d={distance}$m, $\\Delta z={elev_above}$m).',
        'sens_hydro_dur_iso', headers, rows,
    ))

    # ── Table 8: Duration sensitivity (doublet) ──────────────────────
    rows = []
    for dur in durations:
        r = _run_scenario(peak, distance, elev_above, dur, 'doublet')
        rows.append([dur, r['max_depth'], r['flooded_hrs'],
                     r['arrival_hr'] if r['arrival_hr'] is not None else '---',
                     r['peak_hr'] if r['peak_hr'] is not None else '---',
                     round(r['damage'] * 100, 1)])
    tables.append(latex_table(
        f'Doublet storm: pulse duration sensitivity (peak$={peak}$m, '
        f'$d={distance}$m, $\\Delta z={elev_above}$m).',
        'sens_hydro_dur_dbl', headers, rows,
    ))

    # ── Table 9: Isolated vs doublet comparison ──────────────────────
    # Fixed property, varying peak — side by side
    headers = ['Peak (m)', 'Iso depth (m)', 'Dbl depth (m)',
               '$\\Delta$ depth (m)', 'Iso dur (hrs)', 'Dbl dur (hrs)',
               '$\\Delta$ dur (hrs)']
    rows = []
    for p in peaks:
        ri = _run_scenario(p, distance, elev_above, duration, 'isolated')
        rd = _run_scenario(p, distance, elev_above, duration, 'doublet')
        dd = round(rd['max_depth'] - ri['max_depth'], 4)
        dh = rd['flooded_hrs'] - ri['flooded_hrs']
        rows.append([p, ri['max_depth'], rd['max_depth'], dd,
                     ri['flooded_hrs'], rd['flooded_hrs'], dh])
    tables.append(latex_table(
        f'Isolated vs doublet comparison '
        f'($d={distance}$m, $\\Delta z={elev_above}$m, $D={int(duration)}$h).',
        'sens_hydro_iso_vs_dbl', headers, rows,
        col_fmt='r' * 7,
    ))

    write_tables('hydrograph', '\n\n'.join(tables))
