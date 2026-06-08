# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Model A orchestrators — per-asset and portfolio occurrence simulation.

For each of ``n_sim`` draws, ``N ~ Poisson(lambda_i * horizon_years)`` is drawn;
an earthquake instantiates when ``N >= 1``, with a magnitude, a fault-trace
rupture centroid, a Wells-Coppersmith rupture length, and the Joyner-Boore
distance R_JB. All randomness flows through a single caller-owned generator.
"""

from typing import List, Optional

import numpy as np

from config.seismic import SeismicModelConfig
from models.seismic.datastructures import (
    AssetSeismicFeatures,
    EarthquakeEvent,
    OccurrenceResult,
)
from models.seismic.occurrence._fault import (
    Coord,
    cumulative_arclengths,
    joyner_boore_distance_km,
    point_at,
    rupture_segment,
)
from models.seismic.occurrence._rates import (
    asset_fault_distance_km,
    asset_lambda,
    resolve_site_class,
    resolve_zone,
    sample_magnitude,
)


def simulate_asset_occurrence(
    features: AssetSeismicFeatures,
    config: SeismicModelConfig,
    fault: Optional[List[Coord]],
    rng: np.random.Generator,
    n_sim: Optional[int] = None,
) -> OccurrenceResult:
    """Run Model A occurrence for one asset.

    Args:
        features: the asset's CDM-derived feature bundle.
        config: the hydrated seismic model config.
        fault: the catchment fault trace as ``(lat, lon)`` vertices, or None
            (no spatial draw; events still occur but R_JB is left at 0.0).
        rng: caller-owned random generator (threaded for reproducibility).
        n_sim: optional draw-count override; defaults to ``config.run.n_sim``.

    Returns:
        An :class:`OccurrenceResult` carrying the instantiated events.
    """
    occ = config.occurrence
    zone = resolve_zone(features, occ)
    zone_block = occ.zones[zone]
    site_class = resolve_site_class(features.soil_vs30_mps, config.ground_motion)
    fault_distance = asset_fault_distance_km(features, fault)

    lambda_annual = asset_lambda(features, fault_distance, site_class, config)
    lambda_effective = lambda_annual * config.run.horizon_years
    n = n_sim if n_sim is not None else config.run.n_sim

    cum = cumulative_arclengths(fault) if fault else None
    total_len = cum[-1] if cum else 0.0
    wc = occ.wells_coppersmith

    counts = rng.poisson(lambda_effective, size=n)
    events: List[EarthquakeEvent] = []
    for draw_index in range(n):
        if counts[draw_index] < 1:
            continue
        magnitude = sample_magnitude(
            zone_block["b"], zone_block["m_min"], zone_block["m_max"], rng)
        length_km = 10.0 ** (wc["a"] + wc["b"] * magnitude)

        centroid_lat = features.latitude if features.latitude is not None else 0.0
        centroid_lon = features.longitude if features.longitude is not None else 0.0
        r_jb_km = 0.0
        if cum and total_len > 0.0:
            s_star = float(rng.random()) * total_len
            centroid_lat, centroid_lon = point_at(fault, cum, s_star)
            segment = rupture_segment(
                fault, cum, s_star - length_km / 2.0, s_star + length_km / 2.0)
            if features.latitude is not None and features.longitude is not None:
                r_jb_km = joyner_boore_distance_km(
                    features.latitude, features.longitude, segment)

        events.append(EarthquakeEvent(
            draw_index=draw_index,
            magnitude=magnitude,
            rupture_centroid_lat=centroid_lat,
            rupture_centroid_lon=centroid_lon,
            rupture_length_km=length_km,
            r_jb_km=r_jb_km,
        ))

    return OccurrenceResult(
        asset_id=features.asset_id,
        zone=zone,
        site_class=site_class,
        fault_distance_km=fault_distance,
        lambda_annual=lambda_annual,
        lambda_effective=lambda_effective,
        n_sim=n,
        n_events=len(events),
        events=events,
    )


def simulate_portfolio_occurrence(
    features: List[AssetSeismicFeatures],
    config: SeismicModelConfig,
    fault: Optional[List[Coord]],
    rng: np.random.Generator,
    n_sim: Optional[int] = None,
) -> List[OccurrenceResult]:
    """Run Model A occurrence for every asset in a portfolio.

    Assets share the single caller-owned generator, so the whole portfolio run
    is reproducible from one seed.
    """
    return [
        simulate_asset_occurrence(f, config, fault, rng, n_sim) for f in features
    ]
