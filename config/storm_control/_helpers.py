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

"""Storm-control helper functions."""

import importlib
import logging
import sys
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _patch_module(
    module: Any,
    flat: Dict[str, Any],
    mapping: Dict[str, str],
    label: str,
) -> None:
    """Set attributes on *module* for every key present in *flat*."""
    for json_key, attr in mapping.items():
        if json_key in flat:
            setattr(module, attr, flat[json_key])
            logger.debug("%s.%s = %r", label, attr, flat[json_key])


def _safe_getattr(mod_path: str, attr: str, default: Any) -> Any:
    """Import *mod_path* and return *attr*, or *default* on failure."""
    mod = sys.modules.get(mod_path)
    if mod is not None:
        return getattr(mod, attr, default)
    try:
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr, default)
    except ImportError:
        return default


def _enum_keys_to_str(d: dict) -> dict:
    """Convert any enum keys to their ``.value`` string form."""
    return {(k.value if hasattr(k, "value") else str(k)): v for k, v in d.items()}


def _str_keys_to_gap_type(d: dict) -> dict:
    """Convert string keys back to GapType enum values."""
    try:
        from src.port.src.storm_multi.core.data_structures import GapType
        return {GapType(k): tuple(v) for k, v in d.items()}
    except ImportError:
        return {k: tuple(v) for k, v in d.items()}
