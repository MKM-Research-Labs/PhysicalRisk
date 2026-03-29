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

#
# This software is provided under license by MKM Research Labs.
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
Common Data Model (CDM) definitions.

This package contains standardized data models for all entity types
used in the PRS platform. Each CDM provides schema definitions,
validation methods, and data transformation utilities.

All CDMs include CatchmentID for multi-catchment support.

Usage:
    from port.cdm import PropertyCDM, FloodGaugeCDM, MortgageCDM

    # Validate property data
    cdm = PropertyCDM()
    errors = cdm.validate(property_data)

    # Create flat mapping from nested CDM structure
    flat_data = cdm.create_mapping(nested_data)
"""

from .base import BaseCDM
from .ctpy import CounterpartyCDM
from .gauge import FloodGaugeCDM
from .mortgage import MortgageCDM
from .property import PropertyCDM
from .prs import PhysicalRiskSwapCDM
from .storm import StormEventCDM, TCEventCDM
from .stormts import StormTimeSeriesCDM, TCEventTSCDM

__all__ = [
    # Base class
    'BaseCDM',

    # Entity CDMs
    'FloodGaugeCDM',
    'PropertyCDM',
    'MortgageCDM',
    'StormEventCDM',
    'StormTimeSeriesCDM',
    'PhysicalRiskSwapCDM',
    'CounterpartyCDM',

    # Backwards compatibility aliases
    'TCEventCDM',
    'TCEventTSCDM'
]
