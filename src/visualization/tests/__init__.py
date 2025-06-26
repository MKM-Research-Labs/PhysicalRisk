"""
Tropical Cyclone Event Visualization System.

A modular system for creating interactive visualizations of tropical cyclone events,
including storm paths, flood gauges, properties, and mortgage risk analysis.
"""

import sys
from pathlib import Path

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from utilities.project_paths import ProjectPaths

# Import main classes for easy access
from .core import TCEventVisualization
from .utils import DataFormatter, ColorSchemes, RiskAssessor, DataExtractor

# Version info
__version__ = "2.0.0"
__author__ = "MKM Research Labs"

# Main public interface
__all__ = [
    'TCEventVisualization',
    'DataFormatter',
    'ColorSchemes', 
    'RiskAssessor',
    'DataExtractor'
]


def create_visualization(input_dir=None, output_dir=None):
    """
    Convenience function to create a TCEventVisualization instance.
    
    Args:
        input_dir: Directory containing input JSON files
        output_dir: Directory for output files
        
    Returns:
        TCEventVisualization instance
    """
    return TCEventVisualization(input_dir=input_dir, output_dir=output_dir)