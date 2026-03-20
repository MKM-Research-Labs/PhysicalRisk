# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Property CDM flat-mapping logic.

Provides create_mapping() as a module-level function that flattens the nested
CDM structure into a snake_case dict suitable for downstream model consumption.
"""

from .schema import DEFAULT_ELEVATION


def create_mapping(prop: dict, default_elevation: float = DEFAULT_ELEVATION) -> dict:
    """
    Flatten a nested property CDM record into a snake_case dict.

    Args:
        prop:              Nested property data in CDM format.
        default_elevation: Fallback when GroundLevelMeters is absent.

    Returns:
        Flat dict with snake_case keys.  None-valued keys are omitted.

    Raises:
        ValueError: If the mapping transformation fails unexpectedly.
    """
    try:
        ph           = prop.get("PropertyHeader", {})
        header       = ph.get("Header", {})
        valuation    = ph.get("Valuation", {})
        attrs        = ph.get("PropertyAttributes", {})
        construction = ph.get("Construction", {})
        location     = ph.get("Location", {})
        risk         = ph.get("RiskAssessment", {})

        pm         = prop.get("ProtectionMeasures", {})
        pm_risk    = pm.get("RiskAssessment", {})
        resilience = pm.get("ResilienceMeasures", {})

        trans    = prop.get("TransactionHistory", {})
        purchase = trans.get("Purchase", {})
        rental   = trans.get("Rental", {})

        ground_level = risk.get("GroundLevelMeters")
        if ground_level is None:
            ground_level = default_elevation

        flat = {
            # Header
            "property_id":      header.get("PropertyID"),
            "catchment_id":     header.get("CatchmentID"),
            "uprn":             header.get("UPRN"),
            "property_type":    header.get("propertyType", "residential"),
            "property_status":  header.get("propertyStatus", "active"),

            # Valuation
            "value":             valuation.get("PropertyValue"),
            "valuation_date":    valuation.get("ValuationDate"),
            "valuation_method":  valuation.get("ValuationMethod"),

            # Attributes
            "occupancy_type":    attrs.get("OccupancyType"),
            "property_area_sqm": attrs.get("PropertyAreaSqm"),
            "property_resi":     attrs.get("PropertyResi"),
            "number_storeys":    attrs.get("NumberOfStoreys"),
            "construction_year": attrs.get("ConstructionYear"),
            "property_period":   attrs.get("PropertyPeriod"),
            "council_tax_band":  attrs.get("CouncilTaxBand"),
            "number_bedrooms":   attrs.get("NumberBedrooms"),
            "number_bathrooms":  attrs.get("NumberBathrooms"),
            "property_condition": attrs.get("PropertyCondition"),

            # Construction
            "construction_type":  construction.get("ConstructionType"),
            "foundation_type":    construction.get("FoundationType"),
            "floor_level_metres": construction.get("FloorLevelMeters"),
            "basement_present":   construction.get("BasementPresent"),

            # Location
            "building_number": location.get("BuildingNumber"),
            "street_name":     location.get("StreetName"),
            "town_city":       location.get("TownCity"),
            "county":          location.get("County"),
            "postcode":        location.get("Postcode"),
            "local_authority": location.get("LocalAuthority"),
            "country":         location.get("Country"),
            "region":          location.get("Region"),
            "urban_rural":     location.get("UrbanRuralClassification"),
            "latitude":        location.get("LatitudeDegrees"),
            "longitude":       location.get("LongitudeDegrees"),

            # Risk Assessment (critical for flood model)
            "flood_zone":         risk.get("EAFloodZone"),
            "overall_flood_risk": risk.get("OverallFloodRisk"),
            "flood_risk_type":    risk.get("FloodRiskType"),
            "ground_level_meters": ground_level,
            "elevation":          ground_level,   # alias for flood model compatibility
            "river_distance":     risk.get("RiverDistanceMeters"),

            # Protection
            "insurance_premium":   pm_risk.get("InsurancePremium"),
            "risk_rating":         pm_risk.get("RiskRating"),
            "flood_gates":         resilience.get("FloodGates"),
            "flood_barriers":      resilience.get("FloodBarriers"),
            "sump_pump":           resilience.get("SumpPump"),
            "flood_warning_system": resilience.get("FloodWarningSystem"),

            # Transactions
            "purchase_date":  purchase.get("PurchaseDate"),
            "purchase_price": purchase.get("PurchasePriceGbp"),
            "monthly_rent":   rental.get("MonthlyRentGbp"),
            "rental_yield":   rental.get("RentalYield"),
        }

        # Strip None values
        return {k: v for k, v in flat.items() if v is not None}

    except Exception as exc:
        raise ValueError(f"Error creating property mapping: {exc}") from exc
