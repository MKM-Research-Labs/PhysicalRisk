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

"""Public API — fitted event arrival rates and their calibration provenance.

One document per catchment, keyed by gauge. Written by the frequency model
(MKM-EF-001); read by anything that needs to know how often a qualifying event
arrives, and on what evidence.
"""

from __future__ import annotations

from .backend import active_backend
from ._helpers import load_or


def get_frequency_rates(catchment):
    """Return the fitted rate document for *catchment*, or None."""
    return load_or("frequency_rates", catchment)

def save_frequency_rates(catchment, payload):
    """Persist the fitted rate document for *catchment*."""
    active_backend().save("frequency_rates", catchment, payload)
