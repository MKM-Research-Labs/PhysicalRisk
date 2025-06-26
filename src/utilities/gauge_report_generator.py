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

# src/utilities/gauge_report_generator.py

"""
Clean Gauge Report Generator Utility
Orchestrates page modules to create comprehensive gauge reports.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.pdfgen import canvas

# Import gauge page modules
from .gauge_page_01_title_overview import GaugeTitleOverviewPage
from .gauge_page_02_sensor_details import GaugeSensorDetailsPage
from .gauge_page_03_location import GaugeLocationPage
from .gauge_page_04_measurements import GaugeMeasurementsPage
from .gauge_page_05_flood_stages import GaugeFloodStagesPage
from .gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
from .gauge_page_07_data_summary import GaugeDataSummaryPage

class GaugeReportGenerator:
    """Clean, focused gauge report generator that orchestrates page modules."""
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """Initialize the gauge report generator."""
        self.output_dir = Path(output_dir) if output_dir else Path("reports")
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()
    
    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
            # Gauge pages
            'title_overview': GaugeTitleOverviewPage(),
            'sensor_details': GaugeSensorDetailsPage(),
            'location': GaugeLocationPage(),
            'measurements': GaugeMeasurementsPage(),
            'flood_stages': GaugeFloodStagesPage(),
            'risk_assessment': GaugeRiskAssessmentPage(),
            'data_summary': GaugeDataSummaryPage(),
            # Additional pages will be added incrementally
        }
        
        # Define page categories
        self.categories = {
            'gauge_info': [
                'title_overview', 'sensor_details', 'location'
                # 'sensor_details', 'location' - to be added
            ],
            'operational': [
                'measurements', 'flood_stages'
                # 'maintenance' - to be added
            ],
            'analysis': [
                'risk_assessment'
                # 'historical_data', 'risk_assessment', 'timeseries_analysis' - to be added
            ],
            'summary': [
                'data_summary'
                # 'data_summary' - to be added
            ]
        }
    
    def generate_report(self, gauge_data: Dict[str, Any], 
                  timeseries_data: Optional[Dict[str, Any]] = None,
                  pages_to_include: Optional[List[str]] = None,
                  output_filename: Optional[str] = None) -> Path:
        """
        Generate a gauge report.
        
        Args:
            gauge_data: Gauge information
            timeseries_data: Timeseries data (optional)
            pages_to_include: Specific pages to include (auto-selected if None)
            output_filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to generated PDF
        """
        # Auto-select pages if not specified
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(gauge_data, timeseries_data)
        
        # Generate filename if not provided
        if output_filename is None:
            output_filename = self._generate_filename(gauge_data)
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=1.2*inch,
            bottomMargin=1*inch
        )
        
        # Generate all page elements
        elements = self._generate_elements(gauge_data, timeseries_data, pages_to_include)
        
        # Store count before doc.build() consumes the elements
        element_count = len(elements)
        
        # Build PDF
        doc.build(elements, 
                    onFirstPage=self._create_header_footer,
                    onLaterPages=self._create_header_footer)
        
        print(f"✓ Gauge report generated: {output_path}")
        print(f"📊 Pages: {len(pages_to_include)} | Elements: {element_count}")
        
        return output_path
    
    def _auto_select_pages(self, gauge_data: Dict[str, Any], 
                          timeseries_data: Optional[Dict[str, Any]]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['gauge_info'].copy()
        
        # Add operational pages when available
        pages.extend(self.categories['operational'])
        
        # Add analysis pages if timeseries data available
        if timeseries_data:
            pages.extend(self.categories['analysis'])
        
        # Always add summary
        pages.extend(self.categories['summary'])
        
        # Filter out pages that don't exist yet
        available_pages = [page for page in pages if page in self.pages]
        return available_pages
    
    def _generate_filename(self, gauge_data: Dict[str, Any]) -> str:
        """Generate output filename based on gauge data."""
        try:
            gauge_id = gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            gauge_id = 'unknown'
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"gauge_report_{gauge_id}_{timestamp}.pdf"
    
    def _generate_elements(self, gauge_data: Dict[str, Any], 
                     timeseries_data: Optional[Dict[str, Any]],
                     pages_to_include: List[str]) -> List:
        """Generate all report elements."""
        elements = []
        
        for i, page_name in enumerate(pages_to_include):
            if page_name not in self.pages:
                print(f"⚠️  Skipping unknown page: {page_name}")
                continue
            
            try:
                # Add page break (except for first page)
                if i > 0:
                    elements.append(PageBreak())
                
                # Generate page elements
                page_elements = self.pages[page_name].generate_elements(
                    gauge_data, timeseries_data
                )
                
                print(f"🔍 Debug - Page {page_name} generated {len(page_elements)} elements")
                elements.extend(page_elements)
                
                print(f"✓ Generated {page_name}")
                
            except Exception as e:
                print(f"✗ Error generating {page_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"🔍 Debug - Total elements in _generate_elements: {len(elements)}")
        return elements
    
    
    def _create_header_footer(self, canvas, doc):
        """Add headers and footers to pages."""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.darkblue)
        canvas.drawString(0.5*inch, doc.height + doc.topMargin, "MKM Research Labs")
        
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.blue)
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.1*inch, 
                              "Flood Gauge Analysis Report")
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.3*inch, 
                              f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(0.5*inch, doc.bottomMargin - 0.5*inch, f"Page {doc.page}")
        canvas.drawCentredString(doc.width/2.0 + 0.5*inch, doc.bottomMargin - 0.5*inch, 
                               "CONFIDENTIAL - For authorized use only")
        
        # Footer line
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(0.5*inch, doc.bottomMargin - 0.25*inch, 
                   doc.width + 0.5*inch, doc.bottomMargin - 0.25*inch)
        
        canvas.restoreState()
    
    # Specialized report generators
    def generate_basic_report(self, gauge_data: Dict[str, Any],
                         output_filename: Optional[str] = None) -> Path:
        """Generate basic gauge report."""
        pages = ['title_overview', 'sensor_details', 'location', 'measurements', 'flood_stages', 'risk_assessment', 'data_summary']
        return self.generate_report(gauge_data, None, pages, output_filename)
    
    def generate_monitoring_report(self, gauge_data: Dict[str, Any],
                                  timeseries_data: Dict[str, Any],
                                  output_filename: Optional[str] = None) -> Path:
        """Generate monitoring-focused report."""
        # Essential gauge context + operational data
        essential_gauge = ['title_overview']  # Will expand
        pages = essential_gauge  # Will add operational pages when available
        return self.generate_report(gauge_data, timeseries_data, pages, output_filename)
    
    def generate_analysis_report(self, gauge_data: Dict[str, Any],
                                timeseries_data: Optional[Dict[str, Any]] = None,
                                output_filename: Optional[str] = None) -> Path:
        """Generate analysis-focused report."""
        analysis_pages = ['title_overview']  # Will expand with analysis pages
        return self.generate_report(gauge_data, timeseries_data, analysis_pages, output_filename)
    
    # Utility methods
    def list_available_pages(self) -> List[str]:
        """Return list of available pages."""
        return list(self.pages.keys())
    
    def get_page_categories(self) -> Dict[str, List[str]]:
        """Return page categories."""
        return self.categories.copy()
    
    def validate_pages(self, pages: List[str]) -> tuple[List[str], List[str]]:
        """Validate page list, return (valid_pages, invalid_pages)."""
        valid = [p for p in pages if p in self.pages]
        invalid = [p for p in pages if p not in self.pages]
        return valid, invalid


# Convenience function
def generate_gauge_report(gauge_data: Dict[str, Any], 
                         timeseries_data: Optional[Dict[str, Any]] = None,
                         output_dir: Optional[Union[str, Path]] = None,
                         report_type: str = "basic",
                         auto_open: bool = True) -> Path:  # Add this parameter
    """
    Simple convenience function to generate a gauge report.
    
    Args:
        gauge_data: Gauge information
        timeseries_data: Timeseries data (optional)
        output_dir: Output directory
        report_type: Type of report ('basic', 'monitoring', 'analysis', 'full')
        auto_open: Whether to automatically open the PDF after generation
        
    Returns:
        Path to generated PDF
    """
    generator = GaugeReportGenerator(output_dir)
    
    # Generate the report
    if report_type == 'basic':
        report_path = generator.generate_basic_report(gauge_data)
    elif report_type == 'monitoring' and timeseries_data:
        report_path = generator.generate_monitoring_report(gauge_data, timeseries_data)
    elif report_type == 'analysis':
        report_path = generator.generate_analysis_report(gauge_data, timeseries_data)
    else:
        report_path = generator.generate_report(gauge_data, timeseries_data)
    
    # Auto-open the PDF if requested
    if auto_open:
        try:
            # Import the open_pdf_file function from report_generator
            from .report_generator import open_pdf_file
            open_pdf_file(report_path)
            print(f"📖 Gauge PDF opened automatically: {report_path}")
        except Exception as e:
            print(f"⚠️  Could not auto-open gauge PDF: {e}")
            print(f"📁 Manual open: {report_path}")
    
    return report_path

def _find_gauge_by_id(data, gauge_id):
    
   """Find specific gauge in data structure."""
   if isinstance(data, dict):
       if 'flood_gauges' in data:
           gauges = data['flood_gauges']
       elif 'FloodGauge' in data:
           # Single gauge object
           return data
       else:
           raise ValueError("Invalid gauge data structure - no 'flood_gauges' or 'FloodGauge' found")
   elif isinstance(data, list):
       gauges = data
   else:
       raise ValueError("Invalid gauge data structure - must be dict or list")
   
   for gauge in gauges:
       try:
           gauge_header_id = gauge.get('FloodGauge', {}).get('Header', {}).get('GaugeID')
           if gauge_header_id == gauge_id:
               return gauge
       except (AttributeError, TypeError):
           continue
   
   raise ValueError(f"Gauge {gauge_id} not found in data")


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate gauge reports using modular page system.')
    
    # Required arguments
    parser.add_argument('--gauge-file', required=True, help='Gauge JSON file path')
    
    # Optional arguments
    parser.add_argument('--timeseries-file', help='Timeseries JSON file path')
    parser.add_argument('--output-dir', default='reports', help='Output directory')
    parser.add_argument('--gauge-id', help='Specific gauge ID to process')
    parser.add_argument('--pages', nargs='+', help='Specific pages to include')
    parser.add_argument('--report-type', 
                       choices=['basic', 'monitoring', 'analysis', 'full'],
                       default='basic', help='Type of report to generate')
    
    # Information arguments
    parser.add_argument('--list-pages', action='store_true', help='List available pages')
    parser.add_argument('--list-categories', action='store_true', help='List page categories')
    
    args = parser.parse_args()
    
    # Handle information requests
    if args.list_pages:
        generator = GaugeReportGenerator()
        print("Available pages:")
        for page in generator.list_available_pages():
            print(f"  - {page}")
        sys.exit(0)
    
    if args.list_categories:
        generator = GaugeReportGenerator()
        print("Page categories:")
        for category, pages in generator.get_page_categories().items():
            print(f"\n{category}:")
            for page in pages:
                print(f"  - {page}")
        sys.exit(0)
    
    try:
        # Load data
        with open(args.gauge_file) as f:
            gauge_data = json.load(f)
        
        timeseries_data = None
        if args.timeseries_file:
            with open(args.timeseries_file) as f:
                timeseries_data = json.load(f)
        
        # Handle specific gauge ID
        if args.gauge_id:
            gauge_data = _find_gauge_by_id(gauge_data, args.gauge_id)
        
        # Generate report
        generator = GaugeReportGenerator(args.output_dir)
        
        if args.report_type == 'basic':
            report_path = generator.generate_basic_report(gauge_data)
        elif args.report_type == 'monitoring' and timeseries_data:
            report_path = generator.generate_monitoring_report(gauge_data, timeseries_data)
        elif args.report_type == 'analysis':
            report_path = generator.generate_analysis_report(gauge_data, timeseries_data)
        else:
            report_path = generator.generate_report(gauge_data, timeseries_data, args.pages)
        
        print(f"\n🎉 Gauge report generated successfully!")
        print(f"📄 File: {report_path}")
        print(f"📊 Type: {args.report_type}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

