# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Synthetic gauge generator package."""

from ._ids import SYNTH_PREFIX, _synth_gauge_id
from ._core import SyntheticGaugeGenerator

__all__ = ["SyntheticGaugeGenerator", "SYNTH_PREFIX", "_synth_gauge_id"]
