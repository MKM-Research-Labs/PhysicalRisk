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

"""Shared helpers for CDM-to-JSON mapping validation tests."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class MappingSummary:
    """Summary of all mapping test results."""
    total_cdm_fields: int = 0
    total_json_fields: int = 0
    fields_present: int = 0
    fields_missing: int = 0
    fields_type_valid: int = 0
    fields_type_invalid: int = 0
    fields_value_valid: int = 0
    fields_value_invalid: int = 0
    extra_json_fields: int = 0
    missing_fields: List[str] = field(default_factory=list)
    extra_fields: List[str] = field(default_factory=list)


class CDMSchemaExtractor:
    """Extracts all leaf fields from a CDM schema with their paths and types."""

    def __init__(self, schema: Dict):
        self.schema = schema
        self.fields: Dict[str, Dict] = {}

    def extract_all_fields(self) -> Dict[str, Dict]:
        self.fields = {}
        self._extract_recursive(self.schema, "")
        return self.fields

    def _extract_recursive(self, node: Dict, path: str):
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key in ("type", "options", "description", "values"):
                continue
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                if "type" in value:
                    self.fields[current_path] = {
                        "name": key,
                        "type": value.get("type"),
                        "options": value.get("options"),
                        "description": value.get("description", ""),
                    }
                else:
                    self._extract_recursive(value, current_path)


class JSONDataExtractor:
    """Extracts all leaf fields from generated JSON data as dot-separated paths."""

    def __init__(self, json_data: Dict):
        self.json_data = json_data
        self.fields: Dict[str, Any] = {}

    def extract_all_fields(self) -> Dict[str, Any]:
        self.fields = {}
        self._extract_recursive(self.json_data, "")
        return self.fields

    def _extract_recursive(self, node: Any, path: str):
        if isinstance(node, dict):
            for key, value in node.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, dict):
                    self._extract_recursive(value, current_path)
                else:
                    self.fields[current_path] = value


class FieldValidator:
    """Validates field values against CDM type definitions."""

    @staticmethod
    def validate_type(value: Any, cdm_type: str) -> Tuple[bool, str]:
        if value is None:
            return True, ""
        if cdm_type == "text":
            return (True, "") if isinstance(value, str) else (False, f"Expected string, got {type(value).__name__}")
        elif cdm_type == "decimal":
            return (True, "") if isinstance(value, (int, float)) else (False, f"Expected number, got {type(value).__name__}")
        elif cdm_type == "integer":
            if isinstance(value, bool):
                return False, f"Expected integer, got bool"
            if isinstance(value, int):
                return True, ""
            if isinstance(value, float) and value.is_integer():
                return True, ""
            return False, f"Expected integer, got {type(value).__name__}"
        elif cdm_type == "date":
            if isinstance(value, str):
                try:
                    if "T" in value:
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                    else:
                        datetime.strptime(value, "%Y-%m-%d")
                    return True, ""
                except ValueError:
                    return False, f"Invalid date format: {value}"
            return False, f"Expected date string, got {type(value).__name__}"
        elif cdm_type == "menu":
            return (True, "") if isinstance(value, str) else (False, f"Expected string for menu, got {type(value).__name__}")
        elif cdm_type == "boolean":
            return (True, "") if isinstance(value, bool) else (False, f"Expected boolean, got {type(value).__name__}")
        return True, ""

    @staticmethod
    def validate_menu_value(value: Any, options: List[str]) -> Tuple[bool, str]:
        if value is None or not options:
            return True, ""
        if value not in options:
            return False, f"Value '{value}' not in options: {options}"
        return True, ""

    @staticmethod
    def validate_decimal_range(value: Any, field_name: str) -> Tuple[bool, str]:
        if value is None or not isinstance(value, (int, float)):
            return True, ""
        ranges = {
            "GaugeLatitude": (-90, 90), "GaugeLongitude": (-180, 180),
            "GroundLevelMeters": (-500, 9000), "elevation": (-500, 9000),
            "HistoricalHighLevel": (0, 50), "FloodAlert": (0, 50),
            "FloodWarning": (0, 50), "SevereFloodWarning": (0, 50),
        }
        if field_name in ranges:
            lo, hi = ranges[field_name]
            if value < lo or value > hi:
                return False, f"Value {value} outside expected range [{lo}, {hi}]"
        return True, ""


class CDMMappingTest:
    """Generic CDM-to-JSON mapping validator."""

    def __init__(self, label: str, cdm_schema: Dict, json_data: Dict,
                 skip_fields: Optional[Set[str]] = None, verbose: bool = True):
        self.label = label
        self.cdm_schema = cdm_schema
        self.json_data = json_data
        self.skip_fields = skip_fields or set()
        self.verbose = verbose
        self.summary = MappingSummary()

    def run_all_tests(self) -> MappingSummary:
        cdm_fields = CDMSchemaExtractor(self.cdm_schema).extract_all_fields()
        json_fields = JSONDataExtractor(self.json_data).extract_all_fields()
        self.summary.total_cdm_fields = len(cdm_fields)
        self.summary.total_json_fields = len(json_fields)
        self._test_cdm_coverage(cdm_fields, json_fields)
        self._test_extra_fields(cdm_fields, json_fields)
        self._test_types(cdm_fields, json_fields)
        self._test_values(cdm_fields, json_fields)
        return self.summary

    def _find_json_value(self, cdm_path: str, json_fields: Dict[str, Any]) -> Tuple[bool, Any]:
        if cdm_path in json_fields:
            return True, json_fields[cdm_path]
        parts = cdm_path.split(".")
        if len(parts) > 1:
            shortened = ".".join(parts[1:])
            if shortened in json_fields:
                return True, json_fields[shortened]
        field_name = parts[-1]
        for json_path, value in json_fields.items():
            if json_path.endswith(f".{field_name}") or json_path == field_name:
                return True, value
        return False, None

    def _test_cdm_coverage(self, cdm_fields: Dict, json_fields: Dict):
        for cdm_path, field_def in cdm_fields.items():
            if field_def["name"] in self.skip_fields or cdm_path in self.skip_fields:
                continue
            found, _ = self._find_json_value(cdm_path, json_fields)
            if found:
                self.summary.fields_present += 1
            else:
                self.summary.fields_missing += 1
                self.summary.missing_fields.append(cdm_path)

    def _test_extra_fields(self, cdm_fields: Dict, json_fields: Dict):
        cdm_field_names: Set[str] = set()
        for path in cdm_fields:
            parts = path.split(".")
            cdm_field_names.add(parts[-1])
            cdm_field_names.add(path)
        for json_path in json_fields:
            field_name = json_path.split(".")[-1]
            if field_name in cdm_field_names or json_path in cdm_field_names:
                continue
            if field_name in self.skip_fields:
                continue
            self.summary.extra_json_fields += 1
            self.summary.extra_fields.append(json_path)

    def _test_types(self, cdm_fields: Dict, json_fields: Dict):
        for cdm_path, field_def in cdm_fields.items():
            found, value = self._find_json_value(cdm_path, json_fields)
            if not found:
                continue
            is_valid, _ = FieldValidator.validate_type(value, field_def["type"])
            if is_valid:
                self.summary.fields_type_valid += 1
            else:
                self.summary.fields_type_invalid += 1

    def _test_values(self, cdm_fields: Dict, json_fields: Dict):
        for cdm_path, field_def in cdm_fields.items():
            found, value = self._find_json_value(cdm_path, json_fields)
            if not found or value is None:
                continue
            cdm_type = field_def["type"]
            is_valid = True
            if cdm_type == "menu" and field_def.get("options"):
                is_valid, _ = FieldValidator.validate_menu_value(value, field_def["options"])
            elif cdm_type == "decimal":
                is_valid, _ = FieldValidator.validate_decimal_range(value, field_def["name"])
            if is_valid:
                self.summary.fields_value_valid += 1
            else:
                self.summary.fields_value_invalid += 1


def run_cdm_mapping_test(cdm_instance, json_path: Path, data_key: str,
                          skip_fields: Optional[Set[str]] = None) -> MappingSummary:
    """Generic helper to load JSON and run a CDM mapping test."""
    with open(json_path) as f:
        data = json.load(f)
    records = data.get(data_key, [])
    if not records:
        raise ValueError(f"No records found under key '{data_key}' in {json_path}")
    label = type(cdm_instance).__name__
    test = CDMMappingTest(label, cdm_instance.schema, records[0],
                          skip_fields=skip_fields, verbose=False)
    return test.run_all_tests()
