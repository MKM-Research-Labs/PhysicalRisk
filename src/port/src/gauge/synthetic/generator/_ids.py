# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Synthetic gauge identifier scheme."""

import hashlib

SYNTH_PREFIX = "SYNTH"


def _synth_gauge_id(ga_id: str, gb_id: str, alpha: float) -> str:
    """Deterministic synthetic gauge ID from flanking IDs + alpha."""
    key = f"{ga_id}:{gb_id}:{alpha:.3f}"
    h = hashlib.md5(key.encode()).hexdigest()[:8]
    return f"{SYNTH_PREFIX}-{h}"
