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

"""Render the ProtectionMeasures section.

CDM sub-shape:
    ProtectionMeasures
      RiskAssessment
        InsuranceBodyRatings { … }
        GoverningBodyRatings { … }
      HazardProfile          { FloodHazardClass, WindHazardClass, … }
      ResilienceMeasures
        BuildingAssessment   (may be empty)
        SiteAndDrainage      (may be empty)
        FloodProtection      { FloodGates, FloodBarriers, … }
        FireProtection       (may be empty)
        ContinuityMeasures   (may be empty)
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_INSURANCE_FIELDS = [
    ("InsuranceRating",        "Insurance Rating"),
    ("InsuranceDate",          "Insurance Date"),
    ("InsuranceRatingVersion", "Insurance Rating Version"),
    ("InsuranceRatingBody",    "Insurance Rating Body"),
]

_GOVERNING_METADATA_FIELDS = [
    ("BRIDate",          "BRI Date"),
    ("BRIRatingVersion", "BRI Rating Version"),
    ("BRIRatingAgent",   "BRI Rating Agent"),
]

# Per-hazard BRI sub-ratings + scores. Phase 2 added Water + Flash to split
# what used to be a single Flood envelope. BRIFloodRating is now the
# weaker-of envelope auto-computed from Water + Flash by the BRI helper.
_BRI_RATING_PAIRS = [
    ("Overall",       "BRIRating",        "BRIScore"),
    ("Wind",          "BRIWindRating",    "BRIWindScore"),
    ("Flood (envelope)", "BRIFloodRating", "BRIFloodScore"),
    ("Water (tsunami / surge)", "BRIWaterRating", "BRIWaterScore"),
    ("Flash flood / fluvial",   "BRIFlashRating", "BRIFlashScore"),
    ("Fire",          "BRIFireRating",    "BRIFireScore"),
    ("Seismic",       "BRISeismicRating", "BRISeismicScore"),
]

_HAZARD_FIELDS = [
    ("FloodHazardClass",      "Flood Hazard Class"),
    ("WindHazardClass",       "Wind Hazard Class"),
    ("SeismicHazardClass",    "Seismic Hazard Class"),
    ("FireHazardClass",       "Fire Hazard Class"),
    ("DesignWindSpeedKmh",    "Design Wind Speed (km/h)"),
    ("DesignFloodReturnYr",   "Design Flood Return Period (yr)"),
    ("DesignSeismicPGA",      "Design Seismic PGA"),
]

# Operational thresholds the asset is designed to withstand. Phase 2.
# Wind is now in m/s (Major/Minor); Water + Flash are heights in m above
# the local gauge SevereFloodWarning level.
_THRESHOLD_FIELDS = [
    ("WindThresholdMajorMps",  "Wind Major Threshold (m/s)"),
    ("WindThresholdMinorMps",  "Wind Minor Threshold (m/s)"),
    ("WaterThresholdMajorM",   "Water Major Threshold (m over Severe)"),
    ("WaterThresholdMinorM",   "Water Minor Threshold (m over Severe)"),
    ("FlashThresholdMajorM",   "Flash Major Threshold (m over Severe)"),
    ("FlashThresholdMinorM",   "Flash Minor Threshold (m over Severe)"),
]

# IndustryGroups — free-string BRI measure code lists per hazard.
_INDUSTRY_GROUP_FIELDS = [
    ("WindCodes",    "Wind Codes"),
    ("WaterCodes",   "Water (Tsunami / Surge) Codes"),
    ("FlashCodes",   "Flash Flood / Fluvial Codes"),
    ("FireCodes",    "Fire Codes"),
    ("SeismicCodes", "Seismic Codes"),
]

_FLOOD_PROTECTION_FIELDS = [
    ("FloodGates",         "Flood Gates"),
    ("FloodBarriers",      "Flood Barriers"),
    ("SumpPump",           "Sump Pump"),
    ("FloodWarningSystem", "Flood Warning System"),
]


def _bri_rating_rows(gbr: Dict[str, Any]) -> List[tuple]:
    """Build the per-hazard BRI rating/score rows. Skips hazards where
    both the rating and the score are absent so empty hazards stay out."""
    rows = []
    for label, rating_key, score_key in _BRI_RATING_PAIRS:
        rating = gbr.get(rating_key)
        score = gbr.get(score_key)
        if rating is None and score is None:
            continue
        if isinstance(score, float):
            value = f"{rating or '—'} / {score:.4f}"
        else:
            value = f"{rating or '—'} / —"
        rows.append((label, value))
    return rows


def _industry_group_rows(gbr: Dict[str, Any]) -> List[tuple]:
    """Build the IndustryGroups code-list rows. Empty lists / missing
    blocks are skipped so the section only appears when codes exist."""
    groups = gbr.get("IndustryGroups", {}) or {}
    rows = []
    for key, label in _INDUSTRY_GROUP_FIELDS:
        codes = groups.get(key)
        if not codes:
            continue
        rows.append((label, ", ".join(codes)))
    return rows


def render_protection(protection: Dict[str, Any], page) -> List:
    """Build the protection measures tables."""
    elements: List = [
        Paragraph("Protection Measures", page.styles["SectionHeader"]),
    ]

    risk = protection.get("RiskAssessment", {}) or {}
    gbr = risk.get("GoverningBodyRatings", {}) or {}

    elements.extend(section_block(
        "Insurance Body Ratings",
        page,
        auto_rows(risk.get("InsuranceBodyRatings", {}) or {}, _INSURANCE_FIELDS),
        style="protection",
        header=("Field", "Value"),
    ))

    # BRI ratings split into two tables: metadata, then per-hazard rating/score.
    elements.extend(section_block(
        "Governing Body Ratings",
        page,
        auto_rows(gbr, _GOVERNING_METADATA_FIELDS),
        style="protection",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "BRI Ratings by Hazard",
        page,
        _bri_rating_rows(gbr),
        style="protection",
        header=("Hazard", "Rating / Score"),
    ))
    elements.extend(section_block(
        "BRI Measure Codes (Industry Groups)",
        page,
        _industry_group_rows(gbr),
        style="protection",
        header=("Hazard", "Codes"),
    ))

    hazard_profile = protection.get("HazardProfile", {}) or {}
    elements.extend(section_block(
        "Hazard Profile",
        page,
        auto_rows(hazard_profile, _HAZARD_FIELDS),
        style="protection",
        header=("Hazard", "Value"),
    ))
    elements.extend(section_block(
        "Operational Thresholds",
        page,
        auto_rows(hazard_profile, _THRESHOLD_FIELDS),
        style="protection",
        header=("Threshold", "Value"),
    ))

    resilience = protection.get("ResilienceMeasures", {}) or {}
    elements.extend(section_block(
        "Flood Protection Measures",
        page,
        auto_rows(resilience.get("FloodProtection", {}) or {}, _FLOOD_PROTECTION_FIELDS),
        style="protection",
        header=("Measure", "Status"),
    ))
    return elements
