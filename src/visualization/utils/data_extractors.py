"""
Data extraction utilities for the visualization system.

This module provides functions for extracting and processing data from various
JSON structures including properties, mortgages, gauges, and flood risk data.
"""

from typing import Dict, List, Any, Optional, Union
import re
from datetime import datetime


class DataExtractor:
    """Utility class for extracting data from complex nested structures."""
    
    @classmethod
    def extract_property_info(cls, prop: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract property information from the given property data.

        Args:
            prop: The property data dictionary

        Returns:
            Dictionary containing extracted property information or None if extraction fails
        """
        try:
            # Extract header information
            header = prop.get('PropertyHeader', {}).get('Header', {})
            property_id = header.get('PropertyID', 'Unknown')
            property_type = header.get('propertyType', 'Unknown')
            property_status = header.get('propertyStatus', 'Unknown')
            
            # Extract property attributes
            property_attrs = prop.get('PropertyHeader', {}).get('PropertyAttributes', {})
            building_type = property_attrs.get('PropertyType', 'Unknown')
            construction_year = property_attrs.get('ConstructionYear', 'Unknown')
            number_of_storeys = property_attrs.get('NumberOfStoreys', 'Unknown')
            
            # Extract construction information
            construction = prop.get('PropertyHeader', {}).get('Construction', {})
            construction_type = construction.get('ConstructionType', 'Unknown')
            
            # Extract location information - try multiple possible field names
            location = prop.get('PropertyHeader', {}).get('Location', {})
            lat = location.get('LatitudeDegrees') or location.get('Latitude')
            lon = location.get('LongitudeDegrees') or location.get('Longitude')
            
            # Validate coordinates
            if lat is None or lon is None:
                print(f"Warning: Invalid coordinates for property {property_id}")
                return None
            
            # Extract address components
            building_number = location.get('BuildingNumber', '')
            street_name = location.get('StreetName', '')
            town_city = location.get('TownCity', '')
            post_code = location.get('Postcode', '')

            # Extract risk and value information
            flood_risk = prop.get('FloodRisk', 'Unknown')
            thames_proximity = prop.get('ThamesProximity', 'Unknown')
            ground_elevation = prop.get('GroundElevation', 'Unknown')
            elevation_estimated = prop.get('ElevationEstimated', False)
            
            # Try multiple paths for property value
            property_value = cls._extract_property_value(prop)
            
            # Construct the extracted information dictionary
            extracted_info = {
                'property_id': property_id,
                'property_type': property_type,
                'property_status': property_status,
                'building_type': building_type,
                'construction_year': construction_year,
                'number_of_storeys': number_of_storeys,
                'construction_type': construction_type,
                'coordinates': {'latitude': lat, 'longitude': lon},
                'address': {
                    'building_number': building_number,
                    'street_name': street_name,
                    'town_city': town_city,
                    'post_code': post_code
                },
                'flood_risk': flood_risk,
                'thames_proximity': thames_proximity,
                'ground_elevation': ground_elevation,
                'elevation_estimated': elevation_estimated,
                'property_value': property_value,
                'property_age_factor': cls._calculate_age_factor(construction_year)
            }

            return extracted_info
            
        except Exception as e:
            print(f"Error extracting property info for {prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID', 'Unknown')}: {e}")
            return None
    
    @classmethod
    def extract_mortgage_info(cls, mortgage: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract mortgage information from mortgage data.
        
        Args:
            mortgage: Raw mortgage data dictionary
            
        Returns:
            Structured mortgage data or None if extraction fails
        """
        try:
            # Handle nested structure
            mort_data = mortgage.get('Mortgage', mortgage)
            
            # Extract the Header section
            header = mort_data.get('Header', {})
            property_id = header.get('PropertyID')
            
            if not property_id:
                print("Warning: PropertyID is missing or empty in mortgage data")
                return None

            # Extract financial terms
            financial_terms = mort_data.get('FinancialTerms', {})
            application = mort_data.get('Application', {})
            
            # Try different field names for term years
            term_years = cls._extract_term_years(financial_terms)
            
            mortgage_info = {
                # Header section
                'mortgage_id': header.get('MortgageID'),
                'property_id': property_id,
                'uprn': header.get('UPRN'),
                
                # Financial terms
                'original_loan': financial_terms.get('OriginalLoan'),
                'current_balance': financial_terms.get('CurrentBalance'),
                'original_lending_rate': financial_terms.get('OriginalLendingRate'),
                'current_rate': financial_terms.get('CurrentRate'),
                'loan_to_value_ratio': financial_terms.get('LoanToValueRatio'),
                'term_years': term_years,
                'monthly_payment': financial_terms.get('MonthlyPayment'),
                
                # Application details
                'mortgage_provider': application.get('MortgageProvider'),
                'application_date': application.get('ApplicationDate'),
                'completion_date': application.get('CompletionDate'),
                
                # Store original structure for backward compatibility
                'Header': header,
                'FinancialTerms': financial_terms,
                'Application': application
            }
            
            # Remove None values
            return {k: v for k, v in mortgage_info.items() if v is not None}
            
        except Exception as e:
            print(f"Error extracting mortgage info: {str(e)}")
            return None
    
    @classmethod
    def extract_gauge_info(cls, gauge: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract gauge information from gauge data.
        
        Args:
            gauge: Raw gauge data dictionary
            
        Returns:
            Structured gauge data or None if extraction fails
        """
        try:
            # Handle nested structure
            gauge_data = gauge.get('FloodGauge', gauge)
            
            # Extract header information
            header = gauge_data.get('Header', {})
            gauge_id = header.get('GaugeID', 'Unknown')
            
            # Extract sensor details
            sensor_details = gauge_data.get('SensorDetails', {})
            gauge_info = sensor_details.get('GaugeInformation', {})
            measurements = sensor_details.get('Measurements', {})
            
            # Extract coordinates
            lat = gauge_info.get('GaugeLatitude')
            lon = gauge_info.get('GaugeLongitude')
            
            if lat is None or lon is None:
                print(f"Warning: Invalid coordinates for gauge {gauge_id}")
                return None
            
            # Extract operational information
            gauge_owner = gauge_info.get('GaugeOwner', 'Unknown')
            gauge_type = gauge_info.get('GaugeType', 'Unknown')
            operational_status = gauge_info.get('OperationalStatus', 'Unknown')
            data_source = gauge_info.get('DataSourceType', 'Unknown')
            installation_date = gauge_info.get('InstallationDate', 'Unknown')
            certification_status = gauge_info.get('CertificationStatus', 'Unknown')
            
            # Extract measurement information
            measurement_frequency = measurements.get('MeasurementFrequency', 'Unknown')
            measurement_method = measurements.get('MeasurementMethod', 'Unknown')
            data_transmission = measurements.get('DataTransmission', 'Unknown')
            
            # Extract statistical data
            sensor_stats = gauge_data.get('SensorStats', {})
            
            # Extract flood stage information
            flood_stage = gauge_data.get('FloodStage', {}).get('UK', {})
            
            extracted_info = {
                'gauge_id': gauge_id,
                'coordinates': {'latitude': lat, 'longitude': lon},
                'gauge_owner': gauge_owner,
                'gauge_type': gauge_type,
                'operational_status': operational_status,
                'data_source': data_source,
                'installation_date': installation_date,
                'certification_status': certification_status,
                'measurement_frequency': measurement_frequency,
                'measurement_method': measurement_method,
                'data_transmission': data_transmission,
                'sensor_stats': sensor_stats,
                'flood_stage': flood_stage,
                # Keep original nested structure for detailed popups
                'original_data': gauge_data
            }
            
            return extracted_info
            
        except Exception as e:
            print(f"Error extracting gauge info: {str(e)}")
            return None
    
    @classmethod
    def extract_flood_risk_data(cls, flood_risk_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract flood risk information from flood risk report.
        
        Args:
            flood_risk_report: Complete flood risk report
            
        Returns:
            Dictionary with gauge, property, and mortgage risk data
        """
        result = {
            'gauge_flood_info': {},
            'property_flood_info': {},
            'mortgage_risk_info': {'by_mortgage_id': {}, 'by_property_id': {}}
        }
        
        try:
            # Extract gauge flood information
            gauge_data = flood_risk_report.get("gauge_data", {})
            for gauge_id, gauge_info in gauge_data.items():
                result['gauge_flood_info'][gauge_id] = {
                    "gauge_name": gauge_info.get("gauge_name"),
                    "elevation": gauge_info.get("elevation"),
                    "max_level": gauge_info.get("max_level"),
                    "alert_level": gauge_info.get("alert_level"),
                    "warning_level": gauge_info.get("warning_level"), 
                    "severe_level": gauge_info.get("severe_level"),
                    "max_gauge_reading": gauge_info.get("max_gauge_reading")
                }
            
            # Extract property flood information
            property_risk = flood_risk_report.get("property_risk", {})
            for prop_id, prop_data in property_risk.items():
                result['property_flood_info'][prop_id] = {
                    "property_id": prop_data.get("property_id"),
                    "property_elevation": prop_data.get("property_elevation"),
                    "nearest_gauge": prop_data.get("nearest_gauge"),
                    "nearest_gauge_id": prop_data.get("nearest_gauge_id"),
                    "distance_to_gauge": prop_data.get("distance_to_gauge"),
                    "gauge_elevation": prop_data.get("gauge_elevation"),
                    "water_level": prop_data.get("water_level"),
                    "severe_level": prop_data.get("severe_level"),
                    "gauge_flood_depth": prop_data.get("gauge_flood_depth"),
                    "elevation_diff": prop_data.get("elevation_diff"),
                    "flood_depth": prop_data.get("flood_depth"),
                    "risk_value": prop_data.get("risk_value"),
                    "risk_level": prop_data.get("risk_level"),
                    "property_value": prop_data.get("property_value"),
                    "value_at_risk": prop_data.get("value_at_risk")
                }
            
            # Extract mortgage risk information
            mortgage_risk_data = flood_risk_report.get("mortgage_risk", {})
            for mortgage_id, risk_info in mortgage_risk_data.items():
                # Add to mortgage ID lookup
                result['mortgage_risk_info']['by_mortgage_id'][mortgage_id] = risk_info
                
                # Add to property ID lookup if property ID exists
                property_id = risk_info.get("PropertyID")
                if property_id:
                    result['mortgage_risk_info']['by_property_id'][property_id] = risk_info
            
            print(f"Extracted flood risk data: {len(result['gauge_flood_info'])} gauges, "
                  f"{len(result['property_flood_info'])} properties, "
                  f"{len(result['mortgage_risk_info']['by_mortgage_id'])} mortgages")
                  
        except Exception as e:
            print(f"Error extracting flood risk data: {str(e)}")
        
        return result
    
    @classmethod
    def extract_id_from_tooltip(cls, tooltip_text: str, id_type: str = 'property') -> Optional[str]:
        """
        Extract property or gauge ID from tooltip text.
        
        Args:
            tooltip_text: Tooltip text content
            id_type: Type of ID to extract ('property' or 'gauge')
            
        Returns:
            Extracted ID or None if not found
        """
        if not tooltip_text:
            return None
        
        if id_type == 'property':
            # Look for "Property: XXXXX" pattern
            match = re.search(r'Property:\s*([^|]+)', tooltip_text)
            if match:
                return match.group(1).strip()
        
        elif id_type == 'gauge':
            # Look for "Gauge: XXXXX" or "GAUGE-XXXXX" pattern
            match = re.search(r'Gauge:\s*([^|]+)', tooltip_text)
            if match:
                return match.group(1).strip()
            
            # Alternative pattern for direct gauge ID
            match = re.search(r'GAUGE-[a-f0-9]+', tooltip_text)
            if match:
                return match.group(0).strip()
        
        return None
    
    @classmethod
    def extract_id_from_popup(cls, popup_content: str, id_type: str = 'property') -> Optional[str]:
        """
        Extract property or gauge ID from popup content.
        
        Args:
            popup_content: Popup HTML content
            id_type: Type of ID to extract ('property' or 'gauge')
            
        Returns:
            Extracted ID or None if not found
        """
        if not popup_content:
            return None
        
        # Convert to string if needed
        content_string = str(popup_content)
        
        if id_type == 'property':
            # Look for "ID: XXXXX" pattern in the popup HTML
            match = re.search(r'ID:\s*([^<\r\n]+)', content_string)
            if match:
                return match.group(1).strip()
        
        elif id_type == 'gauge':
            # Look for "ID: GAUGE-XXXXX" pattern
            match = re.search(r'ID:\s*(GAUGE-[a-f0-9]+)', content_string)
            if match:
                return match.group(1).strip()
            
            # Alternative: Look for just "GAUGE-XXXXX" pattern
            match = re.search(r'GAUGE-[a-f0-9]+', content_string)
            if match:
                return match.group(0).strip()
        
        return None
    
    @classmethod
    def build_mortgage_lookup(cls, mortgage_data: Union[Dict, List]) -> Dict[str, Dict]:
        """
        Build a lookup dictionary of mortgages by property ID.
        
        Args:
            mortgage_data: Dictionary or list of mortgage data
            
        Returns:
            Dictionary mapping property IDs to mortgage information
        """
        lookup = {}
        
        print(f"Building mortgage lookup from data of type: {type(mortgage_data)}")
        
        # Handle different possible formats of mortgage data
        mortgages = cls._normalize_mortgage_list(mortgage_data)
        
        if isinstance(mortgages, list):
            for mortgage in mortgages:
                try:
                    mortgage_info = cls.extract_mortgage_info(mortgage)
                    if mortgage_info and mortgage_info.get('property_id'):
                        lookup[mortgage_info['property_id']] = mortgage_info
                except Exception as e:
                    print(f"Error processing mortgage: {e}")
        
        print(f"Built mortgage lookup with {len(lookup)} entries")
        return lookup
    
    @classmethod
    def _extract_property_value(cls, prop: Dict[str, Any]) -> Any:
        """Extract property value from various possible locations in the data."""
        # Try multiple paths for property value
        value_paths = [
            ['PropertyValue'],
            ['PropertyHeader', 'Valuation', 'PropertyValue'],
            ['Valuation', 'PropertyValue'],
            ['PropertyHeader', 'PropertyValue']
        ]
        
        for path in value_paths:
            current = prop
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break
            
            if current is not None and current != 'Unknown':
                return current
        
        return 'Unknown'
    
    @classmethod
    def _extract_term_years(cls, financial_terms: Dict[str, Any]) -> Optional[float]:
        """Extract term years from financial terms, trying multiple field names."""
        term_fields = ['TermYears', 'Term', 'LoanTerm', 'OriginalTerm']
        
        for field in term_fields:
            if field in financial_terms:
                term_years = financial_terms.get(field)
                if term_years is not None:
                    # If term is in months, convert to years
                    if field == 'OriginalTerm' and term_years > 100:
                        return term_years / 12
                    return term_years
        
        return None
    
    @classmethod
    def _calculate_age_factor(cls, construction_year: Union[int, str]) -> str:
        """Calculate property age factor."""
        if construction_year and construction_year != 'Unknown':
            try:
                year = int(construction_year)
                current_year = datetime.now().year
                age = current_year - year
                
                if age > 100:
                    return f"High Risk (Pre-{current_year - 100})"
                elif age > 50:
                    return f"Medium Risk ({current_year - 100}-{current_year - 50})"
                else:
                    return f"Low Risk (Post-{current_year - 50})"
            except (ValueError, TypeError):
                pass
        
        return "Unknown"
    
    @classmethod
    def _normalize_mortgage_list(cls, mortgage_data: Union[Dict, List]) -> List:
        """Normalize mortgage data to a list format."""
        if isinstance(mortgage_data, dict):
            if 'mortgages' in mortgage_data:
                return mortgage_data['mortgages']
            elif 'Mortgages' in mortgage_data:
                return mortgage_data['Mortgages']
            elif 'mortgage_portfolio' in mortgage_data:
                return mortgage_data['mortgage_portfolio']
            else:
                # Assume it's a single mortgage wrapped in dict
                return [mortgage_data]
        elif isinstance(mortgage_data, list):
            return mortgage_data
        else:
            print(f"Warning: Unexpected mortgage data type: {type(mortgage_data)}")
            return []


# Convenience functions for backward compatibility
def extract_property_info(prop: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract property information (backward compatibility)."""
    return DataExtractor.extract_property_info(prop)

def build_mortgage_lookup(mortgage_data: Union[Dict, List]) -> Dict[str, Dict]:
    """Build mortgage lookup (backward compatibility)."""
    return DataExtractor.build_mortgage_lookup(mortgage_data)

# Add these to your existing files:

# ==== ADD TO src/visualization/utils/data_extractors.py ====
# Add this class at the end of your data_extractors.py file:

class PropertyDataExtractor(DataExtractor):
    """
    Specialized extractor for property data.
    
    This class provides a more specific interface for property data extraction
    while maintaining compatibility with the test expectations.
    """
    
    def extract_property_info(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract property information from property data.
        
        Args:
            property_data: Raw property data dictionary
            
        Returns:
            Extracted property information or None if extraction fails
        """
        return super().extract_property_info(property_data)
    
    def extract_coordinates(self, property_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Extract just the coordinates from property data.
        
        Args:
            property_data: Raw property data dictionary
            
        Returns:
            Dictionary with latitude and longitude or None
        """
        info = self.extract_property_info(property_data)
        if info and 'coordinates' in info:
            return info['coordinates']
        return None
    
    def extract_address(self, property_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract address information from property data.
        
        Args:
            property_data: Raw property data dictionary
            
        Returns:
            Dictionary with address components or None
        """
        info = self.extract_property_info(property_data)
        if info and 'address' in info:
            return info['address']
        return None


# ==== ADD TO src/visualization/utils/risk_assessors.py ====
# Add this method to your existing RiskAssessor class:

    @classmethod
    def get_risk_color(cls, risk_level: str) -> str:
        """
        Get color code for flood risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Color string for visualization
        """
        risk_colors = {
            'Very Low': 'green',
            'Very low': 'green',
            'Low': 'lightgreen',
            'Medium': 'orange',
            'High': 'red',
            'Very High': 'darkred',
            'Very high': 'darkred',
            'Unknown': 'blue',
            'N/A': 'gray'
        }
        return risk_colors.get(risk_level, 'blue')  # Default blue
    
    @classmethod
    def get_risk_icon(cls, risk_level: str) -> str:
        """
        Get icon name for flood risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Icon name string
        """
        risk_icons = {
            'Very Low': 'check-circle',
            'Very low': 'check-circle',
            'Low': 'info-circle',
            'Medium': 'exclamation-triangle',
            'High': 'exclamation-circle',
            'Very High': 'times-circle',
            'Very high': 'times-circle',
            'Unknown': 'question-circle'
        }
        return risk_icons.get(risk_level, 'question-circle')
    
    @classmethod
    def get_ltv_color(cls, ltv_ratio: float) -> str:
        """
        Get color code for LTV ratio.
        
        Args:
            ltv_ratio: LTV ratio (0-1 or 0-100)
            
        Returns:
            Color string for visualization
        """
        if ltv_ratio is None:
            return 'gray'
        
        # Normalize to 0-1 if needed
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100
        
        if ltv_ratio <= 0.6:
            return 'green'
        elif ltv_ratio <= 0.8:
            return 'yellow'
        elif ltv_ratio <= 0.95:
            return 'orange'
        else:
            return 'red'
