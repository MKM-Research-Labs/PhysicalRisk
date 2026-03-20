# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Mortgage risk circles and LTV indicator drawing functions."""

import logging
from typing import Any, Dict, List

import folium

from ...utils import ColorSchemes, DataFormatter
from .popup import create_mortgage_circle_popup

logger = logging.getLogger(__name__)


def get_mortgage_risk_color(mortgage_info: Dict[str, Any],
                            mortgage_risk_info,
                            property_flood_info: Dict[str, Any]) -> str:
    """
    Determine the appropriate color for a mortgage risk circle.

    Args:
        mortgage_info: Basic mortgage information
        mortgage_risk_info: Detailed risk analysis (or None)
        property_flood_info: Property flood risk information

    Returns:
        Color string for the circle
    """
    if mortgage_risk_info:
        flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
        return ColorSchemes.get_flood_risk_color(flood_risk_level)

    if property_flood_info:
        risk_level = property_flood_info.get('risk_level', 'Unknown')
        return ColorSchemes.get_flood_risk_color(risk_level)

    ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
    if ltv_ratio:
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100
        return ColorSchemes.get_ltv_risk_color(ltv_ratio)

    return '#2196F3'  # Blue


def add_mortgage_risk_circles(feature_group: folium.FeatureGroup,
                               mortgage_locations: List[Dict[str, Any]],
                               circle_opacity: float,
                               max_circle_radius: int):
    """
    Add mortgage risk circles to show loan amounts and risk levels.

    Args:
        feature_group: Folium FeatureGroup to add circles to
        mortgage_locations: List of mortgage location data
        circle_opacity: Fill opacity for the circles
        max_circle_radius: Maximum radius in metres
    """
    loan_amounts = []
    for location in mortgage_locations:
        mortgage_info = location['mortgage_info']
        loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
        if loan_amount and loan_amount > 0:
            loan_amounts.append(float(loan_amount))

    if not loan_amounts:
        logger.warning("No valid loan amounts found for risk circles")
        return

    min_loan = min(loan_amounts)
    max_loan = max(loan_amounts)
    loan_range = max_loan - min_loan if max_loan > min_loan else 1

    circles_added = 0

    for location in mortgage_locations:
        try:
            mortgage_info = location['mortgage_info']
            mortgage_risk_info = location['mortgage_risk_info']
            property_flood_info = location['property_flood_info']

            loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))

            if not loan_amount or loan_amount <= 0:
                continue

            normalized_loan = (float(loan_amount) - min_loan) / loan_range
            radius = 100 + (normalized_loan * (max_circle_radius - 100))

            color = get_mortgage_risk_color(mortgage_info, mortgage_risk_info, property_flood_info)
            popup_content = create_mortgage_circle_popup(location)

            circle = folium.Circle(
                location=[location['lat'], location['lon']],
                radius=radius,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=circle_opacity,
                weight=2,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"Mortgage: {DataFormatter.format_currency(loan_amount)}"
            )

            circle.add_to(feature_group)
            circles_added += 1

        except Exception as e:
            logger.warning(f"Error creating mortgage circle for {location.get('property_id', 'Unknown')}: {e}")
            continue

    logger.info(f"Added {circles_added} mortgage risk circles")


def add_ltv_indicators(feature_group: folium.FeatureGroup,
                       mortgage_locations: List[Dict[str, Any]]):
    """
    Add LTV ratio indicators as small markers.

    Args:
        feature_group: Folium FeatureGroup to add indicators to
        mortgage_locations: List of mortgage location data
    """
    indicators_added = 0

    for location in mortgage_locations:
        try:
            mortgage_info = location['mortgage_info']

            ltv_ratio = mortgage_info.get('OriginalLTV',
                        mortgage_info.get('CurrentLTV', 0))

            if not ltv_ratio:
                continue

            if ltv_ratio > 1:
                ltv_ratio = ltv_ratio / 100

            if ltv_ratio < 0.8:
                continue

            color = ColorSchemes.get_ltv_risk_color(ltv_ratio)

            indicator = folium.CircleMarker(
                location=[location['lat'], location['lon']],
                radius=8,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.9,
                weight=2,
                tooltip=f"High LTV: {DataFormatter.format_percentage(ltv_ratio)}"
            )

            indicator.add_to(feature_group)
            indicators_added += 1

        except Exception as e:
            logger.warning(f"Error creating LTV indicator: {e}")
            continue

    logger.info(f"Added {indicators_added} LTV indicators")
