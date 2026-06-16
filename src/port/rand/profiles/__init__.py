# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Per-catchment rand-generation profiles.

Each profile module (``profiles/<catchment_id>.py``) holds ONLY the
catchment-specific DATA the shared generators need (seismic ranges, BRI
toggles, commercial archetype tables, …). The shared generators read the
active catchment's profile via ``active_profile()`` so there is a single
implementation; adding a catchment is a new profile module, not a forked tree.
"""

import importlib


def get(catchment_id: str):
    """Return the profile module for *catchment_id*."""
    return importlib.import_module(f"port.rand.profiles.{catchment_id}")


def active_profile():
    """Return the profile for the active catchment (config.CATCHMENT).

    Function-local config import: rand modules are loaded *by* config, so a
    top-level import risks a circular import.
    """
    from config import config
    return get(config.CATCHMENT)
