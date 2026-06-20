# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

from .backend import active_backend
from ._helpers import load_or


def get_property_timeseries(catchment, property_id, mode=DEFAULT_MODE):
    return load_or("property_timeseries", catchment, property_id, mode=mode)

def iter_property_timeseries_ids(catchment, mode=DEFAULT_MODE) -> Iterator[str]:
    return active_backend().iter_keys("property_timeseries", catchment, mode=mode)

def save_property_timeseries(catchment, property_id, payload, mode=DEFAULT_MODE):
    active_backend().save("property_timeseries", catchment, payload, property_id, mode=mode)

def property_timeseries_exists(catchment, mode=DEFAULT_MODE) -> bool:
    """True if the property-timeseries collection has been generated (even if empty)."""
    return active_backend().has_collection("property_timeseries", catchment, mode=mode)

def get_portfolio_flood_summary(catchment, mode=DEFAULT_MODE):
    return load_or("portfolio_flood_summary", catchment, mode=mode)

def get_commercial_timeseries(catchment, asset_id, mode=DEFAULT_MODE):
    return load_or("commercial_timeseries", catchment, asset_id, mode=mode)

def iter_commercial_timeseries_ids(catchment, mode=DEFAULT_MODE) -> Iterator[str]:
    return active_backend().iter_keys("commercial_timeseries", catchment, mode=mode)

def commercial_timeseries_exists(catchment, mode=DEFAULT_MODE) -> bool:
    """True if the commercial-timeseries collection has been generated (even if empty)."""
    return active_backend().has_collection("commercial_timeseries", catchment, mode=mode)

def save_commercial_timeseries(catchment, asset_id, payload, mode=DEFAULT_MODE):
    active_backend().save("commercial_timeseries", catchment, payload, asset_id, mode=mode)

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
