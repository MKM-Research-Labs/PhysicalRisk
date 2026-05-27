# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flatten ProtectionMeasures.RiskAssessment (insurance + governing-body ratings)."""


def flatten_ratings(prop: dict) -> dict:
    """Return flat snake_case keys for the two parallel rating subsections."""
    pm_risk = prop.get("ProtectionMeasures", {}).get("RiskAssessment", {})
    insurance = pm_risk.get("InsuranceBodyRatings", {})
    governing = pm_risk.get("GoverningBodyRatings", {})

    return {
        "insurance_rating":         insurance.get("InsuranceRating"),
        "insurance_date":           insurance.get("InsuranceDate"),
        "insurance_rating_version": insurance.get("InsuranceRatingVersion"),
        "insurance_rating_body":    insurance.get("InsuranceRatingBody"),

        "bri_rating":         governing.get("BRIRating"),
        "bri_date":           governing.get("BRIDate"),
        "bri_rating_version": governing.get("BRIRatingVersion"),
        "bri_rating_agent":   governing.get("BRIRatingAgent"),
    }
