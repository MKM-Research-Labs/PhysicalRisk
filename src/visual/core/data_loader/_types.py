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

"""Data containers for the visualization data loader."""

from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Optional


@dataclass
class LoadedData:
    """Container for all loaded visualization data."""
    gauge_data: Optional[Dict[str, Any]] = None
    property_data: Optional[Dict[str, Any]] = None
    rloan_data: Optional[Dict[str, Any]] = None
    commercial_data: Optional[Dict[str, Any]] = None
    commercial_loan_data: Optional[Dict[str, Any]] = None
    hazard_data: Optional[Dict[str, Any]] = None
    property_hazard_data: Optional[Dict[str, Any]] = None
    storm_data: Optional[Dict[str, Any]] = None
    counterparty_data: Optional[Dict[str, Any]] = None

    # Directory-based data counts
    gaugets_count: int = 0
    gaugehd_count: int = 0
    propertyts_count: int = 0

    # Processed lookups
    rloan_lookup: Optional[Dict[str, Dict]] = None
    commercial_loan_lookup: Optional[Dict[str, Dict]] = None
    gauge_flood_info: Optional[Dict[str, Dict]] = None
    property_flood_info: Optional[Dict[str, Dict]] = None


class DataValidationResult(NamedTuple):
    """Result of data validation."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    summary: Dict[str, Any]
