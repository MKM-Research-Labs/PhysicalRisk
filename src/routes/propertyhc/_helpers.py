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

"""Shared data-loading helpers for the property hazard-curve routes."""

from flask import jsonify, request

from config import config
from config.data_layout import PROPERTY_HAZARD_FILES

import database

# filename -> scenario mode (inverse of the config data-layout map)
_FILE_TO_MODE = {fname: mode for mode, fname in PROPERTY_HAZARD_FILES.items()}


def _get_hazard_data(filename: str = 'propertyhc.json') -> dict:
    """Load property hazard curves for the scenario mapped to *filename*, via the
    database package (coding rule R6). Unknown filename -> None."""
    mode = _FILE_TO_MODE.get(filename)
    if mode is None:
        return None
    return database.get_property_hazard_curves(config.catchment_id, mode)


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
