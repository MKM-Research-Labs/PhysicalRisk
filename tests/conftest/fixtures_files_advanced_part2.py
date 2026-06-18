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

"""Fixtures for advanced data directories: gaugehc, storms, fully_populated."""

import json

import pytest


@pytest.fixture
def sample_gaugehc_file(temp_data_dir):
    """Create sample gauge hazard curves file."""
    data = {
        "metadata": {"generated": "2025-01-01", "catchment": "test"},
        "hazard_curves": {
            "GAUGE-001": {
                "gauge_id": "GAUGE-001",
                "gauge_name": "Thames at Teddington",
                "gev_location": 4.5,
                "gev_scale": 0.8,
                "gev_shape": 0.1,
                "flood_alert_m": 4.5,
                "flood_warning_m": 5.0,
                "flood_severe_m": 5.5,
                "annual_flood_prob_alert": 0.15,
                "annual_flood_prob_warning": 0.08,
                "annual_flood_prob_severe": 0.03,
                "curve_points": [
                    {"water_level_m": 4.0, "exceedance_prob": 0.3},
                    {"water_level_m": 5.0, "exceedance_prob": 0.08},
                    {"water_level_m": 6.0, "exceedance_prob": 0.01}
                ],
                "return_period_levels": {"10yr": 4.8, "50yr": 5.5, "100yr": 6.0},
                "term_structure_alert": [
                    {"year": 1, "cum_prob": 0.15, "survival_prob": 0.85},
                    {"year": 2, "cum_prob": 0.2775, "survival_prob": 0.7225},
                    {"year": 5, "cum_prob": 0.5563, "survival_prob": 0.4437}
                ],
                "term_structure_warning": [
                    {"year": 1, "cum_prob": 0.08, "survival_prob": 0.92},
                    {"year": 2, "cum_prob": 0.1536, "survival_prob": 0.8464},
                    {"year": 5, "cum_prob": 0.3409, "survival_prob": 0.6591}
                ],
                "term_structure_severe": [
                    {"year": 1, "cum_prob": 0.03, "survival_prob": 0.97},
                    {"year": 2, "cum_prob": 0.0591, "survival_prob": 0.9409},
                    {"year": 5, "cum_prob": 0.1413, "survival_prob": 0.8587}
                ]
            },
            "GAUGE-002": {
                "gauge_id": "GAUGE-002",
                "gauge_name": "Richmond Lock",
                "gev_location": 3.0,
                "gev_scale": 0.5,
                "gev_shape": 0.05,
                "flood_alert_m": 3.0,
                "flood_warning_m": 3.5,
                "flood_severe_m": 4.0,
                "annual_flood_prob_alert": 0.2,
                "annual_flood_prob_warning": 0.1,
                "annual_flood_prob_severe": 0.04,
                "curve_points": [],
                "return_period_levels": {"10yr": 3.5, "50yr": 4.0, "100yr": 4.5},
                "term_structure_alert": [],
                "term_structure_warning": [],
                "term_structure_severe": []
            }
        }
    }
    filepath = temp_data_dir / "gaugehc.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath


@pytest.fixture
def sample_storms_file(temp_data_dir):
    """Create storm_sequences.json with all storms (flooding + non-flooding).

    STORM-001 to STORM-004 match the propertyts flood events.
    STORM-005 to STORM-008 are non-flooding storms that must still appear in the dropdown.
    Each storm is wrapped in an isolated sequence (storm_multi format).
    """
    categories = ['minor', 'moderate', 'significant', 'catastrophic',
                  'minor', 'moderate', 'significant', 'catastrophic']
    sequences = []
    for i in range(1, 9):
        sequences.append({
            'sequence_id': f'SEQ-{i:03d}',
            'sequence_type': 'isolated',
            'intensity_category': categories[i - 1],
            'sequence_start': '2024-01-01T00:00:00+00:00',
            'total_duration_hours': 24 + i * 6,
            'event_window_hours': 168,
            'drainage_window_hours': 12.0,
            'storms': [{
                'storm_id': f'STORM-{i:03d}',
                'scenario_id': f'SEQ-{i:03d}',
                'storm_index': 0,
                'start_time_hours': 0.0,
                'duration_hours': 24 + i * 6,
                'intensity_category': categories[i - 1],
                'intensity_factor': 0.5 + i * 0.1,
                'precipitation_mm': 50 + i * 20,
                'peak_position': 0.5,
            }],
            'num_storms': 1,
            'inter_storm_gaps_hours': [],
            'total_precipitation_mm': 50 + i * 20,
            'max_intensity_factor': 0.5 + i * 0.1,
            'avg_intensity_factor': 0.5 + i * 0.1,
            'cumulative_intensity_factor': 0.5 + i * 0.1,
        })
    data = {
        'schema_version': '2.0-multi-storm',
        'num_sequences': len(sequences),
        'sequences': sequences,
    }
    filepath = temp_data_dir / 'storm_sequences.json'
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath


@pytest.fixture
def fully_populated_data_dir(
    populated_data_dir,
    sample_propertyts_dir,
    sample_propertyhc_file,
    sample_gaugehc_file,
    sample_storms_file
):
    """Create a data directory with ALL data types including propertyts, propertyhc, gaugehc.

    Also enriches gaugets files with storm_responses so that the
    /propertyts/storms endpoint (which builds its storm list from gaugets)
    can discover all 8 storms.
    """
    gaugets_dir = populated_data_dir / "gaugets"
    if gaugets_dir.exists():
        # Add storm_responses to each gauge file for all 8 storms
        storm_responses = []
        for i in range(1, 9):
            storm_responses.append({
                "storm_id": f"STORM-{i:03d}",
                "base_level_m": 2.5,
                "level_change_m": 0.5 + i * 0.3,
                "peak_level_m": 3.0 + i * 0.3,
                "exceeded_alert": i >= 3,
                "exceeded_warning": i >= 5,
                "exceeded_severe": i >= 7,
            })
        for gf in gaugets_dir.glob("GAUGE-*.json"):
            with open(gf, 'r') as f:
                gdata = json.load(f)
            gdata["storm_responses"] = {
                "num_storms": 8,
                "responses": storm_responses,
            }
            with open(gf, 'w') as f:
                json.dump(gdata, f)
    return populated_data_dir
