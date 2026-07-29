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

"""Summary, single-property hazard, and basis routes."""


from flask import jsonify, request

from . import propertyhc_bp, _get_hazard_data, _load_or_404


@propertyhc_bp.route('/propertyhc/summary', methods=['GET', 'OPTIONS'])
def propertyhc_summary():
    """Get portfolio-wide property hazard summary."""
    data, err = _load_or_404(label='Property hazard curves. Run: python phys.py port --propertyhc')
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
