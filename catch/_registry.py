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
Catchment package for river catchment definitions.

This package provides access to 20 river catchments across Europe and North America,
each with gauge points, elevation data, and area definitions. Catchments have a 1:1
relationship with portfolios, gauges, storm timeseries, and maps.

Usage:
    from catchments import get_catchment
    
    catchment = get_catchment('thames')
    elevation = catchment.get_elevation(51.5, -0.1)
    gaugepoints = catchment.GAUGEPOINTS
"""

from typing import Dict, List, Any, Optional, Type

from .base import BaseCatchment

# Europe catchments
from .thames import ThamesCatchment
from .rhine import RhineCatchment
from .danube import DanubeCatchment
from .seine import SeineCatchment
from .po import PoCatchment
from .elbe import ElbeCatchment
from .meuse import MeuseCatchment
from .rhinedelta import RhineDeltaCatchment
from .loire import LoireCatchment
from .ebro import EbroCatchment

# North America catchments
from .mississippi import MississippiCatchment
from .hudson import HudsonCatchment
from .stlawrence import StLawrenceCatchment
from .delaware import DelawareCatchment
from .sacramento import SacramentoCatchment
from .connecticut import ConnecticutCatchment
from .susquehanna import SusquehannaCatchment
from .columbia import ColumbiaCatchment
from .fraser import FraserCatchment
from .riogrande import RioGrandeCatchment


# Registry of all available catchments (20 total)
CATCHMENTS: Dict[str, Type[BaseCatchment]] = {
    # Europe (10)
    'thames': ThamesCatchment,
    'rhine': RhineCatchment,
    'danube': DanubeCatchment,
    'seine': SeineCatchment,
    'po': PoCatchment,
    'elbe': ElbeCatchment,
    'meuse': MeuseCatchment,
    'rhinedelta': RhineDeltaCatchment,
    'loire': LoireCatchment,
    'ebro': EbroCatchment,
    # North America (10)
    'mississippi': MississippiCatchment,
    'hudson': HudsonCatchment,
    'stlawrence': StLawrenceCatchment,
    'delaware': DelawareCatchment,
    'sacramento': SacramentoCatchment,
    'connecticut': ConnecticutCatchment,
    'susquehanna': SusquehannaCatchment,
    'columbia': ColumbiaCatchment,
    'fraser': FraserCatchment,
    'riogrande': RioGrandeCatchment,
}

# Cache for instantiated catchments
_catchment_instances: Dict[str, BaseCatchment] = {}


def get_catchment(name: str) -> BaseCatchment:
    """
    Get a catchment instance by name.
    
    Args:
        name: Catchment identifier (e.g., 'thames', 'rhine')
        
    Returns:
        BaseCatchment instance
        
    Raises:
        ValueError: If catchment name is not found
        
    Example:
        catchment = get_catchment('thames')
        elevation = catchment.get_elevation(51.5, -0.1)
    """
    name = name.lower()
    
    if name not in CATCHMENTS:
        available = ", ".join(sorted(CATCHMENTS.keys()))
        raise ValueError(f"Unknown catchment: '{name}'. Available: {available}")
    
    # Return cached instance or create new one
    if name not in _catchment_instances:
        _catchment_instances[name] = CATCHMENTS[name]()
    
    return _catchment_instances[name]


def list_catchments(region: Optional[str] = None) -> List[str]:
    """
    List available catchment names.
    
    Args:
        region: Optional filter by region ('Europe' or 'NorthAmerica')
        
    Returns:
        List of catchment names
        
    Example:
        all_catchments = list_catchments()
        european = list_catchments(region='Europe')
    """
    if region is None:
        return sorted(CATCHMENTS.keys())
    
    result = []
    for name, cls in CATCHMENTS.items():
        if cls.REGION.lower() == region.lower():
            result.append(name)
    
    return sorted(result)


def get_catchment_info(name: str) -> Dict[str, Any]:
    """
    Get metadata about a catchment without instantiating.
    
    Args:
        name: Catchment identifier
        
    Returns:
        Dictionary with catchment metadata
        
    Raises:
        ValueError: If catchment name is not found
    """
    name = name.lower()
    
    if name not in CATCHMENTS:
        available = ", ".join(sorted(CATCHMENTS.keys()))
        raise ValueError(f"Unknown catchment: '{name}'. Available: {available}")
    
    cls = CATCHMENTS[name]
    
    return {
        'name': cls.NAME,
        'displayname': cls.DISPLAYNAME,
        'region': cls.REGION,
        'country': cls.COUNTRY,
        'gaugecount': len(cls.GAUGEPOINTS),
        'areacount': len(cls.AREAS),
        'bounds': cls.get_bounds(),
        'center': cls.get_center(),
        'implemented': len(cls.GAUGEPOINTS) > 0
    }


def get_all_catchment_info() -> Dict[str, Dict[str, Any]]:
    """
    Get metadata for all registered catchments.
    
    Returns:
        Dictionary mapping catchment names to their metadata
    """
    return {name: get_catchment_info(name) for name in CATCHMENTS}


def is_catchment_implemented(name: str) -> bool:
    """
    Check if a catchment has gauge data implemented.
    
    Args:
        name: Catchment identifier
        
    Returns:
        True if catchment has gauge points defined
    """
    name = name.lower()
    
    if name not in CATCHMENTS:
        return False
    
    return len(CATCHMENTS[name].GAUGEPOINTS) > 0


# Module exports
__all__ = [
    # Base
    'BaseCatchment',
    # Europe
    'ThamesCatchment',
    'RhineCatchment',
    'DanubeCatchment',
    'SeineCatchment',
    'PoCatchment',
    'ElbeCatchment',
    'MeuseCatchment',
    'RhineDeltaCatchment',
    'LoireCatchment',
    'EbroCatchment',
    # North America
    'MississippiCatchment',
    'HudsonCatchment',
    'StLawrenceCatchment',
    'DelawareCatchment',
    'SacramentoCatchment',
    'ConnecticutCatchment',
    'SusquehannaCatchment',
    'ColumbiaCatchment',
    'FraserCatchment',
    'RioGrandeCatchment',
    # Functions
    'get_catchment',
    'list_catchments',
    'get_catchment_info',
    'get_all_catchment_info',
    'is_catchment_implemented',
    'CATCHMENTS',
]
