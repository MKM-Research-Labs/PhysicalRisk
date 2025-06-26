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

# src/utilities/page_15_data_summary.py

"""
Page 15: Data Summary & Report Metadata
Handles data completeness analysis and report generation metadata.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class DataSummaryPage(BasePage):
    """Generates data summary and report metadata page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate data summary page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Data Summary & Report Metadata", self.styles['SectionHeader']))
            
            # DATA COMPLETENESS ANALYSIS
            elements.append(Paragraph("Data Completeness Analysis", self.styles['SubSectionHeader']))
            
            completeness_stats = self._analyze_data_completeness(property_data, mortgage_data)
            
            completeness_data = [["Data Section", "Fields Used", "Total Available", "Completeness"]]
            
            total_used = 0
            total_available = 0
            
            for section, stats in completeness_stats.items():
                used = stats['used']
                available = stats['available']
                percentage = stats['percentage']
                
                total_used += used
                total_available += available
                
                completeness_data.append([
                    section,
                    str(used),
                    str(available),
                    f"{percentage:.1f}%"
                ])
            
            # Overall totals
            overall_percentage = (total_used / total_available * 100) if total_available > 0 else 0
            completeness_data.append(["", "", "", ""])
            completeness_data.append([
                "OVERALL TOTAL",
                str(total_used),
                str(total_available),
                f"{overall_percentage:.1f}%"
            ])
            
            completeness_table = Table(completeness_data, colWidths=self.table_widths['four_col'])
            completeness_table.setStyle(self.table_styles['standard'])
            elements.append(completeness_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # DATA QUALITY ASSESSMENT
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Data Quality Assessment", self.styles['SubSectionHeader']))
            
            quality_assessment = self._assess_data_quality(overall_percentage, completeness_stats)
            
            quality_data = [["Quality Metric", "Assessment"]]
            for metric, assessment in quality_assessment.items():
                quality_data.append([metric, assessment])
            
            quality_table = Table(quality_data, colWidths=self.table_widths['two_col'])
            quality_table.setStyle(self.table_styles['standard'])
            elements.append(quality_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # REPORT GENERATION METADATA
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Report Generation Metadata", self.styles['SubSectionHeader']))
            
            metadata = self._generate_report_metadata(property_data, mortgage_data)
            
            metadata_data = [["Metadata Item", "Value"]]
            for item, value in metadata.items():
                metadata_data.append([item, value])
            
            metadata_table = Table(metadata_data, colWidths=self.table_widths['two_col'])
            metadata_table.setStyle(self.table_styles['standard'])
            elements.append(metadata_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RECOMMENDATIONS FOR DATA IMPROVEMENT
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Data Improvement Recommendations", self.styles['SubSectionHeader']))
            
            recommendations = self._generate_data_recommendations(completeness_stats)
            
            if recommendations:
                rec_data = [["Priority", "Recommendation"]]
                for i, recommendation in enumerate(recommendations, 1):
                    rec_data.append([f"Priority {i}", recommendation])
                
                rec_table = Table(rec_data, colWidths=self.table_widths['two_col'])
                rec_table.setStyle(self.table_styles['standard'])
                elements.append(rec_table)
            else:
                elements.append(Paragraph("No specific data improvement recommendations at this time.", self.styles['Normal']))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating data summary: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _analyze_data_completeness(self, property_data: Dict[str, Any], 
                                  mortgage_data: Dict[str, Any] = None) -> Dict[str, Dict]:
        """Analyze data completeness across all sections."""
        
        def count_fields(data, section_name=""):
            """Recursively count fields in a data structure."""
            if not isinstance(data, dict):
                return 0, 0
            
            total_fields = 0
            populated_fields = 0
            
            for key, value in data.items():
                if isinstance(value, dict):
                    sub_total, sub_populated = count_fields(value)
                    total_fields += sub_total
                    populated_fields += sub_populated
                else:
                    total_fields += 1
                    if value is not None and value != '':
                        populated_fields += 1
            
            return total_fields, populated_fields
        
        completeness_stats = {}
        
        # Analyze property data sections
        property_sections = [
            'PropertyHeader', 'ProtectionMeasures', 'EnergyPerformance', 
            'History', 'TransactionHistory'
        ]
        
        for section in property_sections:
            if section in property_data:
                total, populated = count_fields(property_data[section])
                if total > 0:
                    completeness_stats[section] = {
                        'used': populated,
                        'available': total,
                        'percentage': (populated / total) * 100
                    }
        
        # Analyze mortgage data if available
        if mortgage_data:
            total, populated = count_fields(mortgage_data)
            if total > 0:
                completeness_stats['Mortgage Data'] = {
                    'used': populated,
                    'available': total,
                    'percentage': (populated / total) * 100
                }
        
        return completeness_stats
    
    def _assess_data_quality(self, overall_percentage: float, 
                           completeness_stats: Dict[str, Dict]) -> Dict[str, str]:
        """Assess overall data quality."""
        
        assessment = {}
        
        # Overall completeness assessment
        if overall_percentage >= 90:
            assessment["Overall Completeness"] = "Excellent - Very comprehensive dataset"
        elif overall_percentage >= 75:
            assessment["Overall Completeness"] = "Good - Most key data points available"
        elif overall_percentage >= 60:
            assessment["Overall Completeness"] = "Fair - Adequate for basic analysis"
        elif overall_percentage >= 40:
            assessment["Overall Completeness"] = "Limited - Some key data missing"
        else:
            assessment["Overall Completeness"] = "Poor - Significant data gaps present"
        
        # Identify best and worst sections
        if completeness_stats:
            best_section = max(completeness_stats.items(), key=lambda x: x[1]['percentage'])
            worst_section = min(completeness_stats.items(), key=lambda x: x[1]['percentage'])
            
            assessment["Best Data Section"] = f"{best_section[0]} ({best_section[1]['percentage']:.1f}%)"
            assessment["Weakest Data Section"] = f"{worst_section[0]} ({worst_section[1]['percentage']:.1f}%)"
        
        # Data reliability assessment
        critical_sections = ['PropertyHeader', 'FinancialTerms', 'CurrentStatus']
        critical_completeness = []
        
        for section in critical_sections:
            if section in completeness_stats:
                critical_completeness.append(completeness_stats[section]['percentage'])
        
        if critical_completeness:
            avg_critical = sum(critical_completeness) / len(critical_completeness)
            if avg_critical >= 80:
                assessment["Critical Data Reliability"] = "High - Key sections well populated"
            elif avg_critical >= 60:
                assessment["Critical Data Reliability"] = "Medium - Some critical gaps"
            else:
                assessment["Critical Data Reliability"] = "Low - Missing critical information"
        
        return assessment
    
    def _generate_report_metadata(self, property_data: Dict[str, Any], 
                                mortgage_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate report metadata."""
        
        metadata = {}
        
        # Report generation info
        metadata["Report Generated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        metadata["Report Generator"] = "MKM Research Labs Property Report System v2.0"
        metadata["Report Type"] = "Comprehensive Property Analysis"
        
        # Property identification
        try:
            property_id = property_data['PropertyHeader']['Header']['PropertyID']
            metadata["Property ID"] = property_id
        except (KeyError, TypeError):
            metadata["Property ID"] = "Unknown"
        
        try:
            uprn = property_data['PropertyHeader']['Header']['UPRN']
            metadata["UPRN"] = str(uprn)
        except (KeyError, TypeError):
            metadata["UPRN"] = "Not available"
        
        # Data sources
        data_sources = ["Property Portfolio Database"]
        if mortgage_data:
            data_sources.append("Mortgage Management System")
            
            # Try to get mortgage ID
            try:
                mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
                mortgage_id = mortgage_info['Header']['MortgageID']
                metadata["Mortgage ID"] = mortgage_id
            except (KeyError, TypeError):
                pass
        
        metadata["Data Sources"] = ", ".join(data_sources)
        
        # Report scope
        if mortgage_data:
            metadata["Analysis Scope"] = "Property + Mortgage Comprehensive Analysis"
        else:
            metadata["Analysis Scope"] = "Property-Only Analysis"
        
        # Data currency
        try:
            last_updated = property_data['PropertyHeader']['Header']['LastUpdated']
            metadata["Data Last Updated"] = last_updated
        except (KeyError, TypeError):
            metadata["Data Last Updated"] = "Unknown"
        
        return metadata
    
    def _generate_data_recommendations(self, completeness_stats: Dict[str, Dict]) -> List[str]:
        """Generate recommendations for improving data completeness."""
        
        recommendations = []
        
        # Identify sections with low completeness
        for section, stats in completeness_stats.items():
            percentage = stats['percentage']
            
            if percentage < 50:
                recommendations.append(
                    f"Improve {section} data collection - currently only {percentage:.1f}% complete"
                )
            elif percentage < 75:
                recommendations.append(
                    f"Enhance {section} data quality - opportunity to improve from {percentage:.1f}%"
                )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Maintain current high data quality standards")
        else:
            recommendations.append("Implement data validation procedures for incomplete sections")
            recommendations.append("Regular data quality audits recommended")
        
        return recommendations[:5]  # Limit to top 5 recommendations