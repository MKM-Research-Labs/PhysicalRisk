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

"""Fire and seismic peril-model outputs for the active catchment.

Serves the per-asset fire (MKM-FIRE-001) and seismic model outputs. Read-only;
returns an empty payload when the catchment has not been run through those models.
Data access goes through the ``database`` package (coding rule R6).
"""

from json import JSONDecodeError

from flask import Blueprint, jsonify

from config import config
from database import get_fire_results, get_seismic_results

perils_bp = Blueprint('perils', __name__)


@perils_bp.route('/fire', methods=['GET'])
def fire():
    """Per-asset fire-model outcomes (commercial portfolio). A corrupt or
    absent model file yields an empty payload."""
    try:
        return jsonify(get_fire_results(config.catchment_id) or {})
    except (OSError, JSONDecodeError):
        return jsonify({})


@perils_bp.route('/seismic', methods=['GET'])
def seismic():
    """Per-asset seismic-model outcomes (commercial portfolio). A corrupt or
    absent model file yields an empty payload."""
    try:
        return jsonify(get_seismic_results(config.catchment_id) or {})
    except (OSError, JSONDecodeError):
        return jsonify({})
