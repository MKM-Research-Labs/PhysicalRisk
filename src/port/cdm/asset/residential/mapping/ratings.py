# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
