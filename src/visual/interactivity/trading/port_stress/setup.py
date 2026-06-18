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
Port Stress — setup sub-module.

State variables, DOM construction, storm loading, dropdown population,
sub-tab switching, and stats bar update.
All rendering sub-tabs are imported and concatenated here.
"""

from config.format import percentile_selector_html as _pct_html
from config.format import storm_option_js as _storm_opt

from visual.interactivity._jsbundle import js_static

from . import gauge_pnl, pfloods, portfolio_pnl, severity


def get_js() -> str:
    """Return JavaScript fragment for the full Port Stress tab (Tab 8)."""
    return (
        _get_setup_js()
        + pfloods.get_js()
        + portfolio_pnl.get_js()
        + gauge_pnl.get_js()
        + severity.get_js()
    )


def _get_setup_js() -> str:
    """Return JavaScript for state, DOM, loading, and sub-tab switching."""
    return js_static('trading/port_stress/setup.js').replace(
        '__STORM_OPT__', _storm_opt('s', show_warning=True)
    ).replace('__PCT_HTML__', _pct_html('ps-pct-sel', 'ps-storm-sel'))
