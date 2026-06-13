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

"""Shared data-loading helpers for the property hazard-curve routes."""

import json

from flask import jsonify, request

from config import config


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
