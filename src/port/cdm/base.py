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

"""
Base Common Data Model (CDM) abstract class.

All CDM implementations inherit from this base class to ensure
consistent interface across entity types.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseCDM(ABC):
    """
    Abstract base class for all Common Data Models.

    Each CDM provides:
    - schema: The field definitions and structure
    - validate(): Validation against the schema
    - create_mapping(): Transform nested CDM to flat dictionary
    """

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """
        Return the CDM schema definition.

        The schema is a nested dictionary defining all fields,
        their types, descriptions, and valid options for menu fields.

        Returns:
            Schema dictionary
        """
        pass

    @abstractmethod
    def validate(self, data: dict) -> Dict[str, List[str]]:
        """
        Validate data against the CDM schema.

        Args:
            data: Data dictionary to validate

        Returns:
            Dictionary of validation errors by section.
            Empty dict means validation passed.
        """
        pass

    @abstractmethod
    def create_mapping(self, raw_data: dict) -> dict:
        """
        Create a flat dictionary mapping from nested CDM structure.

        Transforms the nested CDM format into a flat key-value
        dictionary suitable for DataFrame operations.

        Args:
            raw_data: Nested CDM-structured data

        Returns:
            Flat dictionary with snake_case keys
        """
        pass

    def get_field_info(self, field_path: str) -> Optional[dict]:
        """
        Get information about a specific field in the schema.

        Args:
            field_path: Dot-separated path to field (e.g., 'Header.GaugeID')

        Returns:
            Field definition dict or None if not found
        """
        path_parts = field_path.split('.')
        current = self.schema

        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current if isinstance(current, dict) else None

    def list_all_fields(self) -> List[str]:
        """
        Get a list of all field paths in the schema.

        Returns:
            List of dot-separated field paths
        """
        def extract_paths(obj: dict, prefix: str = "") -> List[str]:
            paths = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Skip schema metadata keys
                    if key in ['type', 'options', 'values', 'description', 'items']:
                        continue
                    current_path = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict) and 'type' in value:
                        # This is a field definition
                        paths.append(current_path)
                    else:
                        # This is a nested section
                        paths.extend(extract_paths(value, current_path))
            return paths

        return extract_paths(self.schema)

    def get_required_fields(self) -> List[str]:
        """
        Get list of required field paths.

        Override in subclass to specify required fields.

        Returns:
            List of required field paths
        """
        return []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
