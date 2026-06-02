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
Property hazard curve and PRS pricing endpoints.

Provides access to property-level hazard curves, PRS pricing,
and basis calculations against nearest gauge PRS prices.
"""

import json
import logging

from flask import Blueprint, jsonify, request

from config import config

logger = logging.getLogger(__name__)

propertyhc_bp = Blueprint('propertyhc', __name__)


def _get_hazard_data(filename: str = 'propertyhc.json') -> dict:
    """Load property hazard curves data."""
    path = config.get_input_dir() / filename
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return json.load(f)


def _load_or_404(filename: str = 'propertyhc.json', label: str = 'Property hazard curves'):
    """Load hazard data or return a 404 JSON response.

    Returns ``(data, None)`` on success or ``(None, response)`` on failure.
    """
    if request.method == 'OPTIONS':
        return None, jsonify({'status': 'ok'})
    data = _get_hazard_data(filename)
    if not data:
        return None, (jsonify({
            'status': 'error',
            'message': f'{label} not yet generated'
        }), 404)
    return data, None


@propertyhc_bp.route('/propertyhc/summary', methods=['GET', 'OPTIONS'])
def propertyhc_summary():
    """Get portfolio-wide property hazard summary."""
    data, err = _load_or_404(label='Property hazard curves. Run: python app.py port --propertyhc')
    if err:
        return err

    curves = data.get('property_hazard_curves', {})

    # Build summary statistics
    flood_counts = []
    basis_values = []
    transmission_rates = []
    max_depths = []

    for prop_id, pc in curves.items():
        flood_counts.append(pc.get('flood_count', 0))
        summary = pc.get('summary', {})
        if summary.get('avg_basis_bps') is not None:
            basis_values.append(summary['avg_basis_bps'])
        if summary.get('flood_transmission_rate') is not None:
            transmission_rates.append(summary['flood_transmission_rate'])
        if summary.get('max_depth_m') is not None:
            max_depths.append(summary['max_depth_m'])

    return jsonify({
        'status': 'success',
        'data': {
            'metadata': data.get('metadata', {}),
            'summary': data.get('summary', {}),
            'distribution': {
                'num_properties': len(curves),
                'avg_flood_count': round(sum(flood_counts) / len(flood_counts), 1) if flood_counts else 0,
                'avg_basis_bps': round(sum(basis_values) / len(basis_values), 2) if basis_values else 0,
                'avg_transmission_rate': round(sum(transmission_rates) / len(transmission_rates), 4) if transmission_rates else 0,
                'max_depth_m': round(max(max_depths), 4) if max_depths else 0,
            },
        }
    })


@propertyhc_bp.route('/properties/<prop_id>/hazard', methods=['GET', 'OPTIONS'])
def property_hazard(prop_id: str):
    """Get full hazard curve, PRS pricing, and basis for one property."""
    data, err = _load_or_404()
    if err:
        return err

    curves = data.get('property_hazard_curves', {})
    prop_data = curves.get(prop_id)

    if not prop_data:
        return jsonify({
            'status': 'error',
            'message': f'Property {prop_id} not found in hazard curves (may have < 3 flood events)'
        }), 404

    # Attach terrain grid + num_storms from metadata so the PRS pricer
    # can do zone repricing and the panel knows the denominator used by
    # the generator (avoids hard-coded 20000 in the JS).
    metadata = data.get('metadata', {})
    meta_out = {}
    if metadata.get('terrain_grid'):
        meta_out['terrain_grid'] = metadata['terrain_grid']
    if metadata.get('num_storms') is not None:
        meta_out['num_storms'] = metadata['num_storms']
    if meta_out:
        prop_data['_metadata'] = meta_out

    return jsonify({
        'status': 'success',
        'data': prop_data,
    })


@propertyhc_bp.route('/propertyhc/basis', methods=['GET', 'OPTIONS'])
def propertyhc_basis():
    """Get basis table across all properties."""
    data, err = _load_or_404()
    if err:
        return err

    curves = data.get('property_hazard_curves', {})

    # Build basis table: property_id -> summary basis info
    basis_table = []
    for prop_id, pc in curves.items():
        summary = pc.get('summary', {})
        nearest = pc.get('nearest_gauges', [])

        entry = {
            'property_id': prop_id,
            'flood_count': pc.get('flood_count', 0),
            'max_depth_m': summary.get('max_depth_m', 0),
            'avg_basis_bps': summary.get('avg_basis_bps', 0),
            'flood_transmission_rate': summary.get('flood_transmission_rate', 0),
            'nearest_gauges': [
                {
                    'gauge_id': ng['gauge_id'],
                    'distance_km': ng.get('distance_km', 0),
                    'event_basis': ng.get('event_basis', 0),
                    'transmission_rate': ng.get('flood_transmission_rate', 0),
                }
                for ng in nearest
            ],
        }
        basis_table.append(entry)

    # Sort by basis (highest first)
    basis_table.sort(key=lambda x: x['avg_basis_bps'], reverse=True)

    return jsonify({
        'status': 'success',
        'count': len(basis_table),
        'basis_table': basis_table,
    })


# ---------------------------------------------------------------------------
# Synthetic Hazard Distance (propertyshd) and Elevation (propertyshe) routes
# ---------------------------------------------------------------------------

@propertyhc_bp.route('/propertyshd/summary', methods=['GET', 'OPTIONS'])
def propertyshd_summary():
    """Get portfolio-wide synthetic distance hazard summary."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertyshd.json')
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Synthetic distance hazard curves not yet generated. Run: python app.py port --propertyshd'
        }), 404
    return jsonify({'status': 'success', 'data': {
        'metadata': data.get('metadata', {}),
        'summary': data.get('summary', {}),
    }})


@propertyhc_bp.route('/propertyshe/summary', methods=['GET', 'OPTIONS'])
def propertyshe_summary():
    """Get portfolio-wide synthetic elevation hazard summary."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertyshe.json')
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Synthetic elevation hazard curves not yet generated. Run: python app.py port --propertyshe'
        }), 404
    return jsonify({'status': 'success', 'data': {
        'metadata': data.get('metadata', {}),
        'summary': data.get('summary', {}),
    }})


@propertyhc_bp.route('/properties/<prop_id>/shd', methods=['GET', 'OPTIONS'])
def property_shd(prop_id: str):
    """Get synthetic distance hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertyshd.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'Synthetic distance hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in shd curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})


@propertyhc_bp.route('/properties/<prop_id>/she', methods=['GET', 'OPTIONS'])
def property_she(prop_id: str):
    """Get synthetic elevation hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertyshe.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'Synthetic elevation hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in she curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})


@propertyhc_bp.route('/properties/<prop_id>/bri', methods=['GET', 'OPTIONS'])
def property_bri(prop_id: str):
    """Get BRI-adjusted (resilient) hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertybri.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'BRI-adjusted hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in bri curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})
