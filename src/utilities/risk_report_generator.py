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

# src/utilities/flood_risk_report_generator.py

"""
Flood Risk Report Generator
Orchestrates page modules to create comprehensive flood risk reports.
Following the exact patterns of the gauge report system.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.pdfgen import canvas

# Import flood risk page modules
from risk_base_page import FloodRiskBasePage
from risk_page_01_title import FloodRiskTitlePage
from risk_page_02_executive_summary import FloodRiskExecutiveSummaryPage
from risk_page_03_portfolio_overview import FloodRiskPortfolioOverviewPage
from risk_page_04_risk_analysis import FloodRiskAnalysisPage
from risk_page_05_mortgage_analysis import FloodRiskMortgageAnalysisPage
from risk_page_06_property_details import FloodRiskPropertyDetailsPage
from risk_page_07_appendix import FloodRiskAppendixPage


class FloodRiskReportGenerator:
    """Flood risk report generator following gauge system patterns."""
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """Initialize the flood risk report generator."""
        self.output_dir = Path(output_dir) if output_dir else Path("reports")
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()
    
    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
            'title': FloodRiskTitlePage(),
            'executive_summary': FloodRiskExecutiveSummaryPage(),
            'portfolio_overview': FloodRiskPortfolioOverviewPage(),
            'risk_analysis': FloodRiskAnalysisPage(),
            'mortgage_analysis': FloodRiskMortgageAnalysisPage(),
            'property_details': FloodRiskPropertyDetailsPage(),
            'appendix': FloodRiskAppendixPage(),
        }
        
        # Define page categories
        self.categories = {
            'overview': ['title', 'executive_summary', 'portfolio_overview'],
            'analysis': ['risk_analysis', 'mortgage_analysis', 'property_details'],
            'appendix': ['appendix']
        }
    
    def generate_report(self, 
                       flood_data: Dict[str, Any],
                       output_filename: Optional[str] = None,
                       pages_to_include: Optional[List[str]] = None) -> Path:
        """
        Generate a flood risk report.
        
        Args:
            flood_data: Flood risk analysis data
            output_filename: Custom filename (auto-generated if None)
            pages_to_include: Specific pages to include (auto-selected if None)
            
        Returns:
            Path to generated PDF
        """
        # Auto-select pages if not specified
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(flood_data)
        
        # Generate filename if not provided
        if output_filename is None:
            output_filename = self._generate_filename()
        
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
        elements = self._generate_elements(flood_data, pages_to_include)
        
        # Build PDF
        doc.build(elements, 
                    onFirstPage=self._create_header_footer,
                    onLaterPages=self._create_header_footer)
        
        print(f"✓ Flood risk report generated: {output_path}")
        print(f"📊 Pages: {len(pages_to_include)} | Elements: {len(elements)}")
        
        return output_path
    
    def _auto_select_pages(self, flood_data: Dict[str, Any]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['overview'].copy()
        pages.extend(self.categories['analysis'])
        
        # Add appendix
        pages.extend(self.categories['appendix'])
        
        # Filter out pages that don't exist
        available_pages = [page for page in pages if page in self.pages]
        return available_pages
    
    def _generate_filename(self) -> str:
        """Generate output filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"flood_risk_report_{timestamp}.pdf"
    
    def _generate_elements(self, flood_data: Dict[str, Any], 
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
                page_elements = self.pages[page_name].generate_elements(flood_data)
                elements.extend(page_elements)
                
                print(f"✓ Generated {page_name}")
                
            except Exception as e:
                print(f"✗ Error generating {page_name}: {str(e)}")
                continue
        
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
                              "Flood Risk Analysis Report")
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
    def generate_basic_report(self, flood_data: Dict[str, Any],
                             output_filename: Optional[str] = None) -> Path:
        """Generate basic flood risk report."""
        pages = ['title', 'executive_summary', 'portfolio_overview', 'risk_analysis', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)
    
    def generate_detailed_report(self, flood_data: Dict[str, Any],
                                output_filename: Optional[str] = None) -> Path:
        """Generate detailed flood risk report with all pages."""
        pages = ['title', 'executive_summary', 'portfolio_overview', 'risk_analysis', 
                'mortgage_analysis', 'property_details', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)
    
    def generate_summary_report(self, flood_data: Dict[str, Any],
                               output_filename: Optional[str] = None) -> Path:
        """Generate summary-focused report."""
        pages = ['title', 'executive_summary', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)
    
    def generate_analysis_report(self, flood_data: Dict[str, Any],
                                output_filename: Optional[str] = None) -> Path:
        """Generate analysis-focused report."""
        pages = ['title', 'risk_analysis', 'property_details', 'appendix']
        return self.generate_report(flood_data, output_filename, pages)
    
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
def generate_flood_risk_report(flood_data: Dict[str, Any], 
                              output_dir: Optional[Union[str, Path]] = None,
                              report_type: str = "basic") -> Path:
    """
    Simple convenience function to generate a flood risk report.
    
    Args:
        flood_data: Flood risk analysis data
        output_dir: Output directory
        report_type: Type of report ('basic', 'detailed', 'summary', 'analysis')
        
    Returns:
        Path to generated PDF
    """
    generator = FloodRiskReportGenerator(output_dir)
    
    if report_type == 'basic':
        return generator.generate_basic_report(flood_data)
    elif report_type == 'detailed':
        return generator.generate_detailed_report(flood_data)
    elif report_type == 'summary':
        return generator.generate_summary_report(flood_data)
    elif report_type == 'analysis':
        return generator.generate_analysis_report(flood_data)
    else:
        return generator.generate_report(flood_data)


if __name__ == "__main__":
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate flood risk reports using modular page system.')
    
    # Required arguments
    parser.add_argument('--flood-file', required=True, help='Flood risk JSON file path')
    
    # Optional arguments
    parser.add_argument('--output-dir', default='reports', help='Output directory')
    parser.add_argument('--pages', nargs='+', help='Specific pages to include')
    parser.add_argument('--report-type', 
                       choices=['basic', 'detailed', 'summary', 'analysis'],
                       default='basic', help='Type of report to generate')
    
    # Information arguments
    parser.add_argument('--list-pages', action='store_true', help='List available pages')
    parser.add_argument('--list-categories', action='store_true', help='List page categories')
    
    args = parser.parse_args()
    
    # Handle information requests
    if args.list_pages:
        generator = FloodRiskReportGenerator()
        print("Available pages:")
        for page in generator.list_available_pages():
            print(f"  - {page}")
        sys.exit(0)
    
    if args.list_categories:
        generator = FloodRiskReportGenerator()
        print("Page categories:")
        for category, pages in generator.get_page_categories().items():
            print(f"\n{category}:")
            for page in pages:
                print(f"  - {page}")
        sys.exit(0)
    
    try:
        # Load data
        with open(args.flood_file) as f:
            flood_data = json.load(f)
        
        # Generate report
        generator = FloodRiskReportGenerator(args.output_dir)
        
        if args.report_type == 'basic':
            report_path = generator.generate_basic_report(flood_data)
        elif args.report_type == 'detailed':
            report_path = generator.generate_detailed_report(flood_data)
        elif args.report_type == 'summary':
            report_path = generator.generate_summary_report(flood_data)
        elif args.report_type == 'analysis':
            report_path = generator.generate_analysis_report(flood_data)
        else:
            report_path = generator.generate_report(flood_data, pages_to_include=args.pages)
        
        print(f"\n🎉 Flood risk report generated successfully!")
        print(f"📄 File: {report_path}")
        print(f"📊 Type: {args.report_type}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)