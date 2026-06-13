# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Combined JS fragment for the gauge-hazard-curve stress-test charts."""

from . import probability, pnl, surface


def get_js() -> str:
    """Return combined JS fragment for all stress test charts."""
    return (probability.get_js() +
            pnl.get_js() +
            surface.get_js())
