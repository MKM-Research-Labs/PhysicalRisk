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
Stress Test — setup sub-module.

State variables, DOM construction, data loading, gauge/storm dropdown
population and change handlers, chart tab switching.

On-demand classifier training UI is in training_ui.py.
"""

from config.format import percentile_apply_js as _pct_apply

from . import setup_dom, setup_data, setup_charts


def get_js() -> str:
    """Return JavaScript fragment for stress test state, DOM, and loading."""
    return f"""
{_pct_apply()}
            // ==============================================================
            // Tab 7: Stress Test — CDS-in-stress cash pricing
            // ==============================================================
            var tdStressGauges = null;
            var tdStressStorms = null;
            var tdStressResult = null;
            var tdStressChart = null;
            var tdStressChartTab = 0;  // 0 = Flood Probability, 1 = Stress P&L, 2 = Surface
            var tdStressGaugeHint = null;

{setup_dom.get_js()}
{setup_data.get_js()}
{setup_charts.get_js()}
"""
