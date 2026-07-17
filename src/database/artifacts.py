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

"""The artifact registry — structure only. Every literal (filename, directory,
mode suffix) comes from ``config.data_layout`` per rule 1; this module just assembles
them into typed specs and derives per-key filenames from the configured patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from config import data_layout as dl

DOCUMENT = "document"
KEYED = "keyed"
BLOB = "blob"


def _const(path: str) -> Callable[[str], str]:
    return lambda mode: path


@dataclass(frozen=True)
class Spec:
    kind: str
    location: Callable[[str], str]            # mode -> relpath (file for DOCUMENT, dir otherwise)
    name_pattern: str = dl.KEYED_FILENAME     # per-key filename pattern (keyed/blob)


_REGISTRY: dict[str, Spec] = {
    # Portfolio entities (documents)
    **{name: Spec(DOCUMENT, _const(fname)) for name, fname in dl.PORTFOLIO_FILES.items()},

    # Hazard curves (documents; property/commercial vary by mode)
    "gauge_hazard_curve": Spec(DOCUMENT, _const(dl.GAUGE_HAZARD_FILE)),
    "property_hazard_curve": Spec(DOCUMENT, lambda mode: dl.PROPERTY_HAZARD_FILES[mode]),
    "commercial_hazard_curve": Spec(DOCUMENT, lambda mode: dl.COMMERCIAL_HAZARD_FILES[mode]),

    # Storms / sequences / summaries (documents)
    "storm_sequences": Spec(DOCUMENT, _const(dl.STORM_SEQUENCES_FILE)),
    "sequence_summary": Spec(DOCUMENT, _const(dl.SEQUENCES_SUMMARY_FILE)),
    "storm_sequences_legacy": Spec(DOCUMENT, _const(dl.LEGACY_STORM_SEQUENCES_FILE)),
    "stress_storm_index": Spec(DOCUMENT, _const(dl.STRESS_STORM_INDEX_FILE)),
    "stress_storms_legacy": Spec(DOCUMENT, _const(dl.LEGACY_STRESS_STORMS_FILE)),
    "portfolio_flood_summary": Spec(
        DOCUMENT, lambda mode: f"{dl.PROPERTY_TS_DIRS[mode]}/{dl.PORTFOLIO_FLOOD_SUMMARY_FILE}"),
    "commercial_portfolio_flood_summary": Spec(
        DOCUMENT, lambda mode: f"{dl.COMMERCIAL_TS_DIRS[mode]}/{dl.PORTFOLIO_FLOOD_SUMMARY_FILE}"),

    # Perils (documents)
    "fire_results": Spec(DOCUMENT, _const(dl.FIRE_RESULTS_FILE)),
    "seismic_results": Spec(DOCUMENT, _const(dl.SEISMIC_RESULTS_FILE)),

    # Trading (documents)
    "market_state": Spec(DOCUMENT, _const(dl.MARKET_STATE_FILE)),
    "trade_marks": Spec(DOCUMENT, _const(dl.TRADE_MARKS_FILE)),
    "hazard_curve_history": Spec(DOCUMENT, _const(dl.HAZARD_CURVE_HISTORY_FILE)),
    "trade_pnl_history": Spec(DOCUMENT, _const(dl.TRADE_PNL_HISTORY_FILE)),

    # Timeseries (keyed; vary by mode)
    "property_timeseries": Spec(KEYED, lambda mode: dl.PROPERTY_TS_DIRS[mode]),
    "commercial_timeseries": Spec(KEYED, lambda mode: dl.COMMERCIAL_TS_DIRS[mode]),
    "gauge_timeseries": Spec(KEYED, _const(dl.GAUGE_TS_DIR)),
    "gauge_history": Spec(KEYED, _const(dl.GAUGE_HISTORY_DIR),
                          name_pattern=dl.GAUGE_HISTORY_FILENAME),

    # Keyed event/record sets
    "stress_storm": Spec(KEYED, _const(dl.STRESS_STORMS_DIR)),
    "sequence_gauge": Spec(KEYED, _const(dl.SEQUENCE_GAUGE_DIR)),
    "prs_trade": Spec(KEYED, _const(dl.PRS_DIR)),
    "eod_snapshot": Spec(KEYED, _const(dl.EOD_DIR)),
    "typhoon_event": Spec(KEYED, _const(dl.TYPHOON_DAMAGE_DIR)),

    # Binary model artifacts (blob, keyed)
    "classifier": Spec(BLOB, _const(dl.CLASSIFIERS_DIR),
                       name_pattern=dl.CLASSIFIER_FILENAME),

    # Classifier training metadata (documents alongside the model blobs)
    "classifier_training_summary": Spec(DOCUMENT, _const(dl.CLASSIFIER_TRAINING_SUMMARY_FILE)),
    "classifier_timings": Spec(DOCUMENT, _const(dl.CLASSIFIER_TIMINGS_FILE)),
}


def spec(artifact: str) -> Spec:
    try:
        return _REGISTRY[artifact]
    except KeyError:
        raise KeyError(
            f"Unknown artifact {artifact!r}. Add it to config.data_layout + "
            f"database/artifacts.py (do not reach around the package)."
        ) from None


def names() -> list[str]:
    """All registered artifact names."""
    return sorted(_REGISTRY)


# ── per-key filename derivation (from the configured pattern; no literals) ────
def _split(pattern: str) -> tuple[str, str]:
    prefix, suffix = pattern.split("{key}")
    return prefix, suffix


def filename(sp: Spec, key: str) -> str:
    """Filename for a keyed/blob record, e.g. ``gauge_GAUGE-1_hd.json``."""
    prefix, suffix = _split(sp.name_pattern)
    return f"{prefix}{key}{suffix}"


def key_of(sp: Spec, name: str) -> str:
    """Inverse of :func:`filename` — recover the key from a filename."""
    prefix, suffix = _split(sp.name_pattern)
    end = len(name) - len(suffix) if suffix else len(name)
    return name[len(prefix):end]


def glob_ext(sp: Spec) -> str:
    """File extension to glob for, derived from the configured pattern."""
    suffix = _split(sp.name_pattern)[1]
    return "." + suffix.rsplit(".", 1)[-1]
