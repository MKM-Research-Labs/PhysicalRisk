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

# src/utilities/report_generator.py


"""
Clean Property Report Generator Utility
Orchestrates page modules to create comprehensive property reports.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

import webbrowser
import subprocess
import platform
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.pdfgen import canvas

# Import all page modules
from .page_01_title_overview import TitleOverviewPage
from .page_02_location import LocationPage
from .page_03_attributes import AttributesPage
from .page_04_construction import ConstructionPage
from .page_05_risk_assessment import RiskAssessmentPage
from .page_06_financial import FinancialPage
from .page_07_protection import ProtectionPage
from .page_08_energy import EnergyPage
from .page_09_history import HistoryPage
from .page_10_transactions import TransactionsPage
from .page_11_mortgage_overview import MortgageOverviewPage
from .page_11a_mortgage_details import MortgageDetailsPage
from .page_11b_mortgage_costs import MortgageCostsPage
from .page_11c_regulatory import RegulatoryPage
from .page_12_current_status import CurrentStatusPage
from .page_13_risk_analysis import RiskAnalysisPage
from .page_14_borrower_profile import BorrowerProfilePage
from .page_15_data_summary import DataSummaryPage


class PropertyReportGenerator:
    """Clean, focused report generator that orchestrates page modules."""
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """Initialize the report generator."""
        self.output_dir = Path(output_dir) if output_dir else Path("reports")
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()
    
    def _initialize_pages(self):
        """Initialize page generators and define page categories."""
        self.pages = {
            # Property pages
            'title_overview': TitleOverviewPage(),
            'location': LocationPage(),
            'attributes': AttributesPage(),
            'construction': ConstructionPage(),
            'risk_assessment': RiskAssessmentPage(),
            'financial': FinancialPage(),
            'protection': ProtectionPage(),
            'energy': EnergyPage(),
            'history': HistoryPage(),
            'transactions': TransactionsPage(),
            
            # Mortgage pages
            'mortgage_overview': MortgageOverviewPage(),
            'mortgage_details': MortgageDetailsPage(),
            'mortgage_costs': MortgageCostsPage(),
            'regulatory': RegulatoryPage(),
            'current_status': CurrentStatusPage(),
            'borrower_profile': BorrowerProfilePage(),
            
            # Analysis pages
            'risk_analysis': RiskAnalysisPage(),
            'data_summary': DataSummaryPage()
        }
        
        # Define page categories
        self.categories = {
            'property': [
                'title_overview', 'location', 'attributes', 'construction',
                'risk_assessment', 'financial', 'protection', 'energy',
                'history', 'transactions'
            ],
            'mortgage': [
                'mortgage_overview', 'mortgage_details', 'mortgage_costs', 
                'regulatory', 'current_status', 'borrower_profile'
            ],
            'analysis': [
                'risk_analysis', 'data_summary'
            ]
        }
    
    def generate_report(self, property_data: Dict[str, Any], 
                       mortgage_data: Optional[Dict[str, Any]] = None,
                       pages_to_include: Optional[List[str]] = None,
                       output_filename: Optional[str] = None) -> Path:
        """
        Generate a property report.
        
        Args:
            property_data: Property information
            mortgage_data: Mortgage information (optional)
            pages_to_include: Specific pages to include (auto-selected if None)
            output_filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to generated PDF
        """
        # Auto-select pages if not specified
        if pages_to_include is None:
            pages_to_include = self._auto_select_pages(property_data, mortgage_data)
        
        # Generate filename if not provided
        if output_filename is None:
            output_filename = self._generate_filename(property_data)
        
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
        elements = self._generate_elements(property_data, mortgage_data, pages_to_include)

        # Store count before doc.build() consumes the elements
        element_count = len(elements)

        # Build PDF
        doc.build(elements, 
                onFirstPage=self._create_header_footer,
                onLaterPages=self._create_header_footer)

        print(f"✓ Report generated: {output_path}")
        print(f"📊 Pages: {len(pages_to_include)} | Elements: {element_count}")
       
        return output_path
    
    def _auto_select_pages(self, property_data: Dict[str, Any], 
                          mortgage_data: Optional[Dict[str, Any]]) -> List[str]:
        """Auto-select appropriate pages based on available data."""
        pages = self.categories['property'].copy()
        
        if mortgage_data:
            pages.extend(self.categories['mortgage'])
        
        pages.extend(self.categories['analysis'])
        return pages
    
    def _generate_filename(self, property_data: Dict[str, Any]) -> str:
        """Generate output filename based on property data."""
        try:
            property_id = property_data['PropertyHeader']['Header']['PropertyID']
        except (KeyError, TypeError):
            property_id = 'unknown'
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"property_report_{property_id}_{timestamp}.pdf"
    
    def _generate_elements(self, property_data: Dict[str, Any], 
                          mortgage_data: Optional[Dict[str, Any]],
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
                    property_data, mortgage_data
                )
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
        canvas.setFillColor(colors.navy)
        canvas.drawString(0.5*inch, doc.height + doc.topMargin, "MKM Research Labs")
        
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.darkblue)
        canvas.drawRightString(doc.width + 0.5*inch, doc.height + doc.topMargin - 0.1*inch, 
                              "Property Analysis Report")
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
    def generate_property_only_report(self, property_data: Dict[str, Any],
                                    output_filename: Optional[str] = None) -> Path:
        """Generate property-only report."""
        pages = self.categories['property'] + self.categories['analysis']
        return self.generate_report(property_data, None, pages, output_filename)
    
    def generate_mortgage_focused_report(self, property_data: Dict[str, Any],
                                       mortgage_data: Dict[str, Any],
                                       output_filename: Optional[str] = None) -> Path:
        """Generate mortgage-focused report."""
        # Essential property context + all mortgage pages + analysis
        essential_property = ['title_overview', 'location', 'risk_assessment', 'financial']
        pages = essential_property + self.categories['mortgage'] + self.categories['analysis']
        return self.generate_report(property_data, mortgage_data, pages, output_filename)
    
    def generate_risk_focused_report(self, property_data: Dict[str, Any],
                                   mortgage_data: Optional[Dict[str, Any]] = None,
                                   output_filename: Optional[str] = None) -> Path:
        """Generate risk-focused report."""
        risk_pages = ['title_overview', 'risk_assessment', 'protection', 'history']
        
        if mortgage_data:
            risk_pages.extend(['current_status', 'borrower_profile'])
        
        risk_pages.extend(['risk_analysis', 'data_summary'])
        return self.generate_report(property_data, mortgage_data, risk_pages, output_filename)
    
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




def generate_property_report(property_data: Dict[str, Any], 
                        mortgage_data: Optional[Dict[str, Any]] = None,
                        output_dir: Optional[Union[str, Path]] = None,
                        report_type: str = "full",
                        auto_open: bool = True) -> Path:
    """
    Simple convenience function to generate a property report.
    
    Args:
        property_data: Property information
        mortgage_data: Mortgage information (optional)
        output_dir: Output directory
        report_type: Type of report ('full', 'property-only', 'mortgage-focused', 'risk-focused')
        auto_open: Whether to automatically open the PDF after generation
        
    Returns:
        Path to generated PDF
    """
    generator = PropertyReportGenerator(output_dir)
    
    # Generate the report
    if report_type == 'property-only':
        report_path = generator.generate_property_only_report(property_data)
    elif report_type == 'mortgage-focused' and mortgage_data:
        report_path = generator.generate_mortgage_focused_report(property_data, mortgage_data)
    elif report_type == 'risk-focused':
        report_path = generator.generate_risk_focused_report(property_data, mortgage_data)
    else:
        report_path = generator.generate_report(property_data, mortgage_data)
    
    # Auto-open the PDF if requested
    if auto_open:
        print(f"[DEBUG] Calling open_pdf_file({report_path})")
        try:
            open_pdf_file(report_path)
            print(f"📖 PDF opened automatically: {report_path}")
        except Exception as e:
            print(f"⚠️  Could not auto-open PDF: {e}")
            print(f"📁 Manual open: {report_path}")
    else:
        print(f"[DEBUG] auto_open is False, skipping PDF open")
    
    # CRITICAL FIX: Return the report path
    return report_path
    


def open_pdf_file(file_path: Path) -> bool:
    """
    Open a PDF file using the system's default PDF viewer.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        system = platform.system().lower()
        file_path_str = str(file_path.absolute())
        
        if system == "darwin":  # macOS
            subprocess.run(["open", file_path_str], check=True)
        elif system == "windows":  # Windows
            subprocess.run(["start", "", file_path_str], shell=True, check=True)
        elif system == "linux":  # Linux
            subprocess.run(["xdg-open", file_path_str], check=True)
        else:
            # Fallback: try using webbrowser module
            webbrowser.open(f"file://{file_path_str}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"System command failed: {e}")
        return False
    except Exception as e:
        print(f"Failed to open PDF: {e}")
        return False



def _find_property_by_id(data, property_id):
        """Find specific property in data structure."""
        if isinstance(data, dict):
            if 'properties' in data:
                properties = data['properties']
            elif 'portfolio' in data:
                properties = data['portfolio']
            else:
                properties = [data]
        elif isinstance(data, list):
            properties = data
        else:
            raise ValueError("Invalid property data structure")
        
        for prop in properties:
            prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
            if prop_id == property_id:
                return prop
        
        raise ValueError(f"Property {property_id} not found")


def _find_mortgage_by_property_id(data, property_id):
    """Find mortgage for specific property."""
    if isinstance(data, dict):
        mortgages = data.get('mortgages', [data])
    elif isinstance(data, list):
        mortgages = data
    else:
        return data
    
    for mortgage in mortgages:
        if mortgage.get('PropertyID') == property_id:
            return mortgage
    
    return None


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate property reports using modular page system.')
    
    # Required arguments
    parser.add_argument('--property-file', required=True, help='Property JSON file path')
    
    # Optional arguments
    parser.add_argument('--mortgage-file', help='Mortgage JSON file path')
    parser.add_argument('--output-dir', default='reports', help='Output directory')
    parser.add_argument('--property-id', help='Specific property ID to process')
    parser.add_argument('--pages', nargs='+', help='Specific pages to include')
    parser.add_argument('--report-type', 
                       choices=['full', 'property-only', 'mortgage-focused', 'risk-focused'],
                       default='full', help='Type of report to generate')
    
    # Information arguments
    parser.add_argument('--list-pages', action='store_true', help='List available pages')
    parser.add_argument('--list-categories', action='store_true', help='List page categories')
    
    args = parser.parse_args()
    
    # Handle information requests
    if args.list_pages:
        generator = PropertyReportGenerator()
        print("Available pages:")
        for page in generator.list_available_pages():
            print(f"  - {page}")
        sys.exit(0)
    
    if args.list_categories:
        generator = PropertyReportGenerator()
        print("Page categories:")
        for category, pages in generator.get_page_categories().items():
            print(f"\n{category}:")
            for page in pages:
                print(f"  - {page}")
        sys.exit(0)
    
    try:
        # Load data
        with open(args.property_file) as f:
            property_data = json.load(f)
        
        mortgage_data = None
        if args.mortgage_file:
            with open(args.mortgage_file) as f:
                mortgage_data = json.load(f)
        
        # Handle specific property ID
        if args.property_id:
            property_data = _find_property_by_id(property_data, args.property_id)
            if mortgage_data:
                mortgage_data = _find_mortgage_by_property_id(mortgage_data, args.property_id)
        
        # Generate report
        generator = PropertyReportGenerator(args.output_dir)
        
        if args.report_type == 'property-only':
            report_path = generator.generate_property_only_report(property_data)
        elif args.report_type == 'mortgage-focused' and mortgage_data:
            report_path = generator.generate_mortgage_focused_report(property_data, mortgage_data)
        elif args.report_type == 'risk-focused':
            report_path = generator.generate_risk_focused_report(property_data, mortgage_data)
        else:
            report_path = generator.generate_report(property_data, mortgage_data, args.pages)
        
        print(f"\n🎉 Report generated successfully!")
        print(f"📄 File: {report_path}")
        print(f"📊 Type: {args.report_type}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


