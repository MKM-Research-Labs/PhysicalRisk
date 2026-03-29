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

"""Shared helpers for hazard I/O tests."""

from datetime import datetime

from models.hazard.data_structures import (
    GaugeHazardCurve,
    GaugeResponse,
    HazardCurvePoint,
    TermStructurePoint,
)


def _make_gauge_json(gauge_id="GAUGE-001"):
    """Minimal gauge.json structure compatible with FloodGaugeCDM."""
    return {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {
                        "GaugeID": gauge_id,
                        "GaugeName": "Test Gauge",
                    },
                    "Location": {
                        "GaugeLatitude": 51.5,
                        "GaugeLongitude": -0.1,
                        "GaugeDatum": 5.0,
                    },
                    "FloodStage": {
                        "UK": {
                            "FloodAlert": 4.0,
                            "FloodWarning": 4.5,
                            "SevereFloodWarning": 5.0,
                        }
                    },
                    "SensorDetails": {
                        "GaugeInformation": {
                            "GaugeType": "Pressure",
                            "GaugeOwner": "EA",
                            "OperationalStatus": "Active",
                            "GaugeLatitude": 51.5,
                            "GaugeLongitude": -0.1,
                            "GaugeDatum": 5.0,
                        },
                        "SensorSpecifications": {},
                        "Measurements": {},
                    },
                    "SensorStats": {},
                    "NRFAMetadata": {},
                }
            }
        ]
    }


def _make_storms_json(n=3):
    return {
        "storms": [
            {
                "storm_id": f"STORM-{i:04d}",
                "name": f"Storm {i}",
                "effective_precipitation_mm": 50.0 + i * 10,
            }
            for i in range(n)
        ]
    }


def _make_hazard_curve(gauge_id="GAUGE-001"):
    return GaugeHazardCurve(
        gauge_id=gauge_id,
        gauge_name="Test Gauge",
        latitude=51.5,
        longitude=-0.1,
        elevation_m=5.0,
        flood_alert_m=4.0,
        flood_warning_m=4.5,
        severe_flood_warning_m=5.0,
        gev_location=4.0,
        gev_scale=0.5,
        gev_shape=0.1,
        curve_points=[
            HazardCurvePoint(4.0, 0.20, 5.0),
            HazardCurvePoint(5.0, 0.05, 20.0),
        ],
        return_period_levels={"10yr": 4.5, "50yr": 5.0, "100yr": 5.5},
        annual_flood_prob_alert=0.15,
        annual_flood_prob_warning=0.08,
        annual_flood_prob_severe=0.03,
        annual_hazard_rate_alert=0.15,
        annual_hazard_rate_warning=0.08,
        annual_hazard_rate_severe=0.03,
        term_structure_alert=[
            TermStructurePoint(1, 0.15, 0.14, 0.86, 0.14),
            TermStructurePoint(2, 0.30, 0.26, 0.74, 0.26),
        ],
        term_structure_warning=[
            TermStructurePoint(1, 0.08, 0.077, 0.923, 0.077),
        ],
        term_structure_severe=[
            TermStructurePoint(1, 0.03, 0.030, 0.970, 0.030),
        ],
        num_storms_simulated=100,
        simulation_timestamp=datetime.now().isoformat(),
    )
