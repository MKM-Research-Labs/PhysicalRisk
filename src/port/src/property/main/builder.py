# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Property building mixin for PropertyPortfolioGenerator."""

from datetime import date, datetime, timedelta
from typing import Dict

from config import config
from port.utils.schema import build_section


# --- Cross-field consistency lookup tables ---------------------------------

# TownCity → County map for Thames-area locations. Falls back to "Greater
# London" for unknown towns, which is the historical default.
_TOWN_TO_COUNTY = {
    "London": "Greater London",
    "Westminster": "Greater London",
    "Camden": "Greater London",
    "Greenwich": "Greater London",
    "Reading": "Berkshire",
    "Slough": "Berkshire",
    "Windsor": "Berkshire",
    "Maidenhead": "Berkshire",
    "Oxford": "Oxfordshire",
    "Wallingford": "Oxfordshire",
    "Henley-on-Thames": "Oxfordshire",
    "Kingston upon Thames": "Greater London",
    "Richmond": "Greater London",
    "Twickenham": "Greater London",
}

# EAFloodZone → OverallFloodRisk (and FloodHazardClass already tracks zone too).
_ZONE_TO_FLOOD_RISK = {
    "Zone 1": "Low",
    "Zone 2": "Medium",
    "Zone 3a": "High",
    "Zone 3b": "Very high",
}

# Construction year → PropertyPeriod mapping (mirrors property_utils.get_property_period).
def _period_from_year(year: int) -> str:
    if year < 1919: return "Pre-1919"
    if year < 1945: return "1919-1944"
    if year < 1976: return "1945-1975"
    if year < 2000: return "1976-1999"
    if year < 2009: return "2000-2008"
    return "2009-Present"


def _years_since(date_str) -> float:
    """Return fractional years between today and an ISO date string. None on parse failure."""
    if date_str is None:
        return None
    try:
        if isinstance(date_str, str):
            d = datetime.fromisoformat(date_str.split('T')[0]).date()
        elif isinstance(date_str, datetime):
            d = date_str.date()
        elif isinstance(date_str, date):
            d = date_str
        else:
            return None
        return max(0.0, (date.today() - d).days / 365.25)
    except (ValueError, TypeError):
        return None


class BuilderMixin:
    """Mixin providing property data construction methods."""

    def _generate_single_property(self, index: int, schema: Dict, location: Dict) -> tuple:
        """Generate a single property data structure."""
        # Generate property metadata
        property_metadata = self.random.generate_property_metadata(index, location)
        property_id = property_metadata['property_id']

        self.log(f"  Creating property {property_id} at {location['name']}", "DEBUG")

        # Build property data from schema
        property_data = self._build_section(schema, index, property_metadata)

        # Set specific values that need consistency
        self._set_specific_property_values(property_data, property_id, index, property_metadata, location)

        # Patch cross-field inconsistencies left by independent lambda draws
        # (e.g. PropertyPeriod vs ConstructionYear, RentalYield vs PropertyValue).
        self._apply_consistency_fixes(property_data)

        # Override the schema-built resilience checklist with the age/condition/
        # zone-aware generator, then apply the BRI letter ratings. BRI *scores*
        # (BRIScore + per-hazard *Score) are intentionally left blank — a
        # downstream methodology will fill them in.
        self._populate_resilience_and_rating(property_data)

        return property_data, property_id

    def _apply_consistency_fixes(self, property_data: Dict) -> None:
        """Patch fields that should be derived from siblings rather than rolled
        independently. Runs after the schema-walker has produced raw values.

        Fixes:
          - PropertyPeriod ← derived from ConstructionYear
          - NumberOfStoreys forced to 1 when PropertyResi == "Bungalow"
          - PropertyHeight synced to HeightMeters
          - County looked up from TownCity (Thames-area gazetteer)
          - OverallFloodRisk ← derived from EAFloodZone
          - PurchasePriceGbp ← derived from PropertyValue and PurchaseDate
                              (assumes ~4 %/year nominal appreciation)
          - RentalYield ← (MonthlyRentGbp * 12 / PropertyValue) * 100
          - SalePriceGbp ← derived from PropertyValue and SaleDate
          - LastFloodDateHistory cleared when FloodDamageSeverity == "No damage"
          - LastFireDate populated when FireDamageSeverity != "None"
        """
        ph = property_data.get('PropertyHeader', {})
        attrs = ph.get('PropertyAttributes', {})
        construction = ph.get('Construction', {})
        location = ph.get('Location', {})
        risk = ph.get('RiskAssessment', {})
        valuation = ph.get('Valuation', {})

        # PropertyPeriod ← ConstructionYear
        year = attrs.get('ConstructionYear')
        if isinstance(year, int):
            attrs['PropertyPeriod'] = _period_from_year(year)

        # Bungalow ⇒ single-storey
        if attrs.get('PropertyResi') == 'Bungalow':
            attrs['NumberOfStoreys'] = 1

        # PropertyHeight ← HeightMeters (treat them as the same measurement)
        if 'HeightMeters' in attrs and 'PropertyHeight' in construction:
            construction['PropertyHeight'] = attrs['HeightMeters']

        # County ← TownCity lookup
        town = location.get('TownCity')
        if town and town in _TOWN_TO_COUNTY:
            location['County'] = _TOWN_TO_COUNTY[town]

        # OverallFloodRisk ← EAFloodZone
        zone = risk.get('EAFloodZone')
        if zone in _ZONE_TO_FLOOD_RISK:
            risk['OverallFloodRisk'] = _ZONE_TO_FLOOD_RISK[zone]

        # --- TransactionHistory consistency ---------------------------------
        trans = property_data.get('TransactionHistory', {})
        purchase = trans.get('Purchase', {})
        sales = trans.get('Sales', {})
        rental = trans.get('Rental', {})

        property_value = valuation.get('PropertyValue')

        # PurchasePrice ← PropertyValue discounted by years since purchase.
        if property_value and purchase.get('PurchaseDate'):
            years_ago = _years_since(purchase['PurchaseDate'])
            if years_ago is not None:
                purchase['PurchasePriceGbp'] = round(
                    property_value / (1.04 ** years_ago), 2
                )

        # SalePrice ← PropertyValue discounted by years since the past sale.
        if property_value and sales.get('SaleDate'):
            years_ago = _years_since(sales['SaleDate'])
            if years_ago is not None:
                sales['SalePriceGbp'] = round(
                    property_value / (1.04 ** years_ago), 2
                )

        # RentalYield ← (MonthlyRent * 12 / PropertyValue) * 100; clear both
        # when the property has never been rented.
        rent = rental.get('MonthlyRentGbp')
        if rental.get('RentalHistory') == 'Never rented':
            rental['MonthlyRentGbp'] = None
            rental['RentalYield'] = None
        elif property_value and rent:
            rental['RentalYield'] = round((rent * 12 / property_value) * 100, 2)

        # --- HistoryAndIncidents nullable chain -----------------------------
        history = property_data.get('HistoryAndIncidents', {})
        flood = history.get('FloodEvents', {})
        fire = history.get('FireIncidents', {})

        # If FloodDamageSeverity == "No damage", clear the historic flood date.
        if flood.get('FloodDamageSeverity') == 'No damage':
            flood['LastFloodDateHistory'] = None

        # If FireDamageSeverity != "None", ensure a LastFireDate is populated.
        fire_severity = fire.get('FireDamageSeverity')
        if fire_severity and fire_severity != 'None' and not fire.get('LastFireDate'):
            # Pick a date in the past 10 years (severe fires aren't ancient).
            days_ago = (2 + (hash(str(fire_severity)) % 8)) * 365
            fire['LastFireDate'] = (date.today() - timedelta(days=days_ago)).isoformat()

    def _populate_resilience_and_rating(self, property_data: Dict) -> None:
        """Generate the resilience checklist, stamp the BRI letter ratings, and
        apply the flood-spec model to fill the BRI score fields.

        Order matters:
          1. ``generate_resilience`` builds the checklist sub-sections.
          2. ``apply_bri_rating`` stamps the per-hazard + overall letter
             ratings (does NOT touch score fields).
          3. ``apply_flood_resilience_score`` computes the spec's flood
             resilience score and writes it (rescaled to 0-1) into
             BRIFloodScore + jittered siblings + overall BRIScore.

        Imports are local + dispatched via ``config.load_random_module`` so
        the builder picks up the active catchment's resilience module
        (port.rand.<catchment_id>.property.property_random.resilience),
        not a literal ``port.rand.thames.*`` path.
        """
        resilience_module = config.load_random_module('property.property_random.resilience')
        generate_resilience = resilience_module.generate_resilience
        apply_flood_resilience_score = resilience_module.apply_flood_resilience_score
        from port.cdm.asset.residential.bri import apply_bri_rating

        resilience = generate_resilience(property_data)
        pm = property_data.setdefault('ProtectionMeasures', {})
        pm['ResilienceMeasures'] = resilience
        apply_bri_rating(property_data, agent='Bureau Veritas')
        apply_flood_resilience_score(property_data)

    def _build_section(self, section_schema: Dict, index: int, metadata: Dict) -> Dict:
        """Recursively build a section of property data based on the schema."""
        return build_section(section_schema, index, metadata, self.random)

    def _set_specific_property_values(self, property_data: Dict, property_id: str,
                                      index: int, metadata: Dict, location: Dict):
        """Set specific property values that need to be consistent across sections.

        Writes PropertyID/CatchmentID into PropertyHeader.Header (schema home),
        Lat/Long into PropertyHeader.Location, and GroundLevelMeters into
        PropertyHeader.RiskAssessment (overriding the lambda output with the
        rounded value).
        """
        if 'PropertyHeader' not in property_data:
            property_data['PropertyHeader'] = {}

        header = property_data['PropertyHeader']

        # Header section — PropertyID + CatchmentID live here per schema.
        if 'Header' not in header:
            header['Header'] = {}
        header['Header']['PropertyID'] = property_id
        header['Header']['CatchmentID'] = config.CATCHMENT

        # Location — lat/long
        if 'Location' not in header:
            header['Location'] = {}
        loc = header['Location']
        loc['LatitudeDegrees'] = location['lat']
        loc['LongitudeDegrees'] = location['lon']

        # GroundLevelMeters belongs in PropertyHeader.RiskAssessment, not Location.
        if 'elevation' in location:
            if 'RiskAssessment' not in header:
                header['RiskAssessment'] = {}
            header['RiskAssessment']['GroundLevelMeters'] = round(location['elevation'], 2)

        # Store reference gauge IDs.  If placed relative to a synthetic gauge
        # (new pipeline), use the synthetic ID as primary.  Otherwise fall back
        # to legacy index-based mapping.
        synth_id = location.get('synthetic_gauge_id')
        if synth_id:
            header['ReferenceGauges'] = [synth_id]
        else:
            ref_indices = location.get('reference_gauge_indices', [])
            if ref_indices:
                gauge_id_map = getattr(self, '_gauge_id_map', {})
                header['ReferenceGauges'] = [
                    gauge_id_map.get(idx, f"GAUGE-{idx + 1:03d}") for idx in ref_indices
                ]
