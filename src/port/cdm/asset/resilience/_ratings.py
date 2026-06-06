# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Insurance and governing-body (BRI) rating schemas."""

# --- Insurance + governing-body ratings -------------------------------------

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
            "description": "BRI sub-rating for the overall water envelope. Auto-computed as "
                           "min(BRIWaterRating, BRIFlashRating) when both are present. "
                           "N/A when FloodHazardClass is None."
        },
        "BRIFloodScore": {
            "type": "decimal",
            "description": "BRI sub-score for flood resilience (0.0-1.0); null when FloodHazardClass is None"
        },
        "BRIWaterRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for water (tsunami / storm-surge) resilience. "
                           "Drives WaterThresholdMajorM / WaterThresholdMinorM coverage. "
                           "N/A when the asset has no tsunami or storm-surge exposure."
        },
        "BRIWaterScore": {
            "type": "decimal",
            "description": "BRI sub-score for water (tsunami / storm-surge) resilience (0.0-1.0)"
        },
        "BRIFlashRating": {
            "type": "menu",
            "options": ["AA", "A", "B", "NR", "N/A"],
            "description": "BRI sub-rating for flash-flood / fluvial resilience. Drives "
                           "FlashThresholdMajorM / FlashThresholdMinorM coverage. N/A when "
                           "the asset has no flash-flood exposure."
        },
        "BRIFlashScore": {
            "type": "decimal",
            "description": "BRI sub-score for flash-flood / fluvial resilience (0.0-1.0)"
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
        },
        "IndustryGroups": {
            "WindCodes": {
                "type": "text[]",
                "description": "Free-string list of industry BRI wind-resilience measure codes "
                               "applied to the asset (e.g. ['WD02','WD04','WD05','WD08']). "
                               "Catalogue is regional; SE-Asia commercial codes live in "
                               "port.rand.halong.commercial.bri_codes."
            },
            "WaterCodes": {
                "type": "text[]",
                "description": "Free-string list of BRI water (tsunami / storm-surge) resilience "
                               "measure codes applied to the asset (e.g. ['WT08','WT09','WT13'])."
            },
            "FlashCodes": {
                "type": "text[]",
                "description": "Free-string list of BRI flash-flood / fluvial resilience measure "
                               "codes applied to the asset (e.g. ['WT05','WT10','WT13','WT15'])."
            },
            "FireCodes": {
                "type": "text[]",
                "description": "Free-string list of BRI fire-resilience measure codes applied "
                               "to the asset (e.g. ['FI04','FI12','FI14','FI16','FI17','FI21'])."
            },
            "SeismicCodes": {
                "type": "text[]",
                "description": "Free-string list of BRI seismic-resilience measure codes applied "
                               "to the asset (e.g. ['GS02','GS08','GS11','GS15','GS16'])."
            }
        }
    }
}
