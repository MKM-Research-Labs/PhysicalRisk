# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
HistoryAndIncidents — environmental, fire, flood, and ground-condition history.

Not part of the revised BRI-focused CDM proposal, but kept because the rand
generator registry already produces these fields and removing them would
silently break their generation path.

Sub-sections:
    EnvironmentalIssues   — air/water/noise quality, last issue date.
    FireIncidents         — past fire damage severity and date.
    FloodEvents           — past flood return period, damage severity, date.
    GroundConditions      — subsidence, contamination, stability, last date.
"""

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
            "type": "menu",
            "options": [50, 100, 200, 500, 1000],
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
