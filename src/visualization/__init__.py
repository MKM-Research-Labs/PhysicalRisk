# Copyright (c) 2025 MKM Research Labs. All rights reserved.
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