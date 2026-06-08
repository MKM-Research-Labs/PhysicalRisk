# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Functional helpers for the commercial hazard routes.

Holds the read-time loaders and the independent-peril joins the route handlers
(``_routes.py``) use: the hazard-file loader, the OPTIONS/404 guard, and the
fire and seismic read-time joins. Kept out of the package ``__init__``, which is
purely for package assembly.
"""

import json

from flask import jsonify, request

from config import config


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


def _attach_seismic(asset_data: dict, prop_id: str) -> None:
    """Read-time join: fold the seismic model's collapse leg into the asset's
    spread_decomposition so the PRS pricer waterfall can render a SEISMIC row.

    Reads seismic/seismic.json (written by the port seismic stage), matches the
    asset by asset_id == PropertyID, and writes ``seismic_spread_bps`` plus a
    ``peril_outcomes.seismic`` {count, spread_bps} entry. The spread is the
    model's full-collapse leg (n_DS3 / n_sim x LGE x 10,000), taken directly
    from the model output rather than recomputed. A no-op when seismic.json is
    absent or the asset has no seismic result, so pre-seismic portfolios render
    exactly as before.
    """
    seismic_path = config.get_input_dir() / 'seismic' / 'seismic.json'
    if not seismic_path.exists():
        return
    try:
        with open(seismic_path, 'r') as f:
            seismic = json.load(f)
    except (OSError, ValueError):
        return

    record = None
    for a in seismic.get('assets', []):
        if a.get('asset_id') == prop_id:
            record = a
            break
    if record is None:
        return

    spread_bps = record.get('seismic_spread_bps')
    if spread_bps is None:
        return
    n_ds3 = (record.get('damage_state_counts') or {}).get('3', 0)
    spread_bps = round(spread_bps, 1)

    sd = asset_data.setdefault('spread_decomposition', {})
    sd['seismic_spread_bps'] = spread_bps
    sd.setdefault('peril_outcomes', {})['seismic'] = {
        'count': n_ds3,
        'spread_bps': spread_bps,
    }
    # Also expose the raw seismic summary so the panel/tooltips can show context.
    asset_data['seismic'] = {
        'n_sim': record.get('n_sim', 0),
        'n_events': record.get('n_events', 0),
        'zone': record.get('zone'),
        'site_class': record.get('site_class'),
        'rating': record.get('rating'),
        'no_collapse_rate': record.get('no_collapse_rate', 0.0),
        'loss_frequency': record.get('loss_frequency', 0.0),
        'pml_475': record.get('pml_475', 0.0),
        'pml_2475': record.get('pml_2475', 0.0),
        'mean_resilience_index': record.get('mean_resilience_index', 0.0),
        'n_cascade_fire': record.get('n_cascade_fire', 0),
    }
