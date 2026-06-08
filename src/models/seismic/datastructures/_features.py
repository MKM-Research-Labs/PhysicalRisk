# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""CDM-derived seismic feature bundle."""

from dataclasses import dataclass, field
from typing import FrozenSet, Optional


@dataclass(frozen=True)
class AssetSeismicFeatures:
    """The CDM fields the seismic model needs for one commercial asset.

    A boundary adapter (cdm_adapter.py) extracts these from the commercial-asset
    CDM record; the model reads only this bundle, never the raw CDM, so the CDM
    schema can evolve independently.

    ``construction_type`` carries a *fragility-class key* (one of the Appendix E1
    classes: ``RC_Modern``, ``RC_PreCode``, ``Masonry_RC``, ``Masonry_URM``,
    ``Steel_MRF``, ``Timber``, ``Default``) — the adapter translates the raw CDM
    ConstructionType menu into this vocabulary so the model and the sensitivity
    harness share one construction taxonomy.

    The eighteen BRI geoseismic measures are carried as the set of present
    codes (``measures``); absence of a code means the measure is not installed
    and attracts no modifier. ``has(code)`` is the membership accessor Model C
    uses.

    Attributes:
        asset_id: stable identifier for the asset.
        commercial_type: CommercialType option (e.g. "Office", "Hotel").
        construction_type: fragility-class key (see above); None -> Default.
        number_of_storeys: NumberOfStoreys (height proxy), or None.
        latitude: asset latitude (degrees), or None if unknown.
        longitude: asset longitude (degrees), or None if unknown.
        soil_type: CDM SoilType menu value (informational), or None.
        soil_vs30_mps: SoilVs30Mps (m/s) when carried by the record, else None
            (Model B falls back to the site-class V_S30 proxy).
        seismic_hazard_class: HazardProfile.SeismicHazardClass menu value
            (None/Low/Medium/High/Extreme), or None.
        design_seismic_pga: DesignSeismicPGA (g) for the mapped class, or None.
        property_condition: PropertyCondition option, or None.
        fault_proximity_km: distance to the nearest fault (km). Left None by the
            adapter and computed at run time from the catchment fault trace
            (Model A); a supplied value overrides that computation.
        measures: frozenset of present BRI geoseismic measure codes (GS01-GS18).
    """
    asset_id: str
    commercial_type: str
    construction_type: Optional[str] = None
    number_of_storeys: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    soil_type: Optional[str] = None
    soil_vs30_mps: Optional[float] = None
    seismic_hazard_class: Optional[str] = None
    design_seismic_pga: Optional[float] = None
    property_condition: Optional[str] = None
    fault_proximity_km: Optional[float] = None
    measures: FrozenSet[str] = field(default_factory=frozenset)

    def has(self, code: str) -> bool:
        """True when BRI geoseismic measure *code* (e.g. "GS12") is present."""
        return code in self.measures
