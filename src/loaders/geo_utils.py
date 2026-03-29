# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Geographic utility functions for distance calculations and spatial queries."""

import math
from typing import Any, Callable, List, Optional, Tuple


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points using the Haversine formula.

    Args:
        lat1: Latitude of point 1 (degrees).
        lon1: Longitude of point 1 (degrees).
        lat2: Latitude of point 2 (degrees).
        lon2: Longitude of point 2 (degrees).

    Returns:
        Distance in kilometres.
    """
    R = 6371  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def find_entities_in_radius(
    entities: List[Any],
    get_coords_fn: Callable[[Any], Optional[Tuple[float, float]]],
    lat: float,
    lon: float,
    radius_km: float
) -> List[Any]:
    """Filter entities that fall within a radius of a centre point.

    Args:
        entities: Iterable of entity objects.
        get_coords_fn: Callable that takes an entity and returns
            ``(latitude, longitude)`` or ``None`` if unavailable.
        lat: Centre latitude (degrees).
        lon: Centre longitude (degrees).
        radius_km: Search radius in kilometres.

    Returns:
        List of entities within the radius.
    """
    results = []
    for entity in entities:
        coords = get_coords_fn(entity)
        if coords:
            entity_lat, entity_lon = coords
            if haversine(lat, lon, entity_lat, entity_lon) <= radius_km:
                results.append(entity)
    return results
