"""
EA Flood Zone terrain grid — spread lookup for interactive zone repricing.

Computes a dense (zone x distance x elevation) grid of property spreads
using the analytical PRS pricer. The grid is shipped with propertyhc.json
and interpolated client-side when the user changes the EA zone dropdown.
"""

import math
from typing import Dict, List

from config.models import (
    EA_FLOOD_ZONE_RATES,
    ELEV_SCALE_M,
    GRID_TENOR,
    GRID_RECOVERY,
    GRID_RISK_FREE_RATE,
)
from models.floodrisk.velocity import compute_retention
from models.hazard.prs_analytical import compute_prs_spread

# Grid resolution
GRID_DISTANCES_M = list(range(0, 5001, 250))     # 0..5000 in 250m steps (21 pts)
GRID_ELEVATIONS_M = [round(0.5 * i, 1) for i in range(11)]  # 0..5 in 0.5m steps (11 pts)


def compute_terrain_grid() -> Dict:
    """
    Build the terrain spread grid for all (zone, distance, elevation) triples.

    Returns:
        Dict with keys: distances, elevations, zones, params.
        zones[name].grid is a 2D list: grid[dist_idx][elev_idx] = spread_bps.
    """
    zones = {}
    for zone_name, zone_rate in EA_FLOOD_ZONE_RATES.items():
        grid: List[List[float]] = []
        for d in GRID_DISTANCES_M:
            retention = compute_retention(d)
            row: List[float] = []
            for h in GRID_ELEVATIONS_M:
                elev_factor = math.exp(-h / ELEV_SCALE_M)
                prop_rate = zone_rate * retention * elev_factor
                spread = compute_prs_spread(
                    prop_rate, tenor=GRID_TENOR,
                    recovery=GRID_RECOVERY, risk_free_rate=GRID_RISK_FREE_RATE,
                )
                row.append(round(spread, 2))
            grid.append(row)
        zones[zone_name] = {'rate': zone_rate, 'grid': grid}

    return {
        'distances': GRID_DISTANCES_M,
        'elevations': GRID_ELEVATIONS_M,
        'zones': zones,
        'params': {
            'elev_scale_m': ELEV_SCALE_M,
            'retention_length_m': 3000.0,
            'tenor': GRID_TENOR,
            'recovery': GRID_RECOVERY,
            'risk_free_rate': GRID_RISK_FREE_RATE,
        },
    }


def interpolate_terrain_spread(
    grid_data: Dict, zone: str, distance_m: float, elevation_m: float,
) -> float:
    """
    Bilinear interpolation of property spread from the terrain grid.

    Args:
        grid_data: Output of compute_terrain_grid().
        zone: EA flood zone name (e.g. 'Zone 3a').
        distance_m: Distance from gauge in metres.
        elevation_m: Elevation above gauge in metres.

    Returns:
        Interpolated property spread in basis points.
    """
    distances = grid_data['distances']
    elevations = grid_data['elevations']
    grid = grid_data['zones'][zone]['grid']

    # Clamp to grid bounds
    d = max(distances[0], min(distance_m, distances[-1]))
    h = max(elevations[0], min(elevation_m, elevations[-1]))

    # Find bracketing distance indices
    di = 0
    for i in range(len(distances) - 1):
        if distances[i + 1] >= d:
            di = i
            break
    else:
        di = len(distances) - 2

    # Find bracketing elevation indices
    ei = 0
    for i in range(len(elevations) - 1):
        if elevations[i + 1] >= h:
            ei = i
            break
    else:
        ei = len(elevations) - 2

    # Fractional positions within the cell
    d_span = distances[di + 1] - distances[di]
    e_span = elevations[ei + 1] - elevations[ei]
    td = (d - distances[di]) / d_span if d_span > 0 else 0.0
    te = (h - elevations[ei]) / e_span if e_span > 0 else 0.0

    # Bilinear interpolation
    v00 = grid[di][ei]
    v01 = grid[di][ei + 1]
    v10 = grid[di + 1][ei]
    v11 = grid[di + 1][ei + 1]

    return (
        v00 * (1 - td) * (1 - te)
        + v10 * td * (1 - te)
        + v01 * (1 - td) * te
        + v11 * td * te
    )
