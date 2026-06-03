# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Halong property resilience — thin shim over the catchment-shared module.

All resilience logic and calibration lives in
``port.rand._shared.property_resilience``. This module re-exports every public
and private symbol from there (so existing imports keep working unchanged) and
sets the two Halong-specific toggles:

  - PUBLISH_BRI_LETTER_RATINGS = True   → Halong publishes certified BRI letter
    ratings (computed from the resilience checklist). Read by the shared builder.
  - BRI_SCORES_ENABLED = True           → the five numeric BRIScore fields are
    computed normally (Halong owns a certified BRI regime).

``apply_flood_resilience_score`` is wrapped so it reads the LOCAL
``BRI_SCORES_ENABLED`` flag at call time and forwards it to the shared
implementation — preserving the historical contract that monkeypatching this
module's flag changes the behaviour.
"""

from typing import Any, Dict

from port.rand._shared import property_resilience as _shared

# Re-export every symbol from the shared module (including underscore-prefixed
# privates that tests import directly). Dunder names are skipped.
globals().update({k: v for k, v in vars(_shared).items() if not k.startswith("__")})


# Halong-specific toggles (see module docstring).
PUBLISH_BRI_LETTER_RATINGS: bool = True
BRI_SCORES_ENABLED: bool = True


def apply_flood_resilience_score(
    property_record: Dict[str, Any],
    jitter_band: float = 0.05,
) -> Dict[str, Any]:
    """Forward to the shared implementation with the local BRI flag.

    Reads ``BRI_SCORES_ENABLED`` from this module at call time so monkeypatch
    overrides take effect.
    """
    return _shared.apply_flood_resilience_score(
        property_record, jitter_band, bri_scores_enabled=BRI_SCORES_ENABLED
    )


def validate_weights() -> None:
    """Validate this module's ``SECTION_WEIGHTS`` sum to 1.0.

    Reads the local ``SECTION_WEIGHTS`` at call time so a monkeypatched
    rebinding of this module's attribute is observed.
    """
    return _shared.validate_weights(SECTION_WEIGHTS)
