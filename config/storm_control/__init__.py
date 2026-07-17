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

"""
Storm Sequence Control — JSON overlay for storm stress parameters.

Loads ``storm_control.json`` from the catchment input directory and patches
the live Python config modules (``config.port``, ``config.models``, and
generator-local constants) so that the rest of the codebase continues to
use ``from config import X`` without any changes.
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


from config.storm_control._mappings import (
    _CONFIG_MODELS_KEYS,
    _CONFIG_PORT_KEYS,
    _CONTROL_FILENAME,
    _GENERATOR_PATCHES,
)
from config.storm_control._helpers import (
    _enum_keys_to_str,
    _patch_module,
    _safe_getattr,
    _str_keys_to_gap_type,
)
from config.storm_control._defaults import get_defaults


def _resolve_path(catchment_id: str = "thames") -> Path:
    """Return path to ``storm_control.json`` for the given catchment."""
    from config import config as _cfg
    return _cfg.get_input_dir() / _CONTROL_FILENAME


def load_storm_control(catchment_id: str = "thames") -> Dict[str, Any]:
    """Read storm_control.json and return parsed dict (empty if missing)."""
    path = _resolve_path(catchment_id)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_storm_control(
    data: Dict[str, Any],
    catchment_id: str = "thames",
) -> None:
    """Write *data* to storm_control.json."""
    path = _resolve_path(catchment_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info("storm_control.json saved to %s", path)


def apply_storm_control(catchment_id: str = "thames") -> None:
    """Load storm_control.json and patch live config modules."""
    data = load_storm_control(catchment_id)
    if not data:
        logger.debug("No storm_control.json found — using Python defaults")
        return

    sections = data.get("sections", {})
    if not sections:
        return

    import config.port as cp
    import config.models as cm

    # Flatten all section params into one dict for lookup
    flat: Dict[str, Any] = {}
    for section_params in sections.values():
        flat.update(section_params)

    # Patch config.port
    _patch_module(cp, flat, _CONFIG_PORT_KEYS, "config.port")

    # Patch config.models
    _patch_module(cm, flat, _CONFIG_MODELS_KEYS, "config.models")

    # Patch config package re-exports (from config import X)
    config_pkg = sys.modules.get("config")
    if config_pkg:
        for json_key, attr in _CONFIG_PORT_KEYS.items():
            if json_key in flat and hasattr(config_pkg, attr):
                setattr(config_pkg, attr, flat[json_key])
                logger.debug("config.%s patched", attr)
        for json_key, attr in _CONFIG_MODELS_KEYS.items():
            if json_key in flat and hasattr(config_pkg, attr):
                setattr(config_pkg, attr, flat[json_key])
                logger.debug("config.%s patched", attr)

    # Patch generator-local constants
    for json_key, (mod_path, attr) in _GENERATOR_PATCHES.items():
        if json_key not in flat:
            continue
        value = flat[json_key]
        # Convert string-keyed dicts back to enum-keyed where needed
        if json_key == "gap_params":
            value = _str_keys_to_gap_type(value)
        elif json_key == "duration_params":
            # duration_params uses tuple values
            value = {k: tuple(v) for k, v in value.items()}
        elif json_key == "base_intensity_params":
            value = {k: tuple(v) for k, v in value.items()}

        mod = sys.modules.get(mod_path)
        if mod is not None:
            setattr(mod, attr, value)
            logger.debug("%s.%s patched from storm_control.json", mod_path, attr)
        else:
            try:
                mod = importlib.import_module(mod_path)
                setattr(mod, attr, value)
                logger.debug("%s.%s patched (lazy import)", mod_path, attr)
            except ImportError:
                logger.debug("Could not import %s — skipping patch", mod_path)

    logger.info("storm_control.json applied (%d params)", len(flat))
