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
Property hazard curve — PRS Pricing tab sub-module.

Input controls, analytical semi-annual cashflow pricer,
6-component PRS rendering with basis waterfall, and trade commit.

Sub-modules:
- phc_prs_pricer: Survival interpolation + cashflow computation
- phc_prs_render: 6-component PRS rendering with basis waterfall
"""

from visual.interactivity._jsbundle import js_static

from . import phc_prs_pricer, phc_prs_render


def get_js() -> str:
    """Return JS fragment for PRS pricing tab (injected into parent IIFE)."""
    return (
        js_static('property/phc_prs_head.js')
        + phc_prs_pricer.get_js()
        + phc_prs_render.get_js()
        + js_static('property/phc_prs_tail.js')
    )
