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
