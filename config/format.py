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
Central display format definitions for MKM Research Labs PRS Platform.

All UI display strings that are shared across multiple panels are defined
here as Python functions returning JavaScript expressions.  Visual modules
import these instead of hardcoding strings, ensuring every dropdown, label,
or tooltip uses exactly the same format.

Usage in visual modules (plain-string get_js functions):
    from config.format import storm_option_js

    def get_js() -> str:
        return '''
            ...
            opt.textContent = __STORM_OPT__;
            ...
        '''.replace('__STORM_OPT__', storm_option_js('s'))

Usage in visual modules (f-string get_js functions):
    from config.format import storm_option_js

    def get_js() -> str:
        _opt = storm_option_js('s')
        return f'''
            ...
            opt.textContent = {_opt};
            ...
        '''
"""


def storm_option_js(var: str = 's',
                    show_warning: bool = False,
                    show_peak: bool = False,
                    show_typhoon: bool = True) -> str:
    """
    Return the JavaScript expression that builds a storm dropdown option label.

    Canonical format (base):
        {name} ({storm_id}) | {category} | {N} severe | {N}mm

    With show_warning=True  (port_stress — endpoint provides gauges_warning):
        {name} ({storm_id}) | {category} | {N} severe | {N} warn | {N}mm

    With show_peak=True  (trading desk stress — endpoint provides peak_level_m):
        {name} ({storm_id}) | {category} | {N} severe | {N}mm | peak {N}m

    With show_typhoon=True (default — endpoint provides typhoon block):
        Adds '[TYPHOON evt_id | family vmax m/s]' suffix when s.typhoon is
        non-null. Storms without a typhoon link get no suffix and look
        identical to the base format.

    Args:
        var:           JavaScript variable name for the storm object (default 's').
                       Use 'r' for gsa_timeline.py which iterates with variable 'r'.
        show_warning:  Include gauges_warning count (default False).
        show_peak:     Include peak water level reading (default False).
        show_typhoon:  Append the typhoon suffix when present (default True).
                       Set False on legacy callers whose endpoint doesn't
                       populate s.typhoon — the suffix would just produce
                       'undefined' otherwise.

    Returns:
        JavaScript expression string, safe for embedding directly in JS source.
    """
    v = var
    parts = [
        f"({v}.name || {v}.storm_id)",
        f"+ ' (' + {v}.storm_id + ') | '",
        f"+ ({v}.intensity_category || '?')",
        f"+ ' | '",
        f"+ ({v}.gauges_severe || 0)",
        f"+ ' severe | '",
    ]
    if show_warning:
        parts += [
            f"+ ({v}.gauges_warning || 0)",
            f"+ ' warn | '",
        ]
    parts.append(f"+ Math.round({v}.effective_precipitation_mm || 0) + 'mm'")
    if show_peak:
        parts.append(f"+ ' | peak ' + ({v}.peak_level_m || 0).toFixed(2) + 'm'")
    if show_typhoon:
        # Suffix is only emitted when the storm has a typhoon block —
        # ternary keeps non-typhoon rows clean.
        parts.append(
            f"+ ({v}.typhoon ? "
            f"  '  \\u26A1 TYPHOON ' + {v}.typhoon.event_id + ' ('"
            f"  + ({v}.typhoon.scenario_family || '?') + ', '"
            f"  + (({v}.typhoon.peak_wind_ms || 0).toFixed(1)) + ' m/s)'"
            f"  : '')"
        )

    return ' '.join(parts)


def gauge_title_js(name_var: str = 'gName', id_var: str = 'gaugeId') -> str:
    """
    Return the JavaScript expression that builds a gauge panel title.

    Canonical format:
        {GaugeName} ({GaugeID})

    Falls back to just {GaugeID} if name is empty.

    Args:
        name_var: JavaScript variable holding the gauge name string.
        id_var:   JavaScript variable holding the gauge ID string.

    Returns:
        JavaScript expression string, safe for embedding directly in JS source.
    """
    return f"({name_var} ? {name_var} + ' (' + {id_var} + ')' : {id_var})"


def gauge_title_py(gauge_name: str, gauge_id: str) -> str:
    """
    Return the formatted gauge display label for Python contexts (reports, tooltips).

    Canonical format:
        {GaugeName} ({GaugeID})

    Falls back to just {GaugeID} if name is empty.

    Args:
        gauge_name: Gauge name string (e.g. "Thames Westminster Bridge").
        gauge_id:   Gauge ID string (e.g. "GAUGE-ca0c20c2").

    Returns:
        Formatted display string.
    """
    if gauge_name:
        return f"{gauge_name} ({gauge_id})"
    return gauge_id


def property_title_js(name_var: str = 'propName',
                      id_var: str = 'propertyId') -> str:
    """
    Return the JavaScript expression that builds a property display label.

    Canonical format:
        {Address} ({PropertyID})

    Falls back to just {PropertyID} if name/address is empty.

    Args:
        name_var: JavaScript variable holding the property address/name string.
        id_var:   JavaScript variable holding the property ID string.

    Returns:
        JavaScript expression string, safe for embedding directly in JS source.
    """
    return f"({name_var} ? {name_var} + ' (' + {id_var} + ')' : {id_var})"


def percentile_apply_js() -> str:
    """Return the shared JS function ``_applyPercentile(pctSelId, stormSelId)``.

    This must be included **once** on the page (typically in the trading-desk
    init block).  Each storm selector location then just calls it from its
    own "Go" button.
    """
    return """
            window._applyPercentile = function(pctSelId, stormSelId) {
                var pctSel = document.getElementById(pctSelId);
                var stormSel = document.getElementById(stormSelId);
                if (!pctSel || !stormSel) return;
                var pct = parseFloat(pctSel.value);
                if (isNaN(pct)) return;
                var opts = stormSel.options;
                var nDropdown = opts.length - 1;
                if (nDropdown <= 0) return;
                // Use total storm catalogue size (set via data-total attribute)
                // so percentile maps across the full 20,000 storms, not just
                // the filtered subset in the dropdown.
                var nTotal = parseInt(stormSel.getAttribute('data-total')) || nDropdown;
                var targetIdx = Math.max(0, Math.floor(nTotal * (1 - pct / 100)));
                // Clamp to dropdown range (filtered list may be shorter)
                var idx = Math.min(targetIdx, nDropdown - 1);
                stormSel.selectedIndex = idx + 1;
                if (typeof stormSel.onchange === 'function') stormSel.onchange();
                else stormSel.dispatchEvent(new Event('change'));
            };
"""


def percentile_selector_html(pct_id: str, storm_sel_id: str) -> str:
    """Return an HTML fragment for a percentile ``<select>`` + Go button.

    Args:
        pct_id:       DOM id for the percentile ``<select>``.
        storm_sel_id: DOM id of the storm ``<select>`` to jump into.

    Returns:
        HTML string safe for embedding in JS string concatenation.
    """
    # Build option tags: 50-99 in 1% steps, then 99.1-99.9 in 0.1% steps
    opts = []
    for p in range(50, 100):
        sel = ' selected' if p == 99 else ''
        opts.append(f'<option value="{p}"{sel}>{p}%</option>')
    for t in range(1, 10):
        v = f"99.{t}"
        opts.append(f'<option value="{v}">{v}%</option>')
    options_html = ''.join(opts)

    return (
        f'<span style="font-size:11px;font-weight:600;color:#333;margin-left:8px;">Percentile:</span>'
        f'<select id="{pct_id}" style="padding:4px 8px;font-size:11px;'
        f'border:1px solid #ccc;border-radius:3px;">'
        f'{options_html}</select>'
        f'<button onclick="_applyPercentile(&#39;{pct_id}&#39;,&#39;{storm_sel_id}&#39;)" '
        f'style="padding:4px 12px;font-size:11px;font-weight:600;border:1px solid #1565c0;'
        f'border-radius:3px;background:#e3f2fd;color:#1565c0;cursor:pointer;">Go</button>'
    )


def property_title_py(address: str, property_id: str) -> str:
    """
    Return the formatted property display label for Python contexts (reports, tooltips).

    Canonical format:
        {Address} ({PropertyID})

    Falls back to just {PropertyID} if address is empty.

    Args:
        address:     Property address string (e.g. "128 Horseferry Road").
        property_id: Property ID string (e.g. "PROP-e5c80163").

    Returns:
        Formatted display string.
    """
    if address:
        return f"{address} ({property_id})"
    return property_id
