# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""Fire and seismic peril-model outputs for the active catchment.

Serves the per-asset fire (MKM-FIRE-001) and seismic model outputs that the
port stage writes to ``<input>/fire/fire.json`` and ``<input>/seismic/
seismic.json``. Read-only; returns an empty payload when the catchment has not
been run through those models.
"""

import json

from flask import Blueprint, jsonify

from config import config

perils_bp = Blueprint('perils', __name__)


def _load_peril(subdir: str, filename: str) -> dict:
    path = config.get_input_dir() / subdir / filename
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


@perils_bp.route('/fire', methods=['GET'])
def fire():
    """Per-asset fire-model outcomes (commercial portfolio)."""
    return jsonify(_load_peril('fire', 'fire.json'))


@perils_bp.route('/seismic', methods=['GET'])
def seismic():
    """Per-asset seismic-model outcomes (commercial portfolio)."""
    return jsonify(_load_peril('seismic', 'seismic.json'))
