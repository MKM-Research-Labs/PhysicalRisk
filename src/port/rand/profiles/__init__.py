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
