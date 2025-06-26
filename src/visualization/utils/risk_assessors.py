"""
Risk assessment utilities for the visualization system.

This module provides functions for calculating and assessing various types of risks
including flood risk, mortgage risk, and combined risk scenarios.
"""

from typing import Dict, Any, Optional, Union
import math


class RiskAssessor:
    """Utility class for risk assessment calculations."""
    
    # Risk level thresholds
    FLOOD_DEPTH_THRESHOLDS = {
        'very_low': 0.0,
        'low': 0.1,
        'medium': 0.5,
        'high': 1.0,
        'very_high': 2.0
    }
    
    LTV_RISK_THRESHOLDS = {
        'low': 0.6,
        'moderate': 0.8,
        'high': 0.95,
        'critical': 1.0
    }
    
    
    
    @classmethod
    def assess_flood_risk_level(cls, flood_depth: float) -> str:
        """
        Assess flood risk level based on flood depth.
        
        Args:
            flood_depth: Flood depth in meters
            
        Returns:
            Risk level string
        """
        if flood_depth is None or flood_depth < 0:
            return "Unknown"
        
        if flood_depth <= cls.FLOOD_DEPTH_THRESHOLDS['very_low']:
            return "Very Low"
        elif flood_depth <= cls.FLOOD_DEPTH_THRESHOLDS['low']:
            return "Low"
        elif flood_depth <= cls.FLOOD_DEPTH_THRESHOLDS['medium']:
            return "Medium"
        elif flood_depth <= cls.FLOOD_DEPTH_THRESHOLDS['high']:
            return "High"
        else:
            return "Very High"
    
    @classmethod
    def assess_ltv_risk_level(cls, ltv_ratio: float) -> str:
        """
        Assess loan-to-value risk level.
        
        Args:
            ltv_ratio: LTV ratio (0-1 or 0-100)
            
        Returns:
            Risk level string
        """
        if ltv_ratio is None:
            return "Unknown"
        
        # Normalize to 0-1 if needed
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100
        
        if ltv_ratio <= cls.LTV_RISK_THRESHOLDS['low']:
            return "Low"
        elif ltv_ratio <= cls.LTV_RISK_THRESHOLDS['moderate']:
            return "Moderate"
        elif ltv_ratio <= cls.LTV_RISK_THRESHOLDS['high']:
            return "High"
        else:
            return "Critical"
    
    @classmethod
    def assess_mortgage_risk(cls, flood_risk_level: str, mortgage_value: float, 
                           loan_amount: float, ltv_ratio: float) -> str:
        """
        Generate a comprehensive mortgage risk assessment.
        
        Args:
            flood_risk_level: The flood risk level for the property
            mortgage_value: The calculated value of the mortgage
            loan_amount: The original loan amount
            ltv_ratio: Loan-to-value ratio
            
        Returns:
            Risk assessment string
        """
        # Check for high flood risk
        if flood_risk_level in ['High', 'Very High']:
            return "High Risk - Significant flood exposure threatening mortgage value"
        
        # Check for negative mortgage value
        if mortgage_value is not None and loan_amount is not None and mortgage_value < 0:
            negative_pct = abs(mortgage_value) / loan_amount if loan_amount > 0 else 0
            
            if negative_pct > 0.1:
                return "Critical Risk - Mortgage value severely impacted"
            elif negative_pct > 0.05:
                return "High Risk - Significant negative impact on mortgage value"
            elif negative_pct > 0.02:
                return "Moderate Risk - Some negative impact on mortgage value"
        
        # Check LTV combined with flood risk
        if ltv_ratio is not None:
            if ltv_ratio > 0.8 and flood_risk_level in ['Medium', 'High', 'Very High']:
                return "High Risk - High LTV with flood exposure"
            elif ltv_ratio > 0.7 and flood_risk_level in ['Medium', 'High']:
                return "Moderate Risk - Elevated LTV with some flood exposure"
        
        # Default assessments based on flood risk
        if flood_risk_level == 'Medium':
            return "Moderate Risk - Some flood exposure"
        elif flood_risk_level == 'Low':
            return "Low Risk - Limited flood exposure"
        else:
            return "Minimal Risk - No significant flood impact identified"
    
    @classmethod
    def calculate_combined_risk_score(cls, flood_risk_level: str, ltv_ratio: float, 
                                    property_age: Optional[int] = None,
                                    construction_type: Optional[str] = None) -> float:
        """
        Calculate a combined risk score considering multiple factors.
        
        Args:
            flood_risk_level: Flood risk level string
            ltv_ratio: Loan-to-value ratio
            property_age: Age of property in years (optional)
            construction_type: Type of construction (optional)
            
        Returns:
            Combined risk score (0-10 scale)
        """
        # Base flood risk score
        flood_scores = {
            'Very Low': 1,
            'Very low': 1,
            'Low': 2,
            'Medium': 4,
            'High': 7,
            'Very High': 9,
            'Very high': 9,
            'Unknown': 3
        }
        
        flood_score = flood_scores.get(flood_risk_level, 3)
        
        # LTV risk multiplier
        ltv_multiplier = 1.0
        if ltv_ratio is not None:
            if ltv_ratio > 1:  # Normalize if needed
                ltv_ratio = ltv_ratio / 100
            
            if ltv_ratio > 0.95:
                ltv_multiplier = 2.0
            elif ltv_ratio > 0.8:
                ltv_multiplier = 1.5
            elif ltv_ratio > 0.6:
                ltv_multiplier = 1.2
        
        # Property age factor
        age_factor = 1.0
        if property_age is not None:
            if property_age > 100:
                age_factor = 1.3
            elif property_age > 50:
                age_factor = 1.1
        
        # Construction type factor
        construction_factor = 1.0
        if construction_type:
            construction_risks = {
                'timber': 1.3,
                'wood': 1.3,
                'brick': 1.0,
                'concrete': 0.9,
                'steel': 0.8
            }
            construction_factor = construction_risks.get(
                construction_type.lower(), 1.0
            )
        
        # Calculate combined score
        combined_score = flood_score * ltv_multiplier * age_factor * construction_factor
        
        # Cap at 10
        return min(combined_score, 10.0)
    
    @classmethod
    def assess_property_vulnerability(cls, ground_elevation: float, 
                                   flood_level: float,
                                   distance_to_water: Optional[float] = None) -> Dict[str, Any]:
        """
        Assess property vulnerability to flooding.
        
        Args:
            ground_elevation: Property elevation in meters
            flood_level: Projected flood level in meters
            distance_to_water: Distance to nearest water body in km (optional)
            
        Returns:
            Dictionary with vulnerability assessment
        """
        if ground_elevation is None or flood_level is None:
            return {
                'flood_depth': None,
                'risk_level': 'Unknown',
                'vulnerability_score': None,
                'recommendations': ['Insufficient data for assessment']
            }
        
        # Calculate flood depth
        flood_depth = max(0, flood_level - ground_elevation)
        
        # Assess risk level
        risk_level = cls.assess_flood_risk_level(flood_depth)
        
        # Calculate vulnerability score (0-100)
        vulnerability_score = min(100, (flood_depth * 30) + (50 if flood_depth > 0 else 0))
        
        # Distance factor
        if distance_to_water is not None and distance_to_water < 1.0:
            vulnerability_score += 20
        
        # Generate recommendations
        recommendations = cls._generate_recommendations(flood_depth, risk_level)
        
        return {
            'flood_depth': flood_depth,
            'risk_level': risk_level,
            'vulnerability_score': min(100, vulnerability_score),
            'recommendations': recommendations
        }
    
    @classmethod
    def calculate_value_at_risk(cls, property_value: float, risk_level: str,
                              flood_depth: Optional[float] = None) -> float:
        """
        Calculate the financial value at risk due to flooding.
        
        Args:
            property_value: Total property value
            risk_level: Flood risk level string
            flood_depth: Flood depth in meters (optional for more precise calculation)
            
        Returns:
            Value at risk amount
        """
        if property_value is None or property_value <= 0:
            return 0.0
        
        # Base risk percentages by level
        risk_percentages = {
            'Very Low': 0.01,
            'Very low': 0.01,
            'Low': 0.05,
            'Medium': 0.15,
            'High': 0.35,
            'Very High': 0.60,
            'Very high': 0.60,
            'Unknown': 0.10
        }
        
        base_percentage = risk_percentages.get(risk_level, 0.10)
        
        # Adjust based on flood depth if available
        if flood_depth is not None and flood_depth > 0:
            # More precise calculation based on depth
            if flood_depth > 2.0:
                depth_factor = 0.8  # 80% of value at risk for severe flooding
            elif flood_depth > 1.0:
                depth_factor = 0.5  # 50% for significant flooding
            elif flood_depth > 0.5:
                depth_factor = 0.25  # 25% for moderate flooding
            else:
                depth_factor = 0.1   # 10% for minor flooding
            
            # Use the higher of the two estimates
            final_percentage = max(base_percentage, depth_factor)
        else:
            final_percentage = base_percentage
        
        return property_value * final_percentage
    
    @classmethod
    def assess_gauge_reliability(cls, operational_status: str, 
                               last_maintenance: Optional[str] = None,
                               data_frequency: Optional[str] = None) -> Dict[str, Any]:
        """
        Assess the reliability of a flood gauge.
        
        Args:
            operational_status: Current operational status
            last_maintenance: Date of last maintenance (optional)
            data_frequency: Frequency of data collection (optional)
            
        Returns:
            Dictionary with reliability assessment
        """
        # Base reliability score based on operational status
        status_scores = {
            'Fully operational': 95,
            'Maintenance required': 70,
            'Temporarily offline': 30,
            'Decommissioned': 0,
            'Unknown': 50
        }
        
        reliability_score = status_scores.get(operational_status, 50)
        
        # Adjust for data frequency
        if data_frequency:
            frequency_adjustments = {
                'real-time': 0,
                'hourly': -5,
                'daily': -15,
                'weekly': -30,
                'monthly': -50
            }
            
            for freq, adjustment in frequency_adjustments.items():
                if freq in data_frequency.lower():
                    reliability_score += adjustment
                    break
        
        # Determine reliability category
        if reliability_score >= 90:
            category = "Highly Reliable"
        elif reliability_score >= 70:
            category = "Reliable"
        elif reliability_score >= 50:
            category = "Moderately Reliable"
        elif reliability_score >= 30:
            category = "Low Reliability"
        else:
            category = "Unreliable"
        
        return {
            'reliability_score': max(0, min(100, reliability_score)),
            'category': category,
            'operational_status': operational_status
        }
    
    @classmethod
    def calculate_distance_risk_factor(cls, distance_km: float) -> float:
        """
        Calculate risk factor based on distance to flood source.
        
        Args:
            distance_km: Distance in kilometers
            
        Returns:
            Risk factor (0-1, where 1 is highest risk)
        """
        if distance_km is None or distance_km < 0:
            return 0.5  # Default moderate risk
        
        # Risk decreases exponentially with distance
        # Maximum risk within 0.1 km, negligible risk beyond 5 km
        if distance_km <= 0.1:
            return 1.0
        elif distance_km <= 0.5:
            return 0.8
        elif distance_km <= 1.0:
            return 0.6
        elif distance_km <= 2.0:
            return 0.4
        elif distance_km <= 5.0:
            return 0.2
        else:
            return 0.1
    
    @classmethod
    def _generate_recommendations(cls, flood_depth: float, risk_level: str) -> list:
        """
        Generate recommendations based on flood risk assessment.
        
        Args:
            flood_depth: Flood depth in meters
            risk_level: Risk level string
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if risk_level in ['High', 'Very High']:
            recommendations.extend([
                "Consider flood insurance if not already covered",
                "Implement flood-resistant modifications",
                "Develop an emergency evacuation plan",
                "Install flood barriers or waterproofing"
            ])
            
            if flood_depth > 1.0:
                recommendations.extend([
                    "Consider relocating utilities to higher floors",
                    "Install flood vents in foundation walls",
                    "Elevate critical equipment and furnaces"
                ])
        
        elif risk_level == 'Medium':
            recommendations.extend([
                "Review flood insurance options",
                "Monitor local flood warnings",
                "Prepare emergency supplies",
                "Consider minor flood-proofing measures"
            ])
        
        elif risk_level == 'Low':
            recommendations.extend([
                "Stay informed about local flood risks",
                "Maintain awareness of seasonal variations",
                "Consider basic emergency preparedness"
            ])
        
        else:  # Very Low or Unknown
            recommendations.extend([
                "Monitor changes in local flood risk",
                "Stay informed about climate projections"
            ])
        
        return recommendations
    
    @classmethod
    def get_risk_color(cls, risk_level: str) -> str:
        """
        Get color code for flood risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Color string for visualization
        """
        risk_colors = {
            'Very Low': 'green',
            'Very low': 'green',
            'Low': 'lightgreen',
            'Medium': 'orange',
            'High': 'red',
            'Very High': 'darkred',
            'Very high': 'darkred',
            'Unknown': 'blue',
            'N/A': 'gray'
        }
        return risk_colors.get(risk_level, 'blue')  # Default blue
    
    @classmethod
    def get_risk_icon(cls, risk_level: str) -> str:
        """
        Get icon name for flood risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Icon name string
        """
        risk_icons = {
            'Very Low': 'check-circle',
            'Very low': 'check-circle',
            'Low': 'info-circle',
            'Medium': 'exclamation-triangle',
            'High': 'exclamation-circle',
            'Very High': 'times-circle',
            'Very high': 'times-circle',
            'Unknown': 'question-circle'
        }
        return risk_icons.get(risk_level, 'question-circle')
    
    @classmethod
    def get_ltv_color(cls, ltv_ratio: float) -> str:
        """
        Get color code for LTV ratio.
        
        Args:
            ltv_ratio: LTV ratio (0-1 or 0-100)
            
        Returns:
            Color string for visualization
        """
        if ltv_ratio is None:
            return 'gray'
        
        # Normalize to 0-1 if needed
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100
        
        if ltv_ratio <= 0.6:
            return 'green'
        elif ltv_ratio <= 0.8:
            return 'yellow'
        elif ltv_ratio <= 0.95:
            return 'orange'
        else:
            return 'red'
    
    
    @classmethod
    def calculate_insurance_premium_factor(cls, risk_level: str, 
                                         property_value: float,
                                         flood_depth: Optional[float] = None) -> float:
        """
        Calculate an estimated insurance premium factor.
        
        Args:
            risk_level: Flood risk level
            property_value: Property value
            flood_depth: Flood depth in meters (optional)
            
        Returns:
            Estimated annual premium as percentage of property value
        """
        # Base premium rates by risk level (as percentage of property value)
        base_rates = {
            'Very Low': 0.001,   # 0.1%
            'Very low': 0.001,
            'Low': 0.002,        # 0.2%
            'Medium': 0.005,     # 0.5%
            'High': 0.015,       # 1.5%
            'Very High': 0.035,  # 3.5%
            'Very high': 0.035,
            'Unknown': 0.005
        }
        
        base_rate = base_rates.get(risk_level, 0.005)
        
        # Adjust for specific flood depth
        if flood_depth is not None and flood_depth > 0:
            depth_multiplier = 1 + (flood_depth * 0.5)  # 50% increase per meter
            base_rate *= depth_multiplier
        
        # Cap at reasonable maximum (10% of property value)
        return min(base_rate, 0.10)


# Convenience functions for backward compatibility
def assess_mortgage_risk_summary(flood_risk_level: str, mortgage_value: float, 
                               loan_amount: float, ltv_ratio: float) -> str:
    """Generate mortgage risk summary (backward compatibility)."""
    return RiskAssessor.assess_mortgage_risk(
        flood_risk_level, mortgage_value, loan_amount, ltv_ratio
    )

def calculate_combined_risk(flood_risk: str, ltv_ratio: float) -> float:
    """Calculate combined risk score (backward compatibility)."""
    return RiskAssessor.calculate_combined_risk_score(flood_risk, ltv_ratio)