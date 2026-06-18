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

"""Occurrence rate resolution and magnitude sampling (Model A).

The per-asset annual rate lambda_i = lambda_zone * m_fault * m_soil (Appendix
A), and the magnitude is drawn from the truncated Gutenberg-Richter law by
inverse transform.
"""

import math
from typing import List, Optional

import numpy as np

from config.seismic import GroundMotionConfig, OccurrenceConfig, SeismicModelConfig
from models.floodrisk.spatial import nearest_point_on_polyline
from models.seismic.datastructures import AssetSeismicFeatures
from models.seismic.occurrence._fault import Coord


def resolve_zone(features: AssetSeismicFeatures, cfg: OccurrenceConfig) -> str:
    """The seismic hazard zone for an asset (from its CDM hazard class)."""
    zone = cfg.hazard_class_to_zone.get(features.seismic_hazard_class)
    if zone in cfg.zones:
        return zone
    return cfg.default_zone


def resolve_site_class(vs30: Optional[float], gm_cfg: GroundMotionConfig) -> str:
    """The Eurocode 8 site class (A-E) for a V_S30, else the default class."""
    if vs30 is None:
        return gm_cfg.default_site_class
    ordered = sorted(gm_cfg.vs30_bands.items(), key=lambda kv: kv[1], reverse=True)
    for cls, lower in ordered:
        if vs30 >= lower:
            return cls
    return ordered[-1][0]


def asset_fault_distance_km(
    features: AssetSeismicFeatures, fault: Optional[List[Coord]],
) -> Optional[float]:
    """Static asset-to-fault distance (km).

    Prefers an explicit ``fault_proximity_km`` on the features; otherwise it is
    derived from the catchment fault trace. Returns None when neither the
    coordinates nor an explicit value are available.
    """
    if features.fault_proximity_km is not None:
        return features.fault_proximity_km
    if not fault or features.latitude is None or features.longitude is None:
        return None
    return nearest_point_on_polyline(
        features.latitude, features.longitude, fault)[2] / 1000.0


def fault_proximity_modifier(
    features: AssetSeismicFeatures,
    fault_distance_km: Optional[float],
    cfg: OccurrenceConfig,
) -> float:
    """Near-fault occurrence uplift m_fault (Appendix A2)."""
    fp = cfg.fault_proximity
    if (fault_distance_km is not None
            and fault_distance_km < fp["threshold_km"]
            and not features.has("GS01")):
        return 1.0 + fp["delta_gs01"]
    return 1.0


def asset_lambda(
    features: AssetSeismicFeatures,
    fault_distance_km: Optional[float],
    site_class: str,
    config: SeismicModelConfig,
) -> float:
    """Per-asset annual occurrence rate lambda_i = lambda_zone * m_fault * m_soil."""
    occ = config.occurrence
    zone = resolve_zone(features, occ)
    lambda_zone = occ.zones[zone]["lambda_zone"]
    m_fault = fault_proximity_modifier(features, fault_distance_km, occ)
    m_soil = occ.soil_recurrence_m_soil.get(site_class, 1.0)
    return lambda_zone * m_fault * m_soil


def sample_magnitude(
    b: float, m_min: float, m_max: float, rng: np.random.Generator,
) -> float:
    """Draw a magnitude from the truncated Gutenberg-Richter law by inversion.

    ``m = m_min - (1/b) * log10(1 - u * (1 - 10^{-b (m_max - m_min)}))`` with
    ``u ~ Uniform(0, 1)`` maps the unit interval onto ``[m_min, m_max]``.
    """
    if m_max <= m_min or b <= 0.0:
        return m_min
    u = float(rng.random())
    span = 1.0 - 10.0 ** (-b * (m_max - m_min))
    return m_min - (1.0 / b) * math.log10(1.0 - u * span)
