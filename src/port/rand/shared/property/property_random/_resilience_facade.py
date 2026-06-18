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

"""Shared installer for the per-catchment property-resilience facade.

Every catchment's ``property/property_random/resilience.py`` is identical: it
calls :func:`install` with its own ``__name__``. ``install`` populates that
module with the shared resilience engine
(``port.rand.shared.property_resilience``) plus the two per-catchment BRI
toggles read from the catchment profile, so there is ONE copy of the logic and
the toggle VALUES are single-sourced in the profile (not duplicated literals).

The toggles are set as REAL module attributes (not ``__getattr__`` hooks) so
the builder's ``getattr(resilience_module, 'PUBLISH_BRI_LETTER_RATINGS')`` and
``monkeypatch.setattr(module, 'BRI_SCORES_ENABLED', ...)`` both behave exactly
as they did with the old hand-written per-catchment shims.
"""

import sys
from typing import Any, Dict

from port.rand.profiles import get as _get_profile
from port.rand.shared import property_resilience as _shared


def _catchment_id_from_module(module_name: str) -> str:
    """Derive the catchment id from ``port.rand.<id>.property.…`` module name."""
    parts = module_name.split(".")
    if parts[:2] != ["port", "rand"] or len(parts) < 3:
        raise ValueError(
            f"resilience facade installed under unexpected module {module_name!r}")
    return parts[2]


def install(module_name: str) -> None:
    """Populate the calling catchment module with the shared resilience facade.

    Re-exports every public/private shared symbol, sets the two BRI toggles from
    the catchment's profile, and installs the two wrappers that forward the
    module's (monkeypatchable) toggle / weights into the shared implementation.
    """
    module = sys.modules[module_name]
    profile = _get_profile(_catchment_id_from_module(module_name))

    # Re-export every shared symbol (including underscore-prefixed privates that
    # tests import directly). Dunder names are skipped.
    for name, value in vars(_shared).items():
        if not name.startswith("__"):
            setattr(module, name, value)

    # Per-catchment BRI toggles, single-sourced from the profile.
    module.PUBLISH_BRI_LETTER_RATINGS = profile.PUBLISH_BRI_LETTER_RATINGS
    module.BRI_SCORES_ENABLED = profile.BRI_SCORES_ENABLED

    def apply_flood_resilience_score(
        property_record: Dict[str, Any],
        jitter_band: float = 0.05,
    ) -> Dict[str, Any]:
        """Forward to the shared implementation with this module's BRI flag.

        Reads ``BRI_SCORES_ENABLED`` off the module at call time so monkeypatch
        overrides take effect.
        """
        return _shared.apply_flood_resilience_score(
            property_record, jitter_band,
            bri_scores_enabled=module.BRI_SCORES_ENABLED,
        )

    def validate_weights() -> None:
        """Validate this module's ``SECTION_WEIGHTS`` sum to 1.0.

        Reads the module's ``SECTION_WEIGHTS`` at call time so a monkeypatched
        rebinding is observed.
        """
        return _shared.validate_weights(module.SECTION_WEIGHTS)

    module.apply_flood_resilience_score = apply_flood_resilience_score
    module.validate_weights = validate_weights
