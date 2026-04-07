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
                    show_peak: bool = False) -> str:
    """
    Return the JavaScript expression that builds a storm dropdown option label.

    Canonical format (base):
        {name} ({storm_id}) | {category} | {N} severe | {N}mm

    With show_warning=True  (port_stress — endpoint provides gauges_warning):
        {name} ({storm_id}) | {category} | {N} severe | {N} warn | {N}mm

    With show_peak=True  (trading desk stress — endpoint provides peak_level_m):
        {name} ({storm_id}) | {category} | {N} severe | {N}mm | peak {N}m

    Args:
        var:          JavaScript variable name for the storm object (default 's').
                      Use 'r' for gsa_timeline.py which iterates with variable 'r'.
        show_warning: Include gauges_warning count (default False).
        show_peak:    Include peak water level reading (default False).

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
