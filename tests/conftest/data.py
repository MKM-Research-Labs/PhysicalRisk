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

"""Sample test data constants matching CDM schemas."""

SAMPLE_PROPERTY = {
    "PropertyHeader": {
        "Header": {
            "PropertyID": "PROP-001",
            "PropertyType": "Residential"
        },
        "Location": {
            "Address": "123 Main Street",
            "City": "Miami",
            "State": "FL",
            "ZipCode": "33101",
            "County": "Miami-Dade",
            "Latitude": 25.7617,
            "Longitude": -80.1918
        },
        "Valuation": {
            "MarketValue": 450000,
            "AssessedValue": 425000
        }
    }
}

SAMPLE_PROPERTY_2 = {
    "PropertyHeader": {
        "Header": {
            "PropertyID": "PROP-002",
            "PropertyType": "Commercial"
        },
        "Location": {
            "Address": "456 Ocean Drive",
            "City": "Miami Beach",
            "State": "FL",
            "ZipCode": "33139",
            "County": "Miami-Dade",
            "Latitude": 25.7825,
            "Longitude": -80.1340
        },
        "Valuation": {
            "MarketValue": 1250000,
            "AssessedValue": 1100000
        }
    }
}

SAMPLE_PROPERTY_TX = {
    "PropertyHeader": {
        "Header": {
            "PropertyID": "PROP-003",
            "PropertyType": "Residential"
        },
        "Location": {
            "Address": "789 Houston Ave",
            "City": "Houston",
            "State": "TX",
            "ZipCode": "77001",
            "County": "Harris",
            "Latitude": 29.7604,
            "Longitude": -95.3698
        },
        "Valuation": {
            "MarketValue": 350000,
            "AssessedValue": 320000
        }
    }
}

SAMPLE_MORTGAGE = {
    "RLoanID": "RLOAN-001",
    "PropertyID": "PROP-001",
    "LoanAmount": 360000,
    "InterestRate": 6.5,
    "LoanType": "Conventional",
    "Lender": "First National Bank",
    "Status": "Active",
    "OriginationDate": "2024-01-15",
    "MaturityDate": "2054-01-15"
}

SAMPLE_MORTGAGE_2 = {
    "RLoanID": "RLOAN-002",
    "PropertyID": "PROP-002",
    "LoanAmount": 1000000,
    "InterestRate": 7.0,
    "LoanType": "Commercial",
    "Lender": "Regional Credit Union",
    "Status": "Active",
    "OriginationDate": "2023-06-01",
    "MaturityDate": "2053-06-01"
}

SAMPLE_MORTGAGE_DELINQUENT = {
    "RLoanID": "RLOAN-003",
    "PropertyID": "PROP-003",
    "LoanAmount": 280000,
    "InterestRate": 5.5,
    "LoanType": "FHA",
    "Lender": "First National Bank",
    "Status": "Delinquent",
    "OriginationDate": "2022-03-01",
    "MaturityDate": "2052-03-01"
}

SAMPLE_GAUGE = {
    "FloodGauge": {
        "Header": {
            "GaugeID": "GAUGE-001",
            "GaugeName": "Thames at Teddington",
            "Latitude": 51.4309,
            "Longitude": -0.3211
        },
        "SensorDetails": {
            "GaugeInformation": {
                "GaugeType": "River",
                "GaugeOwner": "Environment Agency",
                "OperationalStatus": "Active"
            }
        },
        "FloodStages": {
            "ActionStage": 4.5,
            "MinorFlood": 5.0,
            "ModerateFlood": 5.5,
            "MajorFlood": 6.0
        }
    }
}

SAMPLE_GAUGE_2 = {
    "FloodGauge": {
        "Header": {
            "GaugeID": "GAUGE-002",
            "GaugeName": "Richmond Lock",
            "Latitude": 51.4590,
            "Longitude": -0.3065
        },
        "SensorDetails": {
            "GaugeInformation": {
                "GaugeType": "Tidal",
                "GaugeOwner": "Environment Agency",
                "OperationalStatus": "Active"
            }
        },
        "FloodStages": {
            "ActionStage": 3.0,
            "MinorFlood": 3.5,
            "ModerateFlood": 4.0,
            "MajorFlood": 4.5
        }
    }
}

SAMPLE_GAUGE_INACTIVE = {
    "FloodGauge": {
        "Header": {
            "GaugeID": "GAUGE-003",
            "GaugeName": "Old Weir Station",
            "Latitude": 51.4100,
            "Longitude": -0.3500
        },
        "SensorDetails": {
            "GaugeInformation": {
                "GaugeType": "River",
                "GaugeOwner": "USGS",
                "OperationalStatus": "Inactive"
            }
        }
    }
}

SAMPLE_TIMESERIES = [
    {
        "timestamp": "2025-01-01T00:00:00Z",
        "hour": 0,
        "readings": [
            {"gaugeId": "GAUGE-001", "name": "Thames at Teddington", "level": 4.2},
            {"gaugeId": "GAUGE-002", "name": "Richmond Lock", "level": 2.8}
        ]
    },
    {
        "timestamp": "2025-01-01T01:00:00Z",
        "hour": 1,
        "readings": [
            {"gaugeId": "GAUGE-001", "name": "Thames at Teddington", "level": 4.5},
            {"gaugeId": "GAUGE-002", "name": "Richmond Lock", "level": 3.0}
        ]
    },
    {
        "timestamp": "2025-01-01T02:00:00Z",
        "hour": 2,
        "readings": [
            {"gaugeId": "GAUGE-001", "name": "Thames at Teddington", "level": 4.8},
            {"gaugeId": "GAUGE-002", "name": "Richmond Lock", "level": 3.2}
        ]
    }
]

SAMPLE_STORM = {
    "TCEvent": {
        "Header": {
            "EventID": "STORM-2025-001",
            "EventName": "Hurricane Alpha",
            "Category": 3,
            "Basin": "ATL",
            "Season": 2025,
            "StartDate": "2025-08-15",
            "EndDate": "2025-08-22",
            "PeakIntensity": 120
        },
        "Track": [
            {"Latitude": 20.0, "Longitude": -60.0, "Timestamp": "2025-08-15T00:00:00Z"},
            {"Latitude": 22.0, "Longitude": -65.0, "Timestamp": "2025-08-16T00:00:00Z"},
            {"Latitude": 25.0, "Longitude": -70.0, "Timestamp": "2025-08-17T00:00:00Z"}
        ],
        "Impact": {
            "AffectedArea": "Southeast Florida",
            "EstimatedDamage": 5000000000
        }
    }
}
