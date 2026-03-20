# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Shared regex patterns, constants and helpers for naming convention tests."""

import re
from pathlib import Path

# =============================================================================
# Agreed regex patterns (documented protocol)
# =============================================================================

GAUGE_ID_RE  = re.compile(r'^GAUGE-[0-9a-f]{8}$')
PROP_ID_RE   = re.compile(r'^PROP-[0-9a-f]{8}$')
MORT_ID_RE   = re.compile(r'^MORT-[0-9a-f]{8}$')
STORM_ID_RE  = re.compile(r'^STORM-[0-9a-f]{8}$')
PRS_ID_RE    = re.compile(r'^PRS-[0-9a-fA-F]{8}$')  # book uses .upper()

# Files that build storm dropdowns — must use pipe-separated format
_STORM_DROPDOWN_FILES = [
    'src/visual/interactivity/storm/sp_table.py',
    'src/visual/interactivity/storm/fa_render.py',
    'src/visual/interactivity/gauge/gaugehc/ghc_stress_setup.py',
    'src/visual/interactivity/gauge/gaugesa/gsa_timeline.py',
    'src/visual/interactivity/trading/port_stress/setup.py',
    'src/visual/interactivity/trading/stress/setup.py',
]


def _read_source(rel_path: str) -> str:
    root = Path(__file__).resolve().parent.parent.parent
    return (root / rel_path).read_text()
