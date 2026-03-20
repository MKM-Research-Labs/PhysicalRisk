# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Property building mixin for PropertyPortfolioGenerator."""

from typing import Dict

from config import config


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

        return property_data, property_id

    def _build_section(self, section_schema: Dict, index: int, metadata: Dict) -> Dict:
        """Recursively build a section of property data based on the schema."""
        result = {}

        if not isinstance(section_schema, dict):
            return {}

        for field_name, field_def in section_schema.items():
            if field_name in ['type', 'options', 'description', 'values']:
                continue

            if isinstance(field_def, dict) and not field_def.get("type"):
                result[field_name] = self._build_section(field_def, index, metadata)
            else:
                value = self.random.generate_field_value(field_name, field_def, index, metadata)
                if value is not None:
                    result[field_name] = value

        return result

    def _set_specific_property_values(self, property_data: Dict, property_id: str,
                                      index: int, metadata: Dict, location: Dict):
        """Set specific property values that need to be consistent across sections."""
        if 'PropertyHeader' not in property_data:
            property_data['PropertyHeader'] = {}

        header = property_data['PropertyHeader']

        # Attributes section
        if 'PropertyAttributes' not in header:
            header['PropertyAttributes'] = {}

        attrs = header['PropertyAttributes']
        attrs['PropertyID'] = property_id
        attrs['CatchmentID'] = config.CATCHMENT

        # Also set PropertyID in Header for consumers that look there
        if 'Header' not in header:
            header['Header'] = {}
        header['Header']['PropertyID'] = property_id

        # Location section
        if 'Location' not in header:
            header['Location'] = {}

        loc = header['Location']
        loc['LatitudeDegrees'] = location['lat']
        loc['LongitudeDegrees'] = location['lon']
        if 'elevation' in location:
            if 'RiskAssessment' not in loc:
                loc['RiskAssessment'] = {}
            loc['RiskAssessment']['GroundLevelMeters'] = round(location['elevation'], 2)

        # Store reference gauge IDs (the 3 gauges this property is placed relative to)
        ref_indices = location.get('reference_gauge_indices', [])
        if ref_indices:
            gauge_id_map = getattr(self, '_gauge_id_map', {})
            header['ReferenceGauges'] = [
                gauge_id_map.get(idx, f"GAUGE-{idx + 1:03d}") for idx in ref_indices
            ]
