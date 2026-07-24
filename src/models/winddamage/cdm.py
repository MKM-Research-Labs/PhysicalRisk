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

"""Property CDM record navigation.

Single place that knows the on-disk shape of a property / commercial
record. The damage model navigates the CDM exclusively through this
module so a future schema refactor only touches one file.

CDM paths used:
  PropertyHeader.Header.PropertyID                                       — id
  ProtectionMeasures.HazardProfile.WindThresholdMinorMps                 — threshold (preferred, damage-onset)
  ProtectionMeasures.HazardProfile.WindThresholdMajorMps                 — threshold (severe fallback)
  ProtectionMeasures.HazardProfile.WindThresholdKph                      — threshold (legacy)
  ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIWindScore    — wind BRI
  ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIScore        — composite BRI
"""

from typing import Optional, Tuple


__all__ = [
    "extract_property_id",
    "extract_wind_threshold_mps",
    "extract_wind_threshold_kph",
    "extract_bri_scores",
    "extract_lon_lat",
]


def _get_nested(record: dict, *path: str):
    """Return record[path[0]][path[1]]... or None if any segment is missing."""
    node = record
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
        if node is None:
            return None
    return node


def extract_property_id(record: dict) -> Optional[str]:
    """Return PROP-... / CPROP-... id from a property or commercial record."""
    value = _get_nested(record, "PropertyHeader", "Header", "PropertyID")
    if value is None:
        # Commercial records nest the id under CommercialAsset/Header.
        value = _get_nested(record, "CommercialAsset", "Header", "PropertyID")
    if value is None:
        # Older/alternate commercial layout puts the id at the top-level Header.
        value = _get_nested(record, "Header", "PropertyID")
    return value


def extract_wind_threshold_mps(record: dict) -> Optional[float]:
    """Return the property's wind damage-onset threshold in m/s, or None if absent.

    Resolution order:
        0. ProtectionMeasures.HazardProfile.DesignWindSpeedKmh / 3.6 (preferred
           — the speed THIS building was designed to withstand, so the speed at
           which its damage begins)
        1. ProtectionMeasures.HazardProfile.WindThresholdMinorMps (the BRI
           damage-ONSET level, published per resilience grade)
        2. ProtectionMeasures.HazardProfile.WindThresholdMajorMps (severe-damage
           level; used when no Minor threshold is published)
        3. ProtectionMeasures.HazardProfile.WindThresholdKph / 3.6 (legacy)

    Design speed takes precedence because it is the only per-asset quantity in
    the set. The BRI thresholds are uniform across the prototype catalogue, so
    keying off them gave every asset in a portfolio an identical trigger and no
    wind differentiation at all: on halong, all ten commercial assets fired on
    the same five events out of a thousand.

    Minor is preferred over Major for the same reason it always was: PRS counts
    the onset of wind damage, not the onset of *severe* damage, and keying off
    the Major (catastrophic) level made commercial wind effectively never
    trigger.
    """
    design_kph = _get_nested(
        record, "ProtectionMeasures", "HazardProfile", "DesignWindSpeedKmh"
    )
    if design_kph is not None:
        try:
            design = float(design_kph)
            if design > 0:
                return design / 3.6
        except (TypeError, ValueError):
            pass  # unusable — fall through to the published thresholds

    for field in ("WindThresholdMinorMps", "WindThresholdMajorMps"):
        mps = _get_nested(record, "ProtectionMeasures", "HazardProfile", field)
        if mps is not None:
            try:
                return float(mps)
            except (TypeError, ValueError):
                pass  # garbage at this level — fall through to the next

    kph = _get_nested(
        record, "ProtectionMeasures", "HazardProfile", "WindThresholdKph"
    )
    if kph is None:
        return None
    try:
        return float(kph) / 3.6
    except (TypeError, ValueError):
        return None


def extract_wind_threshold_kph(record: dict) -> Optional[float]:
    """Return the property's wind threshold in km/h.

    DEPRECATED: prefer extract_wind_threshold_mps. Retained as an alias that
    reads the legacy WindThresholdKph field directly, then falls back to
    WindThresholdMajorMps × 3.6 when only the new field is populated.
    """
    value = _get_nested(record, "ProtectionMeasures", "HazardProfile", "WindThresholdKph")
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass

    mps = _get_nested(
        record, "ProtectionMeasures", "HazardProfile", "WindThresholdMajorMps"
    )
    if mps is None:
        return None
    try:
        return float(mps) * 3.6
    except (TypeError, ValueError):
        return None


def extract_lon_lat(record: dict) -> Tuple[Optional[float], Optional[float]]:
    """Return (longitude, latitude) from PropertyHeader.Location (residential)
    or CommercialAsset.Location (commercial), or (None, None)."""
    loc = _get_nested(record, "PropertyHeader", "Location")
    if not isinstance(loc, dict):
        loc = _get_nested(record, "CommercialAsset", "Location")
    if not isinstance(loc, dict):
        return None, None

    def _maybe(key: str) -> Optional[float]:
        v = loc.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return _maybe("LongitudeDegrees"), _maybe("LatitudeDegrees")


def extract_bri_scores(record: dict) -> Tuple[Optional[float], Optional[float]]:
    """Return (BRIWindScore, BRIScore) as (wind, composite); either may be None."""
    ratings = _get_nested(
        record, "ProtectionMeasures", "RiskAssessment", "GoverningBodyRatings"
    )
    if not isinstance(ratings, dict):
        return None, None

    def _maybe(key: str) -> Optional[float]:
        v = ratings.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return _maybe("BRIWindScore"), _maybe("BRIScore")
