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

"""Typhoon stage — boundary adapter between the active catchment's
typhoon configuration and the catchment-agnostic typhoon model.

This stage is the only file in the codebase that knows both:
  - how to discover a catchment's tc.py (the production config path)
  - how to call the typhoon pipeline (the model entry point)

It deliberately does no math: the catchment file constructs the
CatchmentTyphoonConfig via its build_typhoon_config() function, and the
pipeline runs the SMC engine + wind-field model end-to-end.
"""

from ._loaders import (
    _load_catchment_typhoon_config,
    _load_storm_event_drivers,
    _load_property_portfolio,
    _severity_quantiles,
)
from ._run import run_typhoon
from ._run_all import run_all

__all__ = [
    "run_all",
    "run_typhoon",
    "_load_catchment_typhoon_config",
    "_load_storm_event_drivers",
    "_load_property_portfolio",
    "_severity_quantiles",
]
