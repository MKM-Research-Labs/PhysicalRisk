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

"""REIT property portfolio blotter endpoint."""

from flask import jsonify, request

from .blueprint import propertyts_bp
from .financial_loaders import _load_rloan_lookup, _load_property_details


@propertyts_bp.route('/propertyts/blotter', methods=['GET', 'OPTIONS'])
def property_blotter():
    """REIT property portfolio blotter.

    Returns all properties with headline information: value, location,
    distance from river, elevation, floor level, and mortgage summary.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    prop_details = _load_property_details()
    rloan_lookup = _load_rloan_lookup()

    properties = []
    for pid, d in prop_details.items():
        entry = dict(d)
        # Mortgage enrichment
        mg = rloan_lookup.get(pid, {})
        entry['has_rloan'] = pid in rloan_lookup
        entry['outstanding_balance'] = mg.get('outstanding_balance', 0)
        entry['current_ltv'] = mg.get('current_ltv', 0)
        entry['remaining_term_months'] = mg.get('remaining_term_months', 0)
        properties.append(entry)

    properties.sort(key=lambda p: p['property_value'], reverse=True)

    total_value = sum(p['property_value'] for p in properties)
    total_mortgages = sum(p['outstanding_balance'] for p in properties)

    return jsonify({
        'status': 'success',
        'properties': properties,
        'summary': {
            'num_properties': len(properties),
            'total_property_value': round(total_value, 2),
            'total_mortgage_exposure': round(total_mortgages, 2),
        },
    })
