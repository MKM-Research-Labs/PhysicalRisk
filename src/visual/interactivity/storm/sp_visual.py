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

"""
Storm portfolio — Visual (chart) tab sub-module.

Chart.js multi-line time-series showing gauge water levels and
properties flooded over the 60-hour storm window, with gauge
dropdown filter for toggling individual gauge visibility.
"""

from .sp_visual_dom import get_dom_js
from .sp_visual_data import get_data_js
from .sp_visual_render import get_render_js
from .sp_visual_toggle import get_toggle_js


def get_js() -> str:
    """Return JS fragment for visual/chart tab (injected into parent IIFE)."""
    return get_dom_js() + get_data_js() + get_render_js() + get_toggle_js()
