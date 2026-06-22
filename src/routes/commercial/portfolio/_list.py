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

"""Commercial asset / loan list endpoints (startup-preloader counts)."""

from flask import jsonify

import database
from config import config

from ..blueprint import commercial_bp


@commercial_bp.route('/commercial', methods=['GET'])
def list_commercial():
    """List all commercial assets in the active catchment.

    Mirrors GET /api/v1/properties — used by the startup preloader for
    the bottom-left status popup count and to build a PropertyID →
    BuildingName / address lookup for the right-click menu titles.

    Response shape::

        {"status": "success", "count": N, "commercial_assets": [...]}
    """
    assets = database.list_commercial(config.catchment_id)
    return jsonify({
        'status': 'success',
        'count': len(assets),
        'commercial_assets': assets,
    })


@commercial_bp.route('/commercial-loans', methods=['GET'])
def list_commercial_loans():
    """List all commercial loans in the active catchment.

    Mirrors GET /api/v1/rloans — used by the startup preloader for
    the count stat.

    Response shape::

        {"status": "success", "count": N, "commercial_loans": [...]}
    """
    loans = database.list_commercial_loans(config.catchment_id)
    return jsonify({
        'status': 'success',
        'count': len(loans),
        'commercial_loans': loans,
    })
