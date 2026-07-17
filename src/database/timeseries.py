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

"""Public API — timeseries (property / commercial / gauge, plus gauge history)."""

from __future__ import annotations

from typing import Iterator

from config.data_layout import DEFAULT_MODE

from ._helpers import load_or
from .backend import active_backend


def get_property_timeseries(catchment, property_id, mode=DEFAULT_MODE):
    return load_or("property_timeseries", catchment, property_id, mode=mode)

def iter_property_timeseries_ids(catchment, mode=DEFAULT_MODE) -> Iterator[str]:
    return active_backend().iter_keys("property_timeseries", catchment, mode=mode)

def save_property_timeseries(catchment, property_id, payload, mode=DEFAULT_MODE):
    active_backend().save("property_timeseries", catchment, payload, property_id, mode=mode)

def clear_property_timeseries(catchment, mode=DEFAULT_MODE):
    """Remove the whole property-timeseries collection for *mode* (full-rewrite reset)."""
    active_backend().clear("property_timeseries", catchment, mode=mode)

def property_timeseries_exists(catchment, mode=DEFAULT_MODE) -> bool:
    """True if the property-timeseries collection has been generated (even if empty)."""
    return active_backend().has_collection("property_timeseries", catchment, mode=mode)

def get_portfolio_flood_summary(catchment, mode=DEFAULT_MODE):
    return load_or("portfolio_flood_summary", catchment, mode=mode)

def save_portfolio_flood_summary(catchment, payload, mode=DEFAULT_MODE):
    active_backend().save("portfolio_flood_summary", catchment, payload, mode=mode)

def get_commercial_portfolio_flood_summary(catchment, mode=DEFAULT_MODE):
    return load_or("commercial_portfolio_flood_summary", catchment, mode=mode)

def save_commercial_portfolio_flood_summary(catchment, payload, mode=DEFAULT_MODE):
    active_backend().save("commercial_portfolio_flood_summary", catchment, payload, mode=mode)

def get_commercial_timeseries(catchment, asset_id, mode=DEFAULT_MODE):
    return load_or("commercial_timeseries", catchment, asset_id, mode=mode)

def iter_commercial_timeseries_ids(catchment, mode=DEFAULT_MODE) -> Iterator[str]:
    return active_backend().iter_keys("commercial_timeseries", catchment, mode=mode)

def commercial_timeseries_exists(catchment, mode=DEFAULT_MODE) -> bool:
    """True if the commercial-timeseries collection has been generated (even if empty)."""
    return active_backend().has_collection("commercial_timeseries", catchment, mode=mode)

def save_commercial_timeseries(catchment, asset_id, payload, mode=DEFAULT_MODE):
    active_backend().save("commercial_timeseries", catchment, payload, asset_id, mode=mode)

def clear_commercial_timeseries(catchment, mode=DEFAULT_MODE):
    """Remove the whole commercial-timeseries collection for *mode* (full-rewrite reset)."""
    active_backend().clear("commercial_timeseries", catchment, mode=mode)

def get_gauge_timeseries(catchment, gauge_id):
    return load_or("gauge_timeseries", catchment, gauge_id)

def gauge_timeseries_exists(catchment) -> bool:
    """True if the gauge-timeseries collection (``gaugets``) has been generated."""
    return active_backend().has_collection("gauge_timeseries", catchment)

def iter_gauge_timeseries_ids(catchment) -> Iterator[str]:
    return active_backend().iter_keys("gauge_timeseries", catchment)

def save_gauge_timeseries(catchment, gauge_id, payload):
    active_backend().save("gauge_timeseries", catchment, payload, gauge_id)

def delete_gauge_timeseries(catchment, gauge_id):
    active_backend().delete("gauge_timeseries", catchment, gauge_id)

def get_gauge_history(catchment, gauge_id):
    return load_or("gauge_history", catchment, gauge_id)

def iter_gauge_history_ids(catchment) -> Iterator[str]:
    return active_backend().iter_keys("gauge_history", catchment)

def save_gauge_history(catchment, gauge_id, payload):
    active_backend().save("gauge_history", catchment, payload, gauge_id)

def delete_gauge_history(catchment, gauge_id):
    active_backend().delete("gauge_history", catchment, gauge_id)
