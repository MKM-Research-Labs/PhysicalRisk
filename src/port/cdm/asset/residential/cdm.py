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

"""ResidentialAssetCDM — CDM implementation for residential asset (property) data."""

from typing import Dict, List

from ...base import BaseCDM
from .mapping import create_mapping
from .schema import DEFAULT_ELEVATION, PROPERTY_SCHEMA
from .validator import get_required_fields, validate


class ResidentialAssetCDM(BaseCDM):
    """
    Residential Asset Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for residential property data with comprehensive attributes.

    Sub-module responsibilities
    ---------------------------
    schema.py    — canonical PROPERTY_SCHEMA dict and DEFAULT_ELEVATION
    validator.py — validate() and get_required_fields()
    mapping/     — create_mapping() (nested CDM -> flat snake_case dict)
    bri.py       — apply_bri_rating() resilience-checklist aggregator
    """

    DEFAULT_ELEVATION = DEFAULT_ELEVATION

    def __init__(self):
        """Initialize the Residential Asset CDM with schema definition."""
        self._schema = PROPERTY_SCHEMA

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, property_data: dict) -> Dict[str, List[str]]:
        """
        Validate property data against the CDM schema.

        Args:
            property_data: Property data to validate.

        Returns:
            Dictionary of validation errors by section.  Empty = valid.
        """
        return validate(property_data)

    def create_mapping(self, prop: dict) -> dict:
        """
        Flatten a nested CDM record into a snake_case dict.

        Args:
            prop: Nested property data in CDM format.

        Returns:
            Flat dict with snake_case keys; None values are omitted.
        """
        return create_mapping(prop, default_elevation=self.DEFAULT_ELEVATION)

    def get_required_fields(self) -> List[str]:
        """Return list of dotted-path required field names."""
        return get_required_fields()
