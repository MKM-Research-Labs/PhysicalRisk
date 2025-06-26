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
#!/usr/bin/env python3
"""
Property report generation integration.
"""

from pathlib import Path
import json
from typing import Optional
import tempfile

def generate_report_for_property(property_id: str, property_file: Path, 
                                mortgage_file: Path, output_dir: Path) -> Optional[Path]:
    """
    Generate a PDF report for a specific property.
    
    Args:
        property_id: ID of the property to generate report for
        property_file: Path to property portfolio JSON file
        mortgage_file: Path to mortgage portfolio JSON file  
        output_dir: Directory to save the report
        
    Returns:
        Path to generated report file or None if failed
    """
    try:
        print(f"Generating report for property: {property_id}")
        
        # Load property data
        if not property_file.exists():
            print(f"Property file not found: {property_file}")
            return None
            
        with open(property_file) as f:
            property_data = json.load(f)
        
        # Find the specific property
        properties = property_data.get('properties', [])
        target_property = None
        
        for prop in properties:
            prop_id = prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID')
            if prop_id == property_id:
                target_property = prop
                break
        
        if not target_property:
            print(f"Property {property_id} not found in data")
            return None
        
        # Load mortgage data if available
        mortgage_info = None
        if mortgage_file.exists():
            with open(mortgage_file) as f:
                mortgage_data = json.load(f)
                
            mortgages = mortgage_data.get('mortgages', [])
            for mortgage in mortgages:
                mtg_prop_id = mortgage.get('Mortgage', {}).get('Header', {}).get('PropertyID')
                if mtg_prop_id == property_id:
                    mortgage_info = mortgage.get('Mortgage', {})
                    break
        
        # Generate simple text report (could be enhanced to PDF)
        output_dir.mkdir(exist_ok=True)
        report_file = output_dir / f"property_report_{property_id}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"PROPERTY REPORT\n")
            f.write(f"================\n\n")
            f.write(f"Property ID: {property_id}\n")
            
            # Property details
            header = target_property.get('PropertyHeader', {}).get('Header', {})
            f.write(f"Type: {header.get('propertyType', 'Unknown')}\n")
            f.write(f"Status: {header.get('propertyStatus', 'Unknown')}\n")
            
            # Location
            location = target_property.get('PropertyHeader', {}).get('Location', {})
            f.write(f"Address: {location.get('BuildingNumber', '')} {location.get('StreetName', '')}\n")
            f.write(f"City: {location.get('TownCity', '')}\n")
            f.write(f"Postcode: {location.get('Postcode', '')}\n")
            
            # Mortgage info if available
            if mortgage_info:
                f.write(f"\nMORTGAGE INFORMATION:\n")
                financial = mortgage_info.get('FinancialTerms', {})
                f.write(f"Loan Amount: £{financial.get('OriginalLoan', 0):,.2f}\n")
                f.write(f"Interest Rate: {financial.get('OriginalLendingRate', 0):.2%}\n")
                f.write(f"LTV Ratio: {financial.get('LoanToValueRatio', 0):.2%}\n")
            
            f.write(f"\nReport generated successfully.\n")
        
        print(f"Report saved to: {report_file}")
        return report_file
        
    except Exception as e:
        print(f"Error generating property report: {e}")
        return None
