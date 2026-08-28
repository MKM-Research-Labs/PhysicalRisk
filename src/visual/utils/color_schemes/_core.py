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

"""Resolve the design tokens into the hex values the visualisation layer draws with.

The ramps themselves — which token a flood band, a gauge status or an LTV bucket maps
to — live in :mod:`config.theme._status`. This is the Python edge that turns a token
into a colour, and it is deliberately thin: the class below holds no colour of its
own, so there is no second place for the console's appearance to be decided (coding
rule R7).

``FLOOD_RISK_COLORS`` and its siblings are still exposed as concrete hex mappings,
because callers and tests read them directly. They are now derived from the token
ramps at import time rather than written down, so a palette change reaches them.

Folium markers are the exception, and the reason ``get_folium_color_name`` and
``FLOOD_RISK_MARKERS`` exist: a Leaflet marker takes a colour *name* from a fixed
vocabulary, not a hex value, so no token can express one.
"""

from config.theme import (
    DEPTH_BAND_BOUNDS_M,
    DEPTH_BAND_TOKENS,
    DEPTH_BAND_TOP,
    FLOOD_RISK_MARKERS,
    FLOOD_RISK_TOKENS,
    LOAN_RISK_TOKENS,
    LTV_BAND_BOUNDS,
    LTV_BAND_TOKENS,
    LTV_BAND_TOP,
    OPERATIONAL_STATUS_TOKENS,
    PROPERTY_TYPE_TOKENS,
    STORM_INTENSITY_BOUNDS_MS,
    STORM_INTENSITY_TOKENS,
    STORM_INTENSITY_TOP,
    THEME,
)

from ._gradient import _GradientMixin


def _resolve(ramp: dict) -> dict:
    """Turn a value→token ramp into the value→hex mapping the drawing code wants.

    A token missing from the theme is a programming error rather than a runtime
    condition — it means a ramp names something the palette does not define — so it
    fails at import rather than painting an element in a plausible wrong colour.
    """
    missing = sorted({token for token in ramp.values() if token not in THEME})
    if missing:
        raise KeyError(f"ramp refers to undefined design tokens: {', '.join(missing)}")
    return {value: THEME[token] for value, token in ramp.items()}


def _band(value: float, bounds: tuple, top: str, inclusive: bool = True) -> str:
    """The first band *value* falls within, else *top*.

    *inclusive* selects whether a value sitting exactly on a bound belongs to the band
    below it or the one above. The three ramps disagree, and did before this package
    existed: depth and LTV band on ``<=``, storm intensity on ``<``, so a wind speed of
    exactly 30 m/s is "moderate" while a depth of exactly 0.5 m is "minor". That is an
    inconsistency rather than a decision, but correcting it would recolour markers at
    the boundaries, which is not what a styling migration should do. Preserved
    faithfully and now visible in one place instead of implied by two spellings of the
    same loop.
    """
    for bound, band in bounds:
        if (value <= bound) if inclusive else (value < bound):
            return band
    return top


class ColorSchemes(_GradientMixin):
    """Colour lookups for the visualisation system, resolved from ``config.theme``."""

    FLOOD_RISK_COLORS = _resolve(FLOOD_RISK_TOKENS)
    OPERATIONAL_STATUS_COLORS = _resolve(OPERATIONAL_STATUS_TOKENS)
    LOAN_RISK_COLORS = _resolve(LOAN_RISK_TOKENS)
    PROPERTY_TYPE_COLORS = _resolve(PROPERTY_TYPE_TOKENS)
    STORM_INTENSITY_COLORS = _resolve(STORM_INTENSITY_TOKENS)
    DEPTH_BAND_COLORS = _resolve(DEPTH_BAND_TOKENS)
    LTV_BAND_COLORS = _resolve(LTV_BAND_TOKENS)

    #: Folium's own marker vocabulary, which is not expressible as tokens.
    FLOOD_RISK_MARKER_NAMES = dict(FLOOD_RISK_MARKERS)

    @classmethod
    def get_flood_risk_color(cls, risk_level: str) -> str:
        """Hex colour for a flood risk band, falling back to the Unknown band."""
        return cls.FLOOD_RISK_COLORS.get(risk_level, cls.FLOOD_RISK_COLORS['Unknown'])

    @classmethod
    def get_operational_status_color(cls, status: str) -> str:
        """Hex colour for a gauge's operational status."""
        return cls.OPERATIONAL_STATUS_COLORS.get(
            status, cls.OPERATIONAL_STATUS_COLORS['Unknown'])

    @classmethod
    def get_loan_risk_color(cls, risk_level: str) -> str:
        """Hex colour for a loan risk grade."""
        return cls.LOAN_RISK_COLORS.get(risk_level, cls.LOAN_RISK_COLORS['Unknown'])

    @classmethod
    def get_property_type_color(cls, property_type: str) -> str:
        """Hex colour for a property type."""
        return cls.PROPERTY_TYPE_COLORS.get(
            property_type, cls.PROPERTY_TYPE_COLORS['Unknown'])

    @classmethod
    def get_wind_speed_color(cls, wind_speed: float) -> str:
        """Hex colour for a wind speed in m/s, banded per ``STORM_INTENSITY_BOUNDS_MS``."""
        band = _band(wind_speed, STORM_INTENSITY_BOUNDS_MS, STORM_INTENSITY_TOP,
                     inclusive=False)
        return cls.STORM_INTENSITY_COLORS[band]

    @classmethod
    def get_ltv_risk_color(cls, ltv_ratio: float) -> str:
        """Hex colour for a loan-to-value ratio, given as either 0–1 or 0–100."""
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100
        return cls.LTV_BAND_COLORS[_band(ltv_ratio, LTV_BAND_BOUNDS, LTV_BAND_TOP)]

    @classmethod
    def get_depth_color(cls, depth: float, max_depth: float = 5.0) -> str:
        """Hex colour for a flood depth in metres.

        *max_depth* is accepted and unused: the ramp is banded at fixed depths, not
        scaled to a maximum. The parameter is part of the published signature and
        callers pass it, so removing it belongs in its own change.
        """
        return cls.DEPTH_BAND_COLORS[_band(depth, DEPTH_BAND_BOUNDS_M, DEPTH_BAND_TOP)]

    @classmethod
    def get_folium_color_name(cls, hex_color: str) -> str:
        """The Folium marker name closest to a hex colour from one of the ramps.

        Reverse-resolved from the flood ramp, which is the ramp markers are drawn
        from. A colour that is not in it — including one from the gauge or loan ramps
        — falls back to ``blue``, as it always has.

        Matched case-insensitively. The ramps were spelled in uppercase hex before
        they became tokens, so a caller holding an older literal still resolves.
        """
        wanted = hex_color.lower() if hex_color else hex_color
        by_hex = {
            cls.FLOOD_RISK_COLORS[level]: name
            for level, name in cls.FLOOD_RISK_MARKER_NAMES.items()
            if level in cls.FLOOD_RISK_COLORS
        }
        return by_hex.get(wanted, _LEGACY_FOLIUM_NAMES.get(wanted, 'blue'))

    @classmethod
    def get_flood_risk_marker(cls, risk_level: str) -> str:
        """Folium marker name for a flood risk band.

        The direct lookup that ``visual.utils.risk_assessors.get_risk_color`` and
        ``visual.popups.popup_builder.get_risk_color`` each used to spell for
        themselves.
        """
        return cls.FLOOD_RISK_MARKER_NAMES.get(risk_level, 'blue')


# Marker names for colours outside the flood ramp. These come from the gauge, loan and
# property ramps, whose hex values ``get_folium_color_name`` has always accepted even
# though no marker is drawn from them. Kept so the function's behaviour is unchanged.
_LEGACY_FOLIUM_NAMES = {
    THEME['marker-green']: 'green',
    THEME['marker-amber']: 'orange',
    THEME['marker-red']: 'red',
    THEME['marker-red-alt']: 'red',
    THEME['marker-purple']: 'purple',
    THEME['marker-grey']: 'gray',
    THEME['marker-blue']: 'blue',
    THEME['marker-slate']: 'darkblue',
}


def get_risk_color(risk_level: str) -> str:
    """Hex colour for a flood risk band (backward compatibility)."""
    return ColorSchemes.get_flood_risk_color(risk_level)


def get_status_color(status: str) -> str:
    """Hex colour for a gauge status (backward compatibility)."""
    return ColorSchemes.get_operational_status_color(status)
