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

"""Public API — hazard curves (gauge / property / commercial, by scenario mode)."""

from __future__ import annotations

from config.data_layout import DEFAULT_MODE

from .backend import active_backend
from ._helpers import load_or


def get_gauge_hazard_curves(catchment):
    return load_or("gauge_hazard_curve", catchment)

def save_gauge_hazard_curves(catchment, payload):
    active_backend().save("gauge_hazard_curve", catchment, payload)

def get_property_hazard_curves(catchment, mode=DEFAULT_MODE):
    return load_or("property_hazard_curve", catchment, mode=mode)

def save_property_hazard_curves(catchment, payload, mode=DEFAULT_MODE):
    active_backend().save("property_hazard_curve", catchment, payload, mode=mode)

def get_commercial_hazard_curves(catchment, mode=DEFAULT_MODE):
    return load_or("commercial_hazard_curve", catchment, mode=mode)

def save_commercial_hazard_curves(catchment, payload, mode=DEFAULT_MODE):
    active_backend().save("commercial_hazard_curve", catchment, payload, mode=mode)
