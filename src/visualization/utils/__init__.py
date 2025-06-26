"""
Utility modules for the visualization system.

This package provides various utility functions for data formatting,
risk assessment, color schemes, and data extraction.
"""

import sys
from pathlib import Path

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from utilities.project_paths import ProjectPaths

# Import main classes
from .formatters import DataFormatter
from .color_schemes import ColorSchemes
from .risk_assessors import RiskAssessor
from .data_extractors import DataExtractor

# Import convenience functions for backward compatibility
from .formatters import (
    safe_format_float,
    format_currency,
    format_percentage,
    format_coordinates,
    format_date,
    format_address
)

from .color_schemes import (
    get_risk_color,
    get_status_color
)

from .risk_assessors import (
    assess_mortgage_risk_summary,
    calculate_combined_risk
)

from .data_extractors import (
    extract_property_info,
    build_mortgage_lookup
)

__all__ = [
    # Main classes
    'DataFormatter',
    'ColorSchemes',
    'RiskAssessor',
    'DataExtractor',
    
    # Convenience functions
    'safe_format_float',
    'format_currency',
    'format_percentage',
    'format_coordinates',
    'format_date',
    'format_address',
    'get_risk_color',
    'get_status_color',
    'assess_mortgage_risk_summary',
    'calculate_combined_risk',
    'extract_property_info',
    'build_mortgage_lookup'
]