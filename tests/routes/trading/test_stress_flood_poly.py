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
"""The flood polynomial's parameters endpoint, which the port-stress screen evaluates."""

import json

from config.models import flood_poly_coeffs, flood_poly_level_floor


def test_serves_the_live_model(trading_client):
    resp = trading_client.get('/api/v1/trading/stress/flood-poly')
    assert resp.status_code == 200
    model = json.loads(resp.data)['model']
    assert model['model_id'] == 'flood-poly-v2'
    assert model['coeffs'] == list(flood_poly_coeffs)
    assert model['level_floor'] == flood_poly_level_floor
    assert len(model['terms']) == len(model['coeffs'])


def test_is_read_only(trading_client):
    assert trading_client.post('/api/v1/trading/stress/flood-poly').status_code == 405
