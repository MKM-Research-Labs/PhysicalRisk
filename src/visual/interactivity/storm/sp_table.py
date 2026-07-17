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
Storm portfolio — Table tab assembler.

Returns the JS body for the Table tab, composed from sibling sub-modules:

- sp_table_blotter:    Residential property blotter sub-tab
- sp_table_commercial: Commercial asset blotter sub-tab
- sp_table_damage:     Flood Damage (combined residential + commercial) sub-tab
- sp_table_wind:       Wind Damage sub-tab (model pending)
- sp_table_mortgage:   Loan/Mortgage sub-tab (Flood + Wind LTV/Remaining)
- sp_table_summary:    Summary report card

This file owns the cross-sub-tab state, DOM creation, sub-tab switching,
and storm-list / portfolio-impact loaders (which reads the
``window._preStorms`` startup cache).
"""


from config.format import storm_option_js as _storm_opt

from visual.interactivity._jsbundle import js_static

from . import (
    sp_table_blotter,
    sp_table_commercial,
    sp_table_damage,
    sp_table_mortgage,
    sp_table_summary,
    sp_table_wind,
)


def get_js() -> str:
    """Return JS fragment for table tab (injected into parent IIFE).

    The state / DOM / loader JavaScript lives in ``static/js/sp-table.js``;
    sub-tab fragments come from sibling modules.
    """
    js = (
        js_static('sp-table.js')
        + sp_table_blotter.get_js()
        + sp_table_commercial.get_js()
        + sp_table_damage.get_js()
        + sp_table_wind.get_js()
        + sp_table_mortgage.get_js()
        + sp_table_summary.get_js()
    )
    return js.replace('__STORM_OPT__', _storm_opt('s'))
