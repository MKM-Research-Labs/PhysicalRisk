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
