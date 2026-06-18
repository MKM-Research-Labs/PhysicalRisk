# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Data-completeness, quality, metadata and recommendation analysis mixin."""

from datetime import datetime
from typing import Any, Dict, List


class _DataAnalysisMixin:
    """Completeness/quality analysis and report-metadata helpers."""

    def _analyze_data_completeness(self, property_data: Dict[str, Any],
                                  rloan_data: Dict[str, Any] = None) -> Dict[str, Dict]:
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
        if rloan_data:
            total, populated = count_fields(rloan_data)
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
                                rloan_data: Dict[str, Any] = None) -> Dict[str, str]:
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
        if rloan_data:
            data_sources.append("Mortgage Management System")

            # Try to get mortgage ID
            try:
                rloan_info = rloan_data.get('RLoan', rloan_data)
                mortgage_id = rloan_info['Header']['RLoanID']
                metadata["Mortgage ID"] = mortgage_id
            except (KeyError, TypeError):
                pass

        metadata["Data Sources"] = ", ".join(data_sources)

        # Report scope
        if rloan_data:
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
