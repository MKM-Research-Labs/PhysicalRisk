# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial hazard-curve / PRS-pricing endpoints + asset-record lookup.

  GET /api/v1/commercial/<prop_id>/hazard
  GET /api/v1/commercial/<prop_id>/she
  GET /api/v1/commercial/<prop_id>/shd
  GET /api/v1/commercial/<prop_id>/bri
  GET /api/v1/commercial/<prop_id>/win   (wind-only peril)
  GET /api/v1/commercial/<prop_id>/faw   (flood AND wind)
  GET /api/v1/commercial/<prop_id>/fow   (flood OR wind)
  GET /api/v1/commercial/<prop_id>/bow   (BRI OR wind)
  GET /api/v1/commercial/<prop_id>/baw   (BRI AND wind)
      Mirror the /properties/<id>/{hazard,she,shd,bri,win,faw,fow,bow,baw} routes —
      return the per-asset hazard curve + PRS pricing payload. Read from
      commercialhc.json / commercialshe.json / commercialshd.json /
      commercialbri.json / commercialwin.json / commercialfaw.json /
      commercialfow.json / commercialbow.json / commercialbaw.json. All use the
      SAME top-level key `property_hazard_curves` keyed by PropertyID (CPROP-…).

  GET /api/v1/commercial/<prop_id>
      Returns the bare commercial asset record by PropertyID, used by the
      hazard panel for address lookups.
"""

import json

from flask import jsonify, request

from config import config

from .blueprint import commercial_bp


def _load_commercial_hazard(filename: str):
    """Load a commercial hazard file (None if missing on disk)."""
    path = config.get_input_dir() / filename
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return json.load(f)


def _hazard_or_404(filename: str, label: str):
    """OPTIONS preflight / file-missing handler."""
    if request.method == 'OPTIONS':
        return None, jsonify({'status': 'ok'})
    data = _load_commercial_hazard(filename)
    if not data:
        return None, (jsonify({
            'status': 'error',
            'message': f'{label} not yet generated',
        }), 404)
    return data, None


# Full-conflagration fire is priced as a credit event: the fair PRS spread for a
# total-loss-on-event swap is approximately the annual event probability times
# the loss given event. We seed LGE at 100% (a full conflagration destroys the
# building), so fire_spread_bps = pnr_frequency * 10_000. "Full conflagration"
# is defined as a fire that crossed the point of no return (n_point_of_no_return)
# — the uncontrollable fires that run to partial OR total loss.
_FIRE_LOSS_GIVEN_EVENT = 1.0  # seed; tunable when fire config gains an LGE knob


def _attach_fire(asset_data: dict, prop_id: str) -> None:
    """Read-time join: fold the fire model's conflagration leg into the
    asset's spread_decomposition so the PRS pricer waterfall can render it.

    Reads fire/fire.json (written by the port fire stage), matches the asset by
    asset_id == PropertyID, and writes ``fire_spread_bps`` plus a
    ``peril_outcomes.fire_conflagration`` {count, spread_bps} entry. A no-op when
    fire.json is absent or the asset has no fire result, so pre-fire portfolios
    render exactly as before.
    """
    fire_path = config.get_input_dir() / 'fire' / 'fire.json'
    if not fire_path.exists():
        return
    try:
        with open(fire_path, 'r') as f:
            fire = json.load(f)
    except (OSError, ValueError):
        return

    record = None
    for a in fire.get('assets', []):
        if a.get('asset_id') == prop_id:
            record = a
            break
    if record is None:
        return

    n_sim = record.get('n_sim') or 0
    n_pnr = record.get('n_point_of_no_return') or 0
    pnr_frequency = (n_pnr / n_sim) if n_sim else 0.0
    fire_spread_bps = round(pnr_frequency * _FIRE_LOSS_GIVEN_EVENT * 10_000.0, 1)

    sd = asset_data.setdefault('spread_decomposition', {})
    sd['fire_spread_bps'] = fire_spread_bps
    sd.setdefault('peril_outcomes', {})['fire_conflagration'] = {
        'count': n_pnr,
        'spread_bps': fire_spread_bps,
    }
    # Also expose the raw fire summary so the panel/tooltips can show context.
    asset_data['fire'] = {
        'n_sim': n_sim,
        'n_fires': record.get('n_fires', 0),
        'n_point_of_no_return': n_pnr,
        'n_total': record.get('n_total', 0),
        'pnr_frequency': pnr_frequency,
        'total_loss_frequency': record.get('total_loss_frequency', 0.0),
        'containment_rate': record.get('containment_rate', 0.0),
    }


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

    # Read-time join: fold the fire model's full-conflagration leg into the
    # spread_decomposition so the PRS pricer waterfall can render a FIRE row.
    _attach_fire(asset_data, prop_id)

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
