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
Data loaders package for the PRS Platform.

This package provides modular data loading capabilities for various
data types including gauges, properties, mortgages, and storm data.

Data files are loaded from catchment-specific directories by default
(e.g., input/thames/, input/rhine/) based on config.CATCHMENT setting.

Usage:
    from loaders import LoaderRegistry

    # Create registry (uses config.get_catchment_input_dir() by default)
    registry = LoaderRegistry()

    # Get loaders
    properties = registry.get_property_loader()
    gauges = registry.get_gauge_loader()
"""

# Base classes
from .base_loader import BaseLoader

# Individual loaders
from .gauge_loader import GaugeLoader
from .loader_registry import LoaderRegistry, create_registry

# Lookup builders
from .lookups import (
    analyze_id_relationships,
    build_all_lookups,
    build_gauge_flood_info,
    build_rloan_lookup,
    build_property_flood_info,
    extract_gauge_ids,
    extract_rloan_ids,
    extract_rloan_property_ids,
    extract_property_ids,
)
from .rloan_loader import RLoanLoader
from .property_loader import PropertyLoader
from .storm_loader import StormLoader
from .timeseries_loader import TimeseriesLoader

__all__ = [
    # Base classes
    "BaseLoader",
    "LoaderRegistry",
    "create_registry",

    # Loaders
    "GaugeLoader",
    "PropertyLoader",
    "RLoanLoader",
    "StormLoader",
    "TimeseriesLoader",

    # Lookup builders
    "build_rloan_lookup",
    "build_gauge_flood_info",
    "build_property_flood_info",
    "build_all_lookups",
    "extract_property_ids",
    "extract_rloan_ids",
    "extract_rloan_property_ids",
    "extract_gauge_ids",
    "analyze_id_relationships",
]
