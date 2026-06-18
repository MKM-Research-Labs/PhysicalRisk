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

"""Shared fixtures and test data for gauge route coverage tests."""

import json


GAUGE_ID = "GAUGE-001"

GAUGE_DATA = {
    "flood_gauges": [{
        "FloodGauge": {
            "Header": {"GaugeID": GAUGE_ID, "GaugeName": "Test Gauge"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStage": {"UK": {
                "FloodAlert": 4.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.0
            }},
            "SensorDetails": {"GaugeInformation": {
                "GaugeType": "Pressure", "GaugeOwner": "EA",
                "OperationalStatus": "Active",
                "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GaugeDatum": 0.0,
            }, "SensorSpecifications": {}, "Measurements": {}},
            "SensorStats": {"HistoricalHighLevel": 6.0, "HistoricalHighDate": "2024-01-01"},
            "NRFAMetadata": {},
        }
    }]
}

HAZARD_DATA = {
    "hazard_curves": {
        GAUGE_ID: {
            "gauge_name": "Test Gauge",
            "gev_location": 3.5,
            "gev_scale": 0.8,
            "gev_shape": 0.1,
            "curve_points": [{"exceedance_prob": 0.1, "level_m": 4.5}],
            "return_period_levels": {"10": 4.5},
            "flood_alert_m": 4.0,
            "flood_warning_m": 4.5,
            "severe_flood_warning_m": 5.0,
            "annual_flood_prob_alert": 0.12,
            "annual_flood_prob_warning": 0.05,
            "annual_flood_prob_severe": 0.02,
            "term_structure_alert": [{"tenor": 1, "prob": 0.12}],
            "term_structure_warning": [{"tenor": 1, "prob": 0.05}],
            "term_structure_severe": [{"tenor": 1, "prob": 0.02}],
        }
    }
}


def make_client(tmp_path, monkeypatch, *, gauge_data=None, gaugehc=None,
                gaugehd_file=None, gaugets_file=None, storm_sequences=None):
    """Build a Flask test client with configurable data files."""
    from config import config

    if gauge_data is None:
        gauge_data = GAUGE_DATA
    (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

    if gaugehc is not None:
        (tmp_path / "gaugehc.json").write_text(json.dumps(gaugehc))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir(exist_ok=True)
    if gaugets_file is not None:
        (gaugets_dir / f"{GAUGE_ID}.json").write_text(json.dumps(gaugets_file))

    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir(exist_ok=True)
    if gaugehd_file is not None:
        (gaugehd_dir / f"gauge_{GAUGE_ID}_hd.json").write_text(json.dumps(gaugehd_file))

    if storm_sequences is not None:
        (tmp_path / "storm_sequences.json").write_text(json.dumps(storm_sequences))

    reports_dir = tmp_path / "reports" / "gauges"
    reports_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: reports_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
