"""Coverage expansion tests for property_random.py — missing lines.

Lines: 148-149 (generator exception fallback), 157 (string with options),
       160 (number fallback), 162 (integer fallback)
"""

from unittest.mock import patch

import pytest

from port.rand.thames.property.property_random import generate_field_value


@pytest.fixture
def metadata():
    """Minimal property metadata dict."""
    return {
        "property_type": "Flat",
        "property_area": 70.0,
        "property_value": 400000,
        "construction_year": 2000,
        "elevation": 7.5,
        "area_name": "Chelsea",
        "value_factor": 1.2,
        "streets_data": {},
    }


class TestGeneratorExceptionFallback:
    """Lines 148-149: when a registered generator raises, falls back to type-based."""

    def test_generator_exception_falls_through_to_type(self, metadata):
        # PropertyValue is a registered generator. If it raises, should fallback.
        field_def = {"type": "number"}
        with patch(
            "port.rand.thames.property.property_random.generators._value.get_field_generators",
            return_value={"PropertyValue": lambda _: (_ for _ in ()).throw(ValueError("boom"))},
        ):
            result = generate_field_value("PropertyValue", field_def, 0, metadata)
        # Falls back to number type: round(random.uniform(0, 1000), 2)
        assert isinstance(result, float)
        assert 0 <= result <= 1000


class TestStringWithOptions:
    """Line 157: string field_type with options list picks from options."""

    def test_string_with_options_picks_from_list(self, metadata):
        field_def = {"type": "string", "options": ["Brick", "Stone", "Timber"]}
        result = generate_field_value("UnknownStringField", field_def, 0, metadata)
        assert result in ["Brick", "Stone", "Timber"]

    def test_string_without_options_returns_empty(self, metadata):
        field_def = {"type": "string"}
        result = generate_field_value("UnknownStringField", field_def, 0, metadata)
        assert result == ""


class TestNumberFallback:
    """Line 160: unknown number field returns random float."""

    def test_number_type_returns_float(self, metadata):
        field_def = {"type": "number"}
        result = generate_field_value("UnknownNumField", field_def, 0, metadata)
        assert isinstance(result, float)
        assert 0 <= result <= 1000


class TestIntegerFallback:
    """Line 162: unknown integer field returns random int."""

    def test_integer_type_returns_int(self, metadata):
        field_def = {"type": "integer"}
        result = generate_field_value("UnknownIntField", field_def, 0, metadata)
        assert isinstance(result, int)
        assert 0 <= result <= 100


class TestEaZoneFallback:
    """_ea_zone_from_elevation: a below-river property is Zone 3b."""

    def test_negative_offset_is_zone_3b(self):
        """A negative vertical_offset (below river level) classifies as Zone 3b
        (functional floodplain), whose lower bound is unbounded."""
        from port.rand.thames.property.property_random.helpers import _ea_zone_from_elevation
        result = _ea_zone_from_elevation({"vertical_offset": -1.0})
        assert result == "Zone 3b"
