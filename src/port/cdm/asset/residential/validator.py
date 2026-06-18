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

"""
Residential asset CDM validation logic.

Provides validate() and get_required_fields() as module-level functions so they
can be used standalone or delegated to by ResidentialAssetCDM.
"""

from typing import Dict, List


def validate(property_data: dict) -> Dict[str, List[str]]:
    """
    Validate property data against the residential asset CDM schema.

    Args:
        property_data: Property data to validate.

    Returns:
        Dictionary of validation errors keyed by section name.
        Empty dict means the record is valid.
    """
    errors: Dict[str, List[str]] = {}

    try:
        header = property_data.get("PropertyHeader", {}).get("Header", {})
        header_errors: List[str] = []

        if not header.get("PropertyID"):
            header_errors.append("Missing required field: PropertyID")
        if not header.get("CatchmentID"):
            header_errors.append("Missing recommended field: CatchmentID")

        if header_errors:
            errors["Header"] = header_errors

        location = property_data.get("PropertyHeader", {}).get("Location", {})
        location_errors: List[str] = []

        if not location.get("LatitudeDegrees"):
            location_errors.append("Missing required field: LatitudeDegrees")
        if not location.get("LongitudeDegrees"):
            location_errors.append("Missing required field: LongitudeDegrees")

        if location_errors:
            errors["Location"] = location_errors

        return errors

    except Exception as exc:
        return {"validation_error": [str(exc)]}


def get_required_fields() -> List[str]:
    """Return the list of dotted-path required field names."""
    return [
        "PropertyHeader.Header.PropertyID",
        "PropertyHeader.Header.CatchmentID",
        "PropertyHeader.Location.LatitudeDegrees",
        "PropertyHeader.Location.LongitudeDegrees",
    ]
