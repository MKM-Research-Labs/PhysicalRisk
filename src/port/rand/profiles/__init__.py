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
