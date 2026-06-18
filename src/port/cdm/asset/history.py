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

"""
Asset history schema — transaction history + hazard / incident history.

Holds two schema dicts as separate module-level names so the legacy
composition in property/schema/__init__.py continues to resolve to the
same PROPERTY_SCHEMA shape:

    TRANSACTION_HISTORY_SCHEMA   Purchase, Sales, Rental, Insurance
    HISTORY_AND_INCIDENTS_SCHEMA EnvironmentalIssues, FireIncidents,
                                 FloodEvents, GroundConditions
"""

TRANSACTION_HISTORY_SCHEMA = {
    "Purchase": {
        "PurchaseDate": {
            "type": "date",
            "description": "Date of purchase"
        },
        "PurchasePriceGbp": {
            "type": "decimal",
            "description": "Purchase price in GBP"
        }
    },
    "Sales": {
        "SalePriceGbp": {
            "type": "decimal",
            "description": "Most recent sale price in GBP"
        },
        "SaleDate": {
            "type": "date",
            "description": "Date of most recent sale"
        },
        "PreviousOwner": {
            "type": "string",
            "description": "Name of the previous owner"
        },
        "MarketingDays": {
            "type": "integer",
            "description": "Number of days on market before sale"
        }
    },
    "Rental": {
        "MonthlyRentGbp": {
            "type": "decimal",
            "description": "Monthly rent in GBP"
        },
        "RentalYield": {
            "type": "decimal",
            "description": "Annual rental yield percentage"
        },
        "RentalHistory": {
            "type": "menu",
            "options": [
                "Never rented", "Previously rented", "Currently rented",
                "Mixed use history",
            ],
            "description": "Rental history classification"
        },
        "VacancyCount": {
            "type": "integer",
            "description": "Number of vacancy periods recorded"
        },
        "TenancyDuration": {
            "type": "menu",
            "options": [
                "0-6 months", "6-12 months", "12-24 months",
                "24-36 months", "36+ months",
            ],
            "description": "Typical tenancy duration bucket"
        }
    },
    "Insurance": {
        "InsurancePremium": {
            "type": "decimal",
            "description": "Annual insurance premium in local currency"
        },
        "ExcessAmount": {
            "type": "integer",
            "description": "Insurance policy excess in local currency"
        },
        "InsuranceStatus": {
            "type": "menu",
            "options": [
                "Uninsured", "Standard cover", "Flood Re supported",
                "Specialist cover",
            ],
            "description": "Current insurance coverage type"
        },
        "FloodReEligible": {
            "type": "boolean",
            "description": "Eligibility for Flood Re scheme"
        },
        "ClaimsHistory": {
            "type": "integer",
            "description": "Number of historical insurance claims"
        },
        "LastClaimDate": {
            "type": "date",
            "description": "Date of most recent insurance claim"
        },
        "LastClaimType": {
            "type": "menu",
            "options": [
                "None", "Fire", "Flood damage", "Subsidence",
                "Domestic appliances",
            ],
            "description": "Nature of most recent claim"
        }
    }
}


HISTORY_AND_INCIDENTS_SCHEMA = {
    "EnvironmentalIssues": {
        "AirQuality": {
            "type": "menu",
            "options": ["Low", "Moderate", "High", "Very high", "Exceeds limits"],
            "description": "Local air-quality classification"
        },
        "WaterQuality": {
            "type": "menu",
            "options": ["Excellent", "Good", "Fair", "Poor", "Very poor"],
            "description": "Local water-quality classification"
        },
        "NoisePollution": {
            "type": "menu",
            "options": ["None", "Traffic", "Planes", "Train"],
            "description": "Dominant noise pollution source"
        },
        "LastEnvironmentalIssueDate": {
            "type": "date",
            "description": "Date of last recorded environmental issue affecting the property"
        }
    },
    "FireIncidents": {
        "FireDamageSeverity": {
            "type": "menu",
            "options": ["None", "Minor", "Moderate", "Severe", "Total loss"],
            "description": "Severity of most recent fire damage at the property"
        },
        "LastFireDate": {
            "type": "date",
            "description": "Date of most recent fire incident (null if none)"
        }
    },
    "FloodEvents": {
        "FloodReturnPeriod": {
            "type": "integer",
            "description": "Return period (years) of the most recent flood event"
        },
        "FloodDamageSeverity": {
            "type": "menu",
            "options": [
                "No damage", "Minor damage", "Moderate damage",
                "Significant damage", "Severe damage",
            ],
            "description": "Severity of most recent flood damage at the property"
        },
        "LastFloodDateHistory": {
            "type": "date",
            "description": "Date of most recent flood event at the property (null if none)"
        }
    },
    "GroundConditions": {
        "SubsidenceStatus": {
            "type": "menu",
            "options": [
                "No issues", "Minor movement", "Moderate subsidence",
                "Severe subsidence", "Under investigation",
            ],
            "description": "Subsidence status of the property"
        },
        "ContaminationStatus": {
            "type": "menu",
            "options": [
                "None detected", "Historical industrial", "Remediated",
                "Current contamination", "Under investigation",
            ],
            "description": "Land-contamination status"
        },
        "GroundStability": {
            "type": "menu",
            "options": [
                "Stable", "Minor concerns", "Moderate risk", "High risk",
                "Active movement",
            ],
            "description": "Overall ground-stability classification"
        },
        "LastGroundIssueDate": {
            "type": "date",
            "description": "Date of last recorded ground-condition issue (null if none)"
        }
    }
}
