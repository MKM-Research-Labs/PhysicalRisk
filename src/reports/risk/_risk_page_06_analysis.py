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

"""Property-value/risk analysis helpers for the Risk Details page."""

from typing import Any, Dict


class _RiskPropertyAnalysisMixin:
    """Portfolio value/risk aggregation (mixed into RiskPropertyDetailsPage)."""

    def _analyze_property_values(self, property_risk: Dict[str, Any]) -> Dict[str, float]:
        """Analyze property values across the portfolio."""
        all_values = []
        at_risk_values = []

        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            risk_level = prop_data.get('risk_level', 'Unknown')

            all_values.append(prop_value)
            if risk_level in ['High', 'Medium']:
                at_risk_values.append(prop_value)

        return {
            'min_value': min(all_values) if all_values else 0,
            'max_value': max(all_values) if all_values else 0,
            'portfolio_avg_value': sum(all_values) / len(all_values) if all_values else 0,
            'avg_at_risk_value': sum(at_risk_values) / len(at_risk_values) if at_risk_values else 0
        }

    def _categorize_property_values(self, property_risk: Dict[str, Any]) -> Dict[str, Dict]:
        """Categorize properties by value ranges."""
        categories = {
            "Under £500K": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "£500K-£1M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "£1M-£2M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "£2M-£5M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "Over £5M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0}
        }

        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            risk_level = prop_data.get('risk_level', 'Unknown')
            value_at_risk = prop_data.get('value_at_risk', 0) or 0

            # Determine value category
            if prop_value < 500000:
                category = "Under £500K"
            elif prop_value < 1000000:
                category = "£500K-£1M"
            elif prop_value < 2000000:
                category = "£1M-£2M"
            elif prop_value < 5000000:
                category = "£2M-£5M"
            else:
                category = "Over £5M"

            categories[category]["total_count"] += 1
            if risk_level in ['High', 'Medium']:
                categories[category]["at_risk_count"] += 1
                categories[category]["total_value_at_risk"] += value_at_risk

        return categories

    def _analyze_risk_distribution(self, property_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk distribution across property segments."""
        segments = {
            "High Value (>£1M)": {"total": 0, "at_risk": 0, "total_depth": 0},
            "Medium Value (£500K-£1M)": {"total": 0, "at_risk": 0, "total_depth": 0},
            "Lower Value (<£500K)": {"total": 0, "at_risk": 0, "total_depth": 0}
        }

        high_value_at_risk = 0
        high_value_total = 0
        low_value_at_risk = 0
        low_value_total = 0

        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            risk_level = prop_data.get('risk_level', 'Unknown')
            flood_depth = prop_data.get('flood_depth', 0) or 0

            # Determine segment
            if prop_value >= 1000000:
                segment = "High Value (>£1M)"
                high_value_total += 1
                if risk_level in ['High', 'Medium']:
                    high_value_at_risk += 1
            elif prop_value >= 500000:
                segment = "Medium Value (£500K-£1M)"
            else:
                segment = "Lower Value (<£500K)"
                low_value_total += 1
                if risk_level in ['High', 'Medium']:
                    low_value_at_risk += 1

            segments[segment]["total"] += 1
            if risk_level in ['High', 'Medium']:
                segments[segment]["at_risk"] += 1
                segments[segment]["total_depth"] += flood_depth

        # Calculate average depths
        for segment_data in segments.values():
            at_risk_count = segment_data["at_risk"]
            segment_data["avg_depth"] = (
                segment_data["total_depth"] / at_risk_count if at_risk_count > 0 else 0
            )

        return {
            'segments': segments,
            'high_risk_percentage': (high_value_at_risk / high_value_total * 100) if high_value_total > 0 else 0,
            'low_risk_percentage': (low_value_at_risk / low_value_total * 100) if low_value_total > 0 else 0
        }

    def _calculate_portfolio_impact(self, property_risk: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall portfolio impact metrics."""
        total_properties = len(property_risk)
        properties_at_risk = 0
        total_portfolio_value = 0
        total_value_at_risk = 0

        for prop_data in property_risk.values():
            risk_level = prop_data.get('risk_level', 'Unknown')
            prop_value = prop_data.get('property_value', 0) or 0
            value_at_risk = prop_data.get('value_at_risk', 0) or 0

            total_portfolio_value += prop_value
            total_value_at_risk += value_at_risk

            if risk_level in ['High', 'Medium']:
                properties_at_risk += 1

        return {
            'total_properties': total_properties,
            'properties_at_risk': properties_at_risk,
            'portfolio_risk_percentage': (properties_at_risk / total_properties * 100) if total_properties > 0 else 0,
            'total_portfolio_value': total_portfolio_value,
            'total_value_at_risk': total_value_at_risk,
            'value_risk_percentage': (total_value_at_risk / total_portfolio_value * 100) if total_portfolio_value > 0 else 0,
            'avg_risk_per_property': total_value_at_risk / total_properties if total_properties > 0 else 0
        }
