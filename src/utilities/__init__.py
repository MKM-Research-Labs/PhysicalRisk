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
Utilities Package.

This package contains utility functions and helpers that are used across
the different modules of the application, including the modular property
report generation system and flood risk analysis system.
"""

# Existing utilities
from .project_paths import ProjectPaths

# Property Report Generation System
try:
    from .report_generator import (
        PropertyReportGenerator,
        generate_property_report
    )
    from .base_page import BasePage
    
    # Property report generator is available
    _PROPERTY_REPORT_AVAILABLE = True
    
except ImportError:
    # Property report generator dependencies not available
    _PROPERTY_REPORT_AVAILABLE = False

# Flood Risk Report Generation System (New)
try:
    from .flood_risk_report_generator import (
        FloodRiskReportGenerator,
        generate_flood_risk_report
    )
    from .risk_base_page import RiskBasePage
    
    # Import all flood risk page modules
    from .risk_page_01_title import RiskTitlePage
    from .risk_page_02_executive_summary import RiskExecutiveSummaryPage
    from .risk_page_03_portfolio_overview import RiskPortfolioOverviewPage
    from .risk_page_04_risk_analysis import RiskAnalysisPage
    from .risk_page_05_mortgage_analysis import RiskMortgageAnalysisPage
    from .risk_page_06_property_details import RiskPropertyDetailsPage
    from .risk_page_07_appendix import RiskAppendixPage
    
    # Flood risk report generator is available
    _FLOOD_RISK_REPORT_AVAILABLE = True
    
except ImportError:
    # Flood risk report generator dependencies not available
    _FLOOD_RISK_REPORT_AVAILABLE = False

# Gauge Report Generation System
try:
    from .gauge_report_generator import (
        GaugeReportGenerator,
        generate_gauge_report
    )
    from .gauge_base_page import GaugeBasePage
    
    # Import gauge page modules
    from .gauge_page_01_title_overview import GaugeTitleOverviewPage
    from .gauge_page_02_sensor_details import GaugeSensorDetailsPage
    # Additional gauge pages would be imported here as they're added
    
    # Gauge report generator is available
    _GAUGE_REPORT_AVAILABLE = True
    
except ImportError:
    # Gauge report generator dependencies not available
    _GAUGE_REPORT_AVAILABLE = False

# Build public API based on available components
__all__ = ['ProjectPaths']

if _PROPERTY_REPORT_AVAILABLE:
    __all__.extend([
        'PropertyReportGenerator',
        'generate_property_report',
        'BasePage'
    ])

if _FLOOD_RISK_REPORT_AVAILABLE:
    __all__.extend([
        'FloodRiskReportGenerator',
        'generate_flood_risk_report',
        'RiskBasePage',
        'RiskTitlePage',
        'RiskExecutiveSummaryPage', 
        'RiskPortfolioOverviewPage',
        'RiskAnalysisPage',
        'RiskMortgageAnalysisPage',
        'RiskPropertyDetailsPage',
        'RiskAppendixPage'
    ])

if _GAUGE_REPORT_AVAILABLE:
    __all__.extend([
        'GaugeReportGenerator',
        'generate_gauge_report',
        'GaugeBasePage',
        'GaugeTitleOverviewPage',
        'GaugeSensorDetailsPage'
    ])


def is_property_report_available() -> bool:
    """Check if the property report generator is available."""
    return _PROPERTY_REPORT_AVAILABLE


def is_flood_risk_report_available() -> bool:
    """Check if the flood risk report generator is available."""
    return _FLOOD_RISK_REPORT_AVAILABLE


def is_gauge_report_available() -> bool:
    """Check if the gauge report generator is available."""
    return _GAUGE_REPORT_AVAILABLE


def get_available_utilities() -> dict:
    """Return information about available utilities."""
    utilities = {
        'ProjectPaths': {
            'available': True,
            'description': 'Project path management utility'
        }
    }
    
    # Property Report Generator
    if _PROPERTY_REPORT_AVAILABLE:
        utilities.update({
            'PropertyReportGenerator': {
                'available': True,
                'description': 'Modular property report generation system',
                'total_pages': 15,
                'report_types': ['full', 'property-only', 'mortgage-focused', 'risk-focused']
            },
            'generate_property_report': {
                'available': True,
                'description': 'Convenience function for property report generation'
            },
            'BasePage': {
                'available': True,
                'description': 'Base class for custom property report pages'
            }
        })
    else:
        utilities['PropertyReportGenerator'] = {
            'available': False,
            'description': 'Property report generator not available - missing dependencies',
            'required_dependencies': ['reportlab']
        }
    
    # Flood Risk Report Generator
    if _FLOOD_RISK_REPORT_AVAILABLE:
        utilities.update({
            'FloodRiskReportGenerator': {
                'available': True,
                'description': 'Modular flood risk analysis report generation system',
                'total_pages': 7,
                'report_types': ['basic', 'executive', 'detailed', 'full']
            },
            'generate_flood_risk_report': {
                'available': True,
                'description': 'Convenience function for flood risk report generation'
            },
            'RiskBasePage': {
                'available': True,
                'description': 'Base class for custom flood risk report pages'
            }
        })
    else:
        utilities['FloodRiskReportGenerator'] = {
            'available': False,
            'description': 'Flood risk report generator not available - missing dependencies',
            'required_dependencies': ['reportlab', 'matplotlib (optional)']
        }
    
    # Gauge Report Generator
    if _GAUGE_REPORT_AVAILABLE:
        utilities.update({
            'GaugeReportGenerator': {
                'available': True,
                'description': 'Modular gauge analysis report generation system',
                'total_pages': 7,
                'report_types': ['basic', 'monitoring', 'analysis', 'full']
            },
            'generate_gauge_report': {
                'available': True,
                'description': 'Convenience function for gauge report generation'
            },
            'GaugeBasePage': {
                'available': True,
                'description': 'Base class for custom gauge report pages'
            }
        })
    else:
        utilities['GaugeReportGenerator'] = {
            'available': False,
            'description': 'Gauge report generator not available - missing dependencies',
            'required_dependencies': ['reportlab']
        }
    
    return utilities


# Property Report Convenience Functions
if _PROPERTY_REPORT_AVAILABLE:
    def create_property_report(property_data, mortgage_data=None, output_dir="reports", report_type="full"):
        """
        Convenience function to create property reports with minimal setup.
        
        Args:
            property_data: Property information dictionary
            mortgage_data: Mortgage information dictionary (optional)
            output_dir: Output directory for reports
            report_type: Type of report ('full', 'property-only', 'mortgage-focused', 'risk-focused')
            
        Returns:
            Path to generated report
        """
        generator = PropertyReportGenerator(output_dir)
        
        if report_type == 'property-only':
            return generator.generate_property_only_report(property_data)
        elif report_type == 'mortgage-focused' and mortgage_data:
            return generator.generate_mortgage_focused_report(property_data, mortgage_data)
        elif report_type == 'risk-focused':
            return generator.generate_risk_focused_report(property_data, mortgage_data)
        else:
            return generator.generate_report(property_data, mortgage_data)
    
    def list_property_report_pages():
        """List all available property report pages."""
        generator = PropertyReportGenerator()
        return generator.list_available_pages()
    
    def get_property_report_page_categories():
        """Get categorized list of property report pages."""
        generator = PropertyReportGenerator()
        return generator.get_page_categories()
    
    # Add property convenience functions to public API
    __all__.extend([
        'create_property_report',
        'list_property_report_pages', 
        'get_property_report_page_categories'
    ])


# Flood Risk Report Convenience Functions
if _FLOOD_RISK_REPORT_AVAILABLE:
    def create_flood_risk_report(report_data, output_dir="reports", report_type="basic"):
        """
        Convenience function to create flood risk reports with minimal setup.
        
        Args:
            report_data: Flood risk analysis data dictionary
            output_dir: Output directory for reports
            report_type: Type of report ('basic', 'executive', 'detailed', 'full')
            
        Returns:
            Path to generated report
        """
        generator = FloodRiskReportGenerator(output_dir)
        
        if report_type == 'basic':
            return generator.generate_basic_report(report_data)
        elif report_type == 'executive':
            return generator.generate_executive_report(report_data)
        elif report_type == 'detailed':
            return generator.generate_detailed_report(report_data)
        else:
            return generator.generate_report(report_data)
    
    def list_flood_risk_report_pages():
        """List all available flood risk report pages."""
        generator = FloodRiskReportGenerator()
        return generator.list_available_pages()
    
    def get_flood_risk_report_page_categories():
        """Get categorized list of flood risk report pages."""
        generator = FloodRiskReportGenerator()
        return generator.get_page_categories()
    
    # Add flood risk convenience functions to public API
    __all__.extend([
        'create_flood_risk_report',
        'list_flood_risk_report_pages', 
        'get_flood_risk_report_page_categories'
    ])


# Gauge Report Convenience Functions
if _GAUGE_REPORT_AVAILABLE:
    def create_gauge_report(gauge_data, timeseries_data=None, output_dir="reports", report_type="basic"):
        """
        Convenience function to create gauge reports with minimal setup.
        
        Args:
            gauge_data: Gauge information dictionary
            timeseries_data: Timeseries data dictionary (optional)
            output_dir: Output directory for reports
            report_type: Type of report ('basic', 'monitoring', 'analysis', 'full')
            
        Returns:
            Path to generated report
        """
        generator = GaugeReportGenerator(output_dir)
        
        if report_type == 'basic':
            return generator.generate_basic_report(gauge_data)
        elif report_type == 'monitoring' and timeseries_data:
            return generator.generate_monitoring_report(gauge_data, timeseries_data)
        elif report_type == 'analysis':
            return generator.generate_analysis_report(gauge_data, timeseries_data)
        else:
            return generator.generate_report(gauge_data, timeseries_data)
    
    def list_gauge_report_pages():
        """List all available gauge report pages."""
        generator = GaugeReportGenerator()
        return generator.list_available_pages()
    
    def get_gauge_report_page_categories():
        """Get categorized list of gauge report pages."""
        generator = GaugeReportGenerator()
        return generator.get_page_categories()
    
    # Add gauge convenience functions to public API
    __all__.extend([
        'create_gauge_report',
        'list_gauge_report_pages', 
        'get_gauge_report_page_categories'
    ])


# Unified report generation function
def create_report(data_type, data, **kwargs):
    """
    Unified convenience function for creating any type of report.
    
    Args:
        data_type: Type of report ('property', 'flood_risk', 'gauge')
        data: Primary data for the report
        **kwargs: Additional arguments passed to specific generators
        
    Returns:
        Path to generated report
        
    Raises:
        ValueError: If data_type is not supported or generator not available
    """
    if data_type == 'property' and _PROPERTY_REPORT_AVAILABLE:
        return create_property_report(data, **kwargs)
    elif data_type == 'flood_risk' and _FLOOD_RISK_REPORT_AVAILABLE:
        return create_flood_risk_report(data, **kwargs)
    elif data_type == 'gauge' and _GAUGE_REPORT_AVAILABLE:
        return create_gauge_report(data, **kwargs)
    else:
        available_types = []
        if _PROPERTY_REPORT_AVAILABLE:
            available_types.append('property')
        if _FLOOD_RISK_REPORT_AVAILABLE:
            available_types.append('flood_risk')
        if _GAUGE_REPORT_AVAILABLE:
            available_types.append('gauge')
        
        raise ValueError(f"Report type '{data_type}' not supported or not available. "
                        f"Available types: {available_types}")


def get_report_capabilities():
    """Get comprehensive information about all available report generators."""
    return {
        'property_reports': {
            'available': _PROPERTY_REPORT_AVAILABLE,
            'pages': list_property_report_pages() if _PROPERTY_REPORT_AVAILABLE else [],
            'categories': get_property_report_page_categories() if _PROPERTY_REPORT_AVAILABLE else {}
        },
        'flood_risk_reports': {
            'available': _FLOOD_RISK_REPORT_AVAILABLE,
            'pages': list_flood_risk_report_pages() if _FLOOD_RISK_REPORT_AVAILABLE else [],
            'categories': get_flood_risk_report_page_categories() if _FLOOD_RISK_REPORT_AVAILABLE else {}
        },
        'gauge_reports': {
            'available': _GAUGE_REPORT_AVAILABLE,
            'pages': list_gauge_report_pages() if _GAUGE_REPORT_AVAILABLE else [],
            'categories': get_gauge_report_page_categories() if _GAUGE_REPORT_AVAILABLE else {}
        }
    }


# Add unified functions to public API
__all__.extend([
    'create_report',
    'get_report_capabilities'
])


# Package metadata
__version__ = "3.0.0"
__author__ = "MKM Research Labs"
__license__ = "Proprietary"
__description__ = "Utilities package with modular report generation systems (property, flood risk, gauge)"