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
Storm portfolio — VaR tab assembler.

Property Damage / Mortgage Impairment distribution histogram with
VaR and Expected Shortfall annotations at 95% and 99.9% confidence.

Histogram rendering lives in the sibling ``sp_var_chart`` module and
is concatenated into the same IIFE.
"""

from visual.interactivity._jsbundle import js_static

from . import sp_var_chart


def get_js() -> str:
    """Return JS fragment for VaR tab (injected into parent IIFE)."""
    state_dom_metrics_load = js_static('storm/sp_var.js')
    return state_dom_metrics_load + sp_var_chart.get_js()
