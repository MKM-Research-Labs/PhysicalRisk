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
