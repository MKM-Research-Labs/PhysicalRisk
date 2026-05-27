# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Commercial asset extensions to the asset CDM.

Scope: office, retail, hotel, leisure, healthcare, mixed-use.
Industrial / warehousing / manufacturing live in asset/industrial/ —
their risk profile and regulatory burden diverge enough to warrant
their own package.

Holds ONLY commercial-specific schema. Resilience, history and energy are
shared with residential / industrial / infrastructure and live at the
asset/ level — they are NOT duplicated here.

Reference taxonomy (MSCI Property Sector + UK Use Class Order):

    CommercialType (menu):
        Office              — HQ, multi-let office, business park
                              (Use Class E.g.i)
        Retail              — Standard shops, Shopping centre,
                              Retail warehouse, Supermarket,
                              Department store (Use Class E.a)
        Hotel               — Full service, Limited service, Luxury,
                              Budget, Serviced apartments (Use Class C1)
        Leisure             — Restaurant, Gym, Cinema, Pub
                              (Use Class E / sui generis depending on
                              activity)
        Healthcare          — Clinic, GP surgery, Private hospital
                              (Use Class E.e or F.1)
        MixedUse            — Buildings combining two or more of the
                              above with significant non-residential use
        Other               — Catch-all for unusual asset types
                              (student, senior living, etc.)

The MSCI sector menu drives the financial / insurance shape; the UK Use
Class is carried separately as a regulatory/planning attribute so we don't
conflate financial classification with planning classification.

Candidate modules to create here from Commercial_Property_CDM_v1.xlsx
(commercial-only fields that survive once industrial fields move out):

    header.py    Commercial-only attributes:
                 CommercialType (see menu above),
                 UseClassUKO (text — e.g. 'E(g)(i)', 'C1', 'sui generis'),
                 BusinessRatesCategory, OccupancyStatus
                 (Fully occupied / Partially vacant / Vacant),
                 TotalUnits, NetInternalAreaSqm,
                 NetLettableAreaSqm, ParkingSpaces,
                 PlantRoomLocation, ServiceCore

    tenancy.py   Lease economics (commercial-specific):
                 TenancySchedule (rent roll), AnchorTenant,
                 WAULT (years), ServiceChargeGbpPerSqm,
                 NetInitialYield, EquivalentYield, ReversionaryYield,
                 CovenantStrength

    accessibility.py  DisabledAccess, GoodsLiftCount, GoodsLiftCapacity,
                      EmergencyExits, DeliveryBays
                      (DeliveryBays also relevant to industrial — could
                      promote to asset/header.py later)

    cdm.py       CommercialAssetCDM — composes asset.* + commercial.*
                 schemas, exposes the same validate / create_mapping /
                 get_required_fields surface as ResidentialAssetCDM today.

Sector-specific extensions (optional further split if a single header.py
gets cluttered):

    hotel.py    StarRating, NumberOfRooms, NumberOfKeys, FBOffering,
                ConferenceSpaceSqm
    retail.py   AnchorTenantPresent, FootfallAnnual, TradeMixCategory
                (high-street / convenience / destination)
    office.py   GradeClassification (A/B/C), CoreToFloorPlateRatio,
                FloorPlateSqm, RaisedAccessFloor (boolean),
                CeilingHeightMeters

Open vocabulary alignments (resolve in shared asset/* before populating):

    FloodRiskType    residential uses Fluvial/Pluvial/GroundWater/...;
                     commercial v1 uses River/Surface water/Groundwater/...
                     Pick one canonical menu in asset/resilience.py.
    PropertyPeriod   residential …1919-1944, 1945-1975… vs commercial v1
                     …1919-1949, 1950-1975…. Pick one.
    ConstructionType union the menus (Steel/Concrete frame from commercial
                     + Brick and block/Timber frame/Stone from residential).
    Resilience vocab commercial v1 uses booleans; align to the 5-level
                     RESILIENCE_LEVELS menu so BRI scoring works.

Reference workbook (gitignored, do not load at runtime):
    Commercial_Property_CDM_v1.xlsx
"""

from .cdm import CommercialAssetCDM  # noqa: F401
from .schema import COMMERCIAL_SCHEMA, DEFAULT_ELEVATION  # noqa: F401

__all__ = ["CommercialAssetCDM", "COMMERCIAL_SCHEMA", "DEFAULT_ELEVATION"]
