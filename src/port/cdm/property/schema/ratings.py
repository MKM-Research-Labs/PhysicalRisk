# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
ProtectionMeasures.RiskAssessment — assessment outcomes and rating metadata.

Covers §2.1 of the revised Property CDM. Insurance and governing-body ratings
share a parallel structure. InsurancePremium is intentionally not here — it is
financial information and lives in schema/transactions.py.
"""

RATINGS_SCHEMA = {
    "InsuranceBodyRatings": {
        "InsuranceRating": {
            "type": "string",
            "description": "Risk rating assigned by the local insurance market, insurer or underwriting body"
        },
        "InsuranceDate": {
            "type": "date",
            "description": "Date the insurance rating was issued"
        },
        "InsuranceRatingVersion": {
            "type": "string",
            "description": "Version identifier of the insurance rating scheme"
        },
        "InsuranceRatingBody": {
            "type": "string",
            "description": "Name of insurer, broker, pool or local insurance authority that assigned the rating"
        }
    },
    "GoverningBodyRatings": {
        "BRIRating": {
            "type": "menu",
            "options": ["AA", "AA+", "A", "A+", "B", "B+", "NR"],
            "description": "Overall BRI letter grade (weakest-of applicable hazard sub-ratings; '+' suffix indicates operational continuity measures also met)"
        },
        "BRIScore": {
            "type": "decimal",
            "description": "Overall BRI weighted score (0.0-1.0); diagnostic value alongside BRIRating"
        },
        "BRIFloodRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for flood resilience (N/A when FloodHazardClass is None)"
        },
        "BRIFloodScore": {
            "type": "decimal",
            "description": "BRI sub-score for flood resilience (0.0-1.0); null when FloodHazardClass is None"
        },
        "BRIWindRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for wind resilience (N/A when WindHazardClass is None)"
        },
        "BRIWindScore": {
            "type": "decimal",
            "description": "BRI sub-score for wind resilience (0.0-1.0); null when WindHazardClass is None"
        },
        "BRIFireRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for fire resilience (N/A when FireHazardClass is None)"
        },
        "BRIFireScore": {
            "type": "decimal",
            "description": "BRI sub-score for fire resilience (0.0-1.0); null when FireHazardClass is None"
        },
        "BRISeismicRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for seismic resilience (N/A when SeismicHazardClass is None)"
        },
        "BRISeismicScore": {
            "type": "decimal",
            "description": "BRI sub-score for seismic resilience (0.0-1.0); null when SeismicHazardClass is None"
        },
        "BRIDate": {
            "type": "date",
            "description": "Date the BRI rating was issued"
        },
        "BRIRatingVersion": {
            "type": "string",
            "description": "Version identifier of the BRI methodology applied (e.g., 'BRI v1.6')"
        },
        "BRIRatingAgent": {
            "type": "string",
            "description": "Verifier or certifier that performed the BRI assessment (e.g., Bureau Veritas)"
        }
    }
}
