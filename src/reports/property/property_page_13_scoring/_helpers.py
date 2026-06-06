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

"""Key-factor, recommendation, and monitoring helpers for page 13 scoring."""

from typing import Dict, List


def identify_key_factors(categories: Dict[str, Dict]) -> Dict[str, str]:
    """Identify the highest risk factors."""
    key_factors = {}

    # Sort by risk score
    sorted_categories = sorted(categories.items(), key=lambda x: x[1]['score'], reverse=True)

    # Take top 3 highest risk categories
    for i, (category, details) in enumerate(sorted_categories[:3]):
        if details['score'] >= 4:
            key_factors[f"High Risk Factor {i+1}"] = f"{category}: {details['impact']}"
        elif details['score'] >= 3:
            key_factors[f"Medium Risk Factor {i+1}"] = f"{category}: {details['impact']}"

    return key_factors


def generate_recommendations(categories: Dict[str, Dict], overall_score: float) -> List[str]:
    """Generate risk management recommendations."""
    recommendations = []

    # High-level recommendations based on overall score
    if overall_score >= 4:
        recommendations.append("URGENT: Immediate comprehensive risk mitigation required")
    elif overall_score >= 3:
        recommendations.append("HIGH PRIORITY: Implement targeted risk reduction measures")
    elif overall_score >= 2:
        recommendations.append("MODERATE: Consider preventive risk management strategies")
    else:
        recommendations.append("LOW: Maintain current risk management practices")

    # Specific recommendations based on individual categories
    for category, details in categories.items():
        if details['score'] >= 4:
            if 'Flood' in category:
                recommendations.append("Install comprehensive flood protection measures")
            elif 'Payment' in category:
                recommendations.append("Address payment performance issues immediately")
            elif 'LTV' in category:
                recommendations.append("Consider reducing loan-to-value ratio")
            elif 'Credit' in category:
                recommendations.append("Work on improving credit profile")

    return recommendations[:5]  # Limit to top 5 recommendations


def generate_monitoring_schedule(overall_score: float) -> Dict[str, str]:
    """Generate appropriate monitoring schedule based on risk level."""
    if overall_score >= 4:
        return {
            'Overall risk review': 'Monthly',
            'Payment performance': 'Weekly',
            'Property condition': 'Quarterly',
            'Market conditions': 'Monthly',
            'Insurance coverage': 'Quarterly'
        }
    elif overall_score >= 3:
        return {
            'Overall risk review': 'Quarterly',
            'Payment performance': 'Monthly',
            'Property condition': 'Semi-annually',
            'Market conditions': 'Quarterly',
            'Insurance coverage': 'Annually'
        }
    else:
        return {
            'Overall risk review': 'Annually',
            'Payment performance': 'Quarterly',
            'Property condition': 'Annually',
            'Market conditions': 'Semi-annually',
            'Insurance coverage': 'Annually'
        }
