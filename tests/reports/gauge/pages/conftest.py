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

"""Shared helpers for gauge report page tests."""


def _make_gauge_data(
    gauge_id="GAUGE-001",
    risk_score=None,
    risk_category=None,
    distance_to_thames=200,
    freq_exceed=0,
    historical_high=None,
    severe_level=5.0,
    flood_alert=3.5,
    flood_warning=4.5,
    last_exceed_date=None,
):
    flood_risk = {}
    if risk_score is not None:
        flood_risk["FloodRiskScore"] = risk_score
    if risk_category is not None:
        flood_risk["FloodRiskCategory"] = risk_category

    sensor_stats = {"FrequencyExceedLevel3": freq_exceed}
    if historical_high is not None:
        sensor_stats["HistoricalHighLevel"] = historical_high
    if last_exceed_date is not None:
        sensor_stats["LastDateLevelExceedLevel3"] = last_exceed_date

    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id},
            "ThamesInfo": {
                "DistanceToThamesMeters": distance_to_thames,
                "FloodRiskAssessment": flood_risk,
            },
            "SensorStats": sensor_stats,
            "FloodStage": {
                "UK": {
                    "FloodAlert": flood_alert,
                    "FloodWarning": flood_warning,
                    "SevereFloodWarning": severe_level,
                }
            },
        }
    }


def _make_timeseries(level=None, status="Unknown"):
    return {"readings": [{"waterLevel": level, "alertStatus": status}]}


# ---------------------------------------------------------------------------
# Helpers for page_12_trading_part*.py
# ---------------------------------------------------------------------------

def make_page():
    from reports.gauge.gauge_page_12_trading import GaugeTradingPage
    return GaugeTradingPage()


def make_gauge(gauge_id="GAUGE-001"):
    return {"FloodGauge": {"Header": {"GaugeID": gauge_id, "GaugeName": "Test Gauge"}}}


def make_trade(swap_id="PRS-001", gauge_id="GAUGE-001", is_payer=True):
    return {
        "Header": {"SwapID": swap_id},
        "LegData": {"Payer": is_payer, "Notional": 10_000_000},
        "ScheduleData": {"StartDate": "2024-01-01", "EndDate": "2026-01-01", "Tenor": "2Y"},
        "Pricing": {
            "TriggerLevel": "warning",
            "SpreadBps": 150.0,
            "FairSpreadBps": 145.5,
            "NPV": 25000.0,
        },
        "GaugeSet": {"GaugeBasket": [{"GaugeID": gauge_id}]},
    }
