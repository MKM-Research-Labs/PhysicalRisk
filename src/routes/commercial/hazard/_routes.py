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

"""Commercial hazard route handlers (registered on commercial_bp).

Split out of ``routes/commercial/hazard.py`` so each file stays under the
300-line limit. The functional helpers (``_hazard_or_404``, ``_attach_fire``,
``_attach_seismic``) live in ``_helpers.py`` and are imported here.
"""

import json

from flask import jsonify, request

from config import config

from ..blueprint import commercial_bp
from ._helpers import _attach_fire, _attach_seismic, _hazard_or_404


@commercial_bp.route('/commercial/<prop_id>/hazard', methods=['GET', 'OPTIONS'])
def commercial_hazard(prop_id: str):
    """Full hazard curve + PRS pricing for one commercial asset."""
    data, err = _hazard_or_404('commercialhc.json',
                               'Commercial hazard curves')
    if err:
        return err

    curves = data.get('property_hazard_curves', {})
    asset_data = curves.get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': (f'Commercial asset {prop_id} not found in hazard '
                        f'curves (may have < 3 flood events)'),
        }), 404

    # Attach terrain grid + num_storms from metadata so the PRS pricer
    # can do zone repricing and so the panel knows the denominator used
    # by the generator (avoids the previous hard-coded 20000 default).
    metadata = data.get('metadata', {})
    meta_out = {}
    if metadata.get('terrain_grid'):
        meta_out['terrain_grid'] = metadata['terrain_grid']
    if metadata.get('num_storms') is not None:
        meta_out['num_storms'] = metadata['num_storms']
    if meta_out:
        asset_data['_metadata'] = meta_out

    # Read-time joins: fold the independent fire and seismic legs into the
    # spread_decomposition so the PRS pricer waterfall can render FIRE and
    # SEISMIC rows and the all-in root-sum-of-squares coupon.
    _attach_fire(asset_data, prop_id)
    _attach_seismic(asset_data, prop_id)

    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/she', methods=['GET', 'OPTIONS'])
def commercial_she(prop_id: str):
    """Synthetic elevation hazard curve for one commercial asset."""
    data, err = _hazard_or_404('commercialshe.json',
                               'Commercial synthetic elevation hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in SHE curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/shd', methods=['GET', 'OPTIONS'])
def commercial_shd(prop_id: str):
    """Synthetic distance hazard curve for one commercial asset."""
    data, err = _hazard_or_404('commercialshd.json',
                               'Commercial synthetic distance hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in SHD curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/bri', methods=['GET', 'OPTIONS'])
def commercial_bri(prop_id: str):
    """BRI-adjusted (resilient) hazard curve for one commercial asset.

    Mirrors ``/properties/<id>/bri`` so the shared PRS-pricer panel can read
    the resilient flood count for any asset type.
    """
    data, err = _hazard_or_404('commercialbri.json',
                               'Commercial BRI-adjusted hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in BRI curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/win', methods=['GET', 'OPTIONS'])
def commercial_win(prop_id: str):
    """Wind-only peril hazard curve for one commercial asset.

    Mirrors ``/properties/<id>/win`` — wind-only PRS spread (commercialwin.json).
    """
    data, err = _hazard_or_404('commercialwin.json',
                               'Commercial wind-only hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in win curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/faw', methods=['GET', 'OPTIONS'])
def commercial_faw(prop_id: str):
    """Flood-AND-wind peril hazard curve for one commercial asset.

    Mirrors ``/properties/<id>/faw`` (commercialfaw.json).
    """
    data, err = _hazard_or_404('commercialfaw.json',
                               'Commercial flood-AND-wind hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in faw curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/fow', methods=['GET', 'OPTIONS'])
def commercial_fow(prop_id: str):
    """Flood-OR-wind peril hazard curve for one commercial asset.

    Mirrors ``/properties/<id>/fow`` (commercialfow.json).
    """
    data, err = _hazard_or_404('commercialfow.json',
                               'Commercial flood-OR-wind hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in fow curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/bow', methods=['GET', 'OPTIONS'])
def commercial_bow(prop_id: str):
    """BRI-OR-wind peril hazard curve for one commercial asset.

    Mirrors ``/properties/<id>/bow`` (commercialbow.json) — the union of the
    BRI-resilient flood and wind.
    """
    data, err = _hazard_or_404('commercialbow.json',
                               'Commercial BRI-OR-wind hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in bow curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>/baw', methods=['GET', 'OPTIONS'])
def commercial_baw(prop_id: str):
    """BRI-AND-wind peril hazard curve for one commercial asset.

    Mirrors ``/properties/<id>/baw`` (commercialbaw.json) — the intersection of
    the BRI-resilient flood and wind.
    """
    data, err = _hazard_or_404('commercialbaw.json',
                               'Commercial BRI-AND-wind hazard')
    if err:
        return err
    asset_data = data.get('property_hazard_curves', {}).get(prop_id)
    if not asset_data:
        return jsonify({
            'status': 'error',
            'message': f'Commercial asset {prop_id} not in baw curves',
        }), 404
    return jsonify({'status': 'success', 'data': asset_data})


@commercial_bp.route('/commercial/<prop_id>', methods=['GET', 'OPTIONS'])
def commercial_record(prop_id: str):
    """Return the bare commercial asset record by PropertyID.

    Mirrors GET /api/v1/properties/<id> — used by the hazard panel
    to look up the display address when the preloader hasn't cached
    the name. Payload shape: ``{'status': 'success', 'property': {...}}``
    where ``property`` is the full record (CommercialAsset wrapper
    intact, so the panel can read ``CommercialAsset.Location.BuildingName``).
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    try:
        with open(config.get_input_path('commercial.json'), 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'message': 'commercial.json not found for the active catchment',
        }), 404

    for record in data.get('commercial_assets', []):
        ca = record.get('CommercialAsset', {})
        if ca.get('Header', {}).get('PropertyID') == prop_id:
            return jsonify({'status': 'success', 'property': record})

    return jsonify({
        'status': 'error',
        'message': f'Commercial asset {prop_id} not found',
    }), 404
