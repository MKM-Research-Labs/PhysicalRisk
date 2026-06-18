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

"""Flatten PropertyHeader (Header, Valuation, Attributes, Construction, Location)."""


def flatten_header(prop: dict) -> dict:
    """Return flat snake_case keys for PropertyHeader intrinsic-fact sections."""
    ph = prop.get("PropertyHeader", {})
    header = ph.get("Header", {})
    valuation = ph.get("Valuation", {})
    attrs = ph.get("PropertyAttributes", {})
    construction = ph.get("Construction", {})
    location = ph.get("Location", {})

    return {
        "property_id":      header.get("PropertyID"),
        "catchment_id":     header.get("CatchmentID"),
        "uprn":             header.get("UPRN"),
        "property_type":    header.get("propertyType", "residential"),
        "property_status":  header.get("propertyStatus", "active"),

        "value":             valuation.get("PropertyValue"),
        "valuation_date":    valuation.get("ValuationDate"),
        "valuation_method":  valuation.get("ValuationMethod"),

        "occupancy_type":     attrs.get("OccupancyType"),
        "property_area_sqm":  attrs.get("PropertyAreaSqm"),
        "property_resi":      attrs.get("PropertyResi"),
        "number_storeys":     attrs.get("NumberOfStoreys"),
        "construction_year":  attrs.get("ConstructionYear"),
        "property_period":    attrs.get("PropertyPeriod"),
        "council_tax_band":   attrs.get("CouncilTaxBand"),
        "number_bedrooms":    attrs.get("NumberBedrooms"),
        "number_bathrooms":   attrs.get("NumberBathrooms"),
        "property_condition": attrs.get("PropertyCondition"),

        "construction_type":  construction.get("ConstructionType"),
        "foundation_type":    construction.get("FoundationType"),
        "floor_level_metres": construction.get("FloorLevelMeters"),
        "basement_present":   construction.get("BasementPresent"),

        "first_floor_height_m":  construction.get("FloorLevelMeters"),  # OED FirstFloorHeight alias

        # Roof details
        "roof_cover":          construction.get("RoofDetails", {}).get("RoofCover"),
        "roof_geometry":       construction.get("RoofDetails", {}).get("RoofGeometry"),
        "roof_pitch":          construction.get("RoofDetails", {}).get("RoofPitch"),
        "roof_frame":          construction.get("RoofDetails", {}).get("RoofFrame"),
        "roof_deck":           construction.get("RoofDetails", {}).get("RoofDeck"),
        "roof_year_replaced":  construction.get("RoofDetails", {}).get("RoofYearReplaced"),

        # Structural characteristics
        "soft_story":          construction.get("SoftStory"),
        "shape_irregularity":  construction.get("ShapeIrregularity"),
        "brick_veneer":        construction.get("BrickVeneer"),
        "glass_type":          construction.get("GlassType"),
        "retrofit_year":       construction.get("RetrofitYear"),
        "has_cripple_wall":    construction.get("HasCrippleWall"),

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
    }
