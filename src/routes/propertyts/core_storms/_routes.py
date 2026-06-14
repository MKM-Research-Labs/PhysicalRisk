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

"""Per-property storm-analysis endpoint, registered on propertyts_bp."""

import logging

from flask import jsonify

from .. import propertyts_bp
from ..core_summary import _load_property_or_404
from ._helpers import (
    _build_storm_lookups,
    _tag_flood_events,
    _enrich_nearest_gauges,
    _lookup_property_address,
)

logger = logging.getLogger(__name__)


@propertyts_bp.route('/properties/<prop_id>/storms', methods=['GET', 'OPTIONS'])
def property_storms(prop_id: str):
    """
    Get storm scenario analysis for a property.

    Returns flood events with hydrograph readings, nearest gauge info,
    and summary statistics — structured for the property storm analysis panel.
    """
    early, pdata = _load_property_or_404(prop_id)
    if early is not None:
        return early

    seq_lookup, storm_meta, storm_severe, seq_to_event = _build_storm_lookups()
    _tag_flood_events(pdata, prop_id, seq_lookup, storm_meta, storm_severe, seq_to_event)
    severe_at_gauge = _enrich_nearest_gauges(pdata)

    summary = pdata.get('summary', {})
    summary['severe_at_nearest_gauge'] = severe_at_gauge

    prop_address = _lookup_property_address(prop_id)

    return jsonify({
        'status': 'success',
        'property_id': prop_id,
        'property_address': prop_address,
        'property_info': {
            'elevation_m': pdata.get('elevation_m', 0),
            'floor_level_m': pdata.get('floor_level_m', 0),
            'location': pdata.get('location', {}),
        },
        'nearest_gauges': pdata.get('nearest_gauges', []),
        'flood_events': pdata.get('flood_events', []),
        'summary': summary,
    })
