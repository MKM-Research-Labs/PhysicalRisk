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

"""
CDM boundary adapter for the seismic model.

Extracts an :class:`AssetSeismicFeatures` bundle from a commercial-asset CDM
record (the dict shape produced by the commercial portfolio generator and
persisted in ``commercial.json``). The seismic model reads only the bundle,
never the raw CDM, so the CDM schema can evolve independently.

Two resolution decisions are made at this boundary:

1. **Construction taxonomy.** The CDM ``Construction.ConstructionType`` menu
   (``Brick and block`` / ``Timber frame`` / ``Stone`` / ``Modern methods`` /
   ``Mixed construction``) is translated to the seismic fragility-class
   vocabulary of Appendix E1 via :data:`CONSTRUCTION_FRAGILITY_MAP`. This is a
   first-pass engineering-judgement mapping (seed-0) — the construction string
   sets the *base* fragility; BRI geoseismic measures supply the uplift in
   Model C, so the baseline is deliberately the un-credited case.

2. **Geoseismic measures.** The eighteen GS measures are derived (binary
   present/absent) from the asset's applied ``SeismicCodes`` list under
   ``ProtectionMeasures.RiskAssessment.GoverningBodyRatings.IndustryGroups``
   — the same list the commercial generator already writes. No CDM schema
   change and no data regeneration is required.
"""

from typing import List, Optional

from models.seismic.datastructures import AssetSeismicFeatures

__all__ = [
    "CONSTRUCTION_FRAGILITY_MAP",
    "DEFAULT_FRAGILITY_CLASS",
    "map_construction_type",
    "seismic_measures_from_record",
    "commercial_features_from_record",
    "commercial_portfolio_features",
]


# CDM ConstructionType -> Appendix E1 fragility-class key. A value not in the
# map (or a missing one) resolves to DEFAULT_FRAGILITY_CLASS. The keys cover the
# values the residential + commercial generators actually emit. Seed-0 mapping,
# open for review/recalibration. The construction string sets the *base*
# fragility; BRI geoseismic measures supply the uplift in Model C, so the
# baseline is deliberately the un-credited case (e.g. a plain "Concrete frame"
# is treated as pre-code until GS08/GS09 etc. raise it).
#   Concrete frame    -> RC_PreCode   (gravity/unconfirmed-detailing RC base)
#   Reinforced concrete-> RC_Modern   (engineered, ductile-detailed RC)
#   Steel frame       -> Steel_MRF
#   Brick and block   -> Masonry_RC   (modern reinforced blockwork)
#   Stone             -> Masonry_URM  (older unreinforced masonry — most fragile)
#   Timber frame      -> Timber
#   Modern methods    -> RC_Modern    (engineered modern construction)
#   Mixed construction-> Default      (RC pre-code-equivalent baseline)
CONSTRUCTION_FRAGILITY_MAP = {
    "Concrete frame": "RC_PreCode",
    "Reinforced concrete": "RC_Modern",
    "Steel frame": "Steel_MRF",
    "Brick and block": "Masonry_RC",
    "Stone": "Masonry_URM",
    "Timber frame": "Timber",
    "Modern methods": "RC_Modern",
    "Mixed construction": "Default",
}

DEFAULT_FRAGILITY_CLASS = "Default"


def _as_dict(obj) -> dict:
    """Return *obj* if it is a dict, else an empty dict (defensive accessor)."""
    return obj if isinstance(obj, dict) else {}


def _commercial_body(record: dict) -> dict:
    """The ``CommercialAsset`` body, tolerating an already-unwrapped record."""
    body = record.get("CommercialAsset")
    return body if isinstance(body, dict) else record


def _protection_measures(record: dict) -> dict:
    """The ``ProtectionMeasures`` block — a top-level sibling of CommercialAsset.

    In the persisted commercial record ProtectionMeasures sits alongside (not
    inside) CommercialAsset, so it is read from the raw record, mirroring the
    fire adapter.
    """
    return _as_dict(record.get("ProtectionMeasures"))


def _number(value) -> Optional[float]:
    """Coerce a numeric CDM value to float, or None when absent/non-numeric."""
    if isinstance(value, bool):
        return None
    return float(value) if isinstance(value, (int, float)) else None


def map_construction_type(cdm_construction_type: Optional[str]) -> str:
    """Translate a CDM ConstructionType to a fragility-class key.

    Unknown or missing construction types resolve to DEFAULT_FRAGILITY_CLASS.
    """
    if cdm_construction_type is None:
        return DEFAULT_FRAGILITY_CLASS
    return CONSTRUCTION_FRAGILITY_MAP.get(
        cdm_construction_type, DEFAULT_FRAGILITY_CLASS)


def seismic_measures_from_record(record: dict) -> frozenset:
    """The set of present BRI geoseismic measure codes (GS01-GS18).

    Read from the applied ``SeismicCodes`` list under
    ``ProtectionMeasures.RiskAssessment.GoverningBodyRatings.IndustryGroups``.
    Codes are upper-cased and de-duplicated; non-GS entries are dropped so the
    set carries only geoseismic measures.
    """
    groups = _as_dict(
        _as_dict(
            _as_dict(_protection_measures(record).get("RiskAssessment"))
            .get("GoverningBodyRatings")
        ).get("IndustryGroups")
    )
    codes = groups.get("SeismicCodes")
    if not isinstance(codes, list):
        return frozenset()
    return frozenset(
        c.upper() for c in codes
        if isinstance(c, str) and c.strip().upper().startswith("GS")
    )


def commercial_features_from_record(record: dict) -> Optional[AssetSeismicFeatures]:
    """Build an :class:`AssetSeismicFeatures` from one commercial CDM record.

    Returns None when the record carries no asset id or commercial type (it
    cannot be modelled and is skipped by the portfolio builder).
    """
    body = _commercial_body(record)
    header = _as_dict(body.get("Header"))
    attrs = _as_dict(body.get("CommercialAttributes"))

    asset_id = header.get("PropertyID") or header.get("UPRN")
    commercial_type = attrs.get("CommercialType")
    if not asset_id or not commercial_type:
        return None

    construction = _as_dict(body.get("Construction"))
    location = _as_dict(body.get("Location"))
    risk = _as_dict(body.get("RiskAssessment"))
    hazard = _as_dict(_protection_measures(record).get("HazardProfile"))

    storeys = attrs.get("NumberOfStoreys")

    return AssetSeismicFeatures(
        asset_id=asset_id,
        commercial_type=commercial_type,
        construction_type=map_construction_type(
            construction.get("ConstructionType")),
        number_of_storeys=int(storeys) if isinstance(storeys, (int, float)) else None,
        latitude=_number(location.get("LatitudeDegrees")),
        longitude=_number(location.get("LongitudeDegrees")),
        soil_type=risk.get("SoilType"),
        soil_vs30_mps=_number(risk.get("SoilVs30Mps")),
        seismic_hazard_class=hazard.get("SeismicHazardClass"),
        design_seismic_pga=_number(hazard.get("DesignSeismicPGA")),
        property_condition=attrs.get("PropertyCondition"),
        fault_proximity_km=None,
        measures=seismic_measures_from_record(record),
    )


def commercial_portfolio_features(records: List[dict]) -> List[AssetSeismicFeatures]:
    """Map a list of commercial CDM records to AssetSeismicFeatures.

    Records that cannot be modelled (no id / no commercial type) are skipped.
    """
    features: List[AssetSeismicFeatures] = []
    for record in records:
        feat = commercial_features_from_record(record)
        if feat is not None:
            features.append(feat)
    return features
