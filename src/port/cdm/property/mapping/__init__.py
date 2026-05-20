# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Property CDM mapping package.

Composes create_mapping() from per-category flatten functions. Each module
mirrors the corresponding schema/ module.
"""

from ..schema import DEFAULT_ELEVATION
from .contents import flatten_contents
from .hazard_profile import flatten_hazard_profile
from .header import flatten_header
from .ratings import flatten_ratings
from .resilience import flatten_resilience
from .risk_assessment import flatten_risk_assessment
from .transactions import flatten_transactions


def create_mapping(prop: dict, default_elevation: float = DEFAULT_ELEVATION) -> dict:
    """
    Flatten a nested property CDM record into a snake_case dict.

    Args:
        prop:              Nested property data in CDM format.
        default_elevation: Fallback when GroundLevelMeters is absent.

    Returns:
        Flat dict with snake_case keys.  None-valued keys are omitted.

    Raises:
        ValueError: If the mapping transformation fails unexpectedly.
    """
    try:
        flat: dict = {}
        flat.update(flatten_header(prop))
        flat.update(flatten_risk_assessment(prop, default_elevation))
        flat.update(flatten_ratings(prop))
        flat.update(flatten_hazard_profile(prop))
        flat.update(flatten_resilience(prop))
        flat.update(flatten_transactions(prop))
        flat.update(flatten_contents(prop))
        return {k: v for k, v in flat.items() if v is not None}
    except Exception as exc:
        raise ValueError(f"Error creating property mapping: {exc}") from exc
