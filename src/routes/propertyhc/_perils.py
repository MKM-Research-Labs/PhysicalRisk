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

"""Synthetic-distance, elevation, BRI, and wind-coupled peril routes."""


from flask import jsonify, request

from . import propertyhc_bp, _get_hazard_data, _load_or_404


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
            'message': 'Synthetic distance hazard curves not yet generated. Run: python phys.py port --propertyshd'
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
            'message': 'Synthetic elevation hazard curves not yet generated. Run: python phys.py port --propertyshe'
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


# ---------------------------------------------------------------------------
# Wind-coupled peril scenario routes (win / faw / fow / bow / baw)
#   win  — wind-only PRS spread (propertywin.json)
#   faw  — flood AND wind  (propertyfaw.json)
#   fow  — flood OR wind   (propertyfow.json)
#   bow  — BRI OR wind     (propertybow.json)
#   baw  — BRI AND wind    (propertybaw.json)
# Mirror /properties/<id>/{shd,she,bri}: same property_hazard_curves shape.
# ---------------------------------------------------------------------------

@propertyhc_bp.route('/properties/<prop_id>/win', methods=['GET', 'OPTIONS'])
def property_win(prop_id: str):
    """Get wind-only peril hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertywin.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'Wind-only hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in win curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})


@propertyhc_bp.route('/properties/<prop_id>/faw', methods=['GET', 'OPTIONS'])
def property_faw(prop_id: str):
    """Get flood-AND-wind peril hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertyfaw.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'Flood-AND-wind hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in faw curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})


@propertyhc_bp.route('/properties/<prop_id>/fow', methods=['GET', 'OPTIONS'])
def property_fow(prop_id: str):
    """Get flood-OR-wind peril hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertyfow.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'Flood-OR-wind hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in fow curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})


@propertyhc_bp.route('/properties/<prop_id>/bow', methods=['GET', 'OPTIONS'])
def property_bow(prop_id: str):
    """Get BRI-OR-wind peril hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertybow.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'BRI-OR-wind hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in bow curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})


@propertyhc_bp.route('/properties/<prop_id>/baw', methods=['GET', 'OPTIONS'])
def property_baw(prop_id: str):
    """Get BRI-AND-wind peril hazard curve for one property."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = _get_hazard_data('propertybaw.json')
    if not data:
        return jsonify({'status': 'error', 'message': 'BRI-AND-wind hazard curves not yet generated'}), 404
    prop_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not prop_data:
        return jsonify({'status': 'error', 'message': f'Property {prop_id} not found in baw curves'}), 404
    return jsonify({'status': 'success', 'data': prop_data})
