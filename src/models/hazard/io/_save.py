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

"""Writers for hazard curves and per-gauge storm responses."""

from dataclasses import asdict
from datetime import datetime
from typing import Dict

import database
from ..data_structures import GaugeHazardCurve


def save_hazard_curves(
    hazard_curves: Dict[str, GaugeHazardCurve],
    catchment_id: str,
    metadata: Dict = None
) -> str:
    """Persist gauge hazard curves through the database seam."""
    output_data = {
        'metadata': {
            'catchment_id': catchment_id,
            'generated_at': datetime.now().isoformat(),
            'num_gauges': len(hazard_curves),
            'schema_version': '2.0',
            **(metadata or {})
        },
        'hazard_curves': {}
    }

    for gauge_id, curve in hazard_curves.items():
        curve_dict = asdict(curve)
        curve_dict['curve_points'] = [asdict(p) for p in curve.curve_points]
        curve_dict['term_structure_alert'] = [asdict(p) for p in curve.term_structure_alert]
        curve_dict['term_structure_warning'] = [asdict(p) for p in curve.term_structure_warning]
        curve_dict['term_structure_severe'] = [asdict(p) for p in curve.term_structure_severe]
        output_data['hazard_curves'][gauge_id] = curve_dict

    database.save_gauge_hazard_curves(catchment_id, output_data)
    return catchment_id


def save_gauge_storm_responses(
    responses: Dict[str, list],
    catchment_id: str
) -> None:
    """
    Merge gauge storm responses into the per-gauge timeseries records.

    Reads each gauge's existing timeseries record (created by
    GaugeTimeSeriesGenerator) through the database seam, adds/updates its
    ``storm_responses`` section, and writes it back — creating a minimal record
    if none exists yet.

    Args:
        responses: Dict mapping gauge_id → list of GaugeResponse objects
        catchment_id: Catchment identifier
    """
    num_storms = len(next(iter(responses.values()), []))

    for gauge_id, gauge_responses in responses.items():
        gauge_data = database.get_gauge_timeseries(catchment_id, gauge_id)
        if gauge_data is None:
            gauge_data = {
                "gauge_id": gauge_id,
                "metadata": {
                    "catchment": catchment_id,
                    "generated_at": datetime.now().isoformat(),
                },
            }

        # Add/update storm responses section
        gauge_data['storm_responses'] = {
            'num_storms': num_storms,
            'responses': [
                {
                    'storm_id': r.storm_id,
                    'base_level_m': round(r.base_level_m, 4),
                    'level_change_m': round(r.level_change_m, 4),
                    'peak_level_m': round(r.peak_level_m, 4),
                    'exceeded_alert': r.exceeded_alert,
                    'exceeded_warning': r.exceeded_warning,
                    'exceeded_severe': r.exceeded_severe,
                }
                for r in gauge_responses
            ]
        }

        database.save_gauge_timeseries(catchment_id, gauge_id, gauge_data)
