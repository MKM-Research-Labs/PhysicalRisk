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

"""
Stages of the ``generate_stress_storms`` pipeline.

The orchestrator in ``stress_storms.py`` is composed of four sequential
stages, each implemented here:

  1. ``load_storm_metadata``    — optional storms.json lookup
  2. ``scan_gauge_responses``   — fan-in gauge-files → per-storm responses
  3. ``build_storm_records``    — assemble per-storm records with metadata
  4. ``write_storm_files``      — per-storm JSON files + lightweight index
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Set

from config.port import (
    STORM_ID_PREFIX,
    STRESS_STORM_DEFAULT_DURATION_HOURS,
    STRESS_STORM_DEFAULT_PEAK_POSITION,
)

logger = logging.getLogger(__name__)


def load_storm_metadata(storms_json_path) -> Dict[str, Dict]:
    """Optional storms.json lookup for metadata enrichment.

    Supports both ``storm_sequences.json`` (sequences[].storms[]) and
    flat ``storms.json`` (storms[]) formats.  Returns ``{}`` if the
    path is None / missing / unreadable.
    """
    storm_meta: Dict[str, Dict] = {}
    if not storms_json_path or not Path(storms_json_path).exists():
        return storm_meta
    try:
        raw = json.loads(Path(storms_json_path).read_text())
        if "sequences" in raw:
            for seq in raw["sequences"]:
                seq_id = seq.get("sequence_id", "")
                # Index individual storms within each sequence
                for s in seq.get("storms", []):
                    sid = s.get("storm_id", "")
                    if sid:
                        # Carry sequence-level metadata down to the storm
                        entry = dict(s)
                        entry.setdefault("intensity_category",
                                         seq.get("intensity_category", ""))
                        # Normalise precipitation key
                        if "effective_precipitation_mm" not in entry:
                            entry["effective_precipitation_mm"] = (
                                seq.get("total_precipitation_mm",
                                        s.get("precipitation_mm", 0.0)))
                        storm_meta[sid] = entry
                # Also index by sequence_id (for sequence-level lookups)
                if seq_id and seq_id not in storm_meta:
                    seq_entry = dict(seq)
                    seq_entry.setdefault("effective_precipitation_mm",
                                         seq.get("total_precipitation_mm", 0.0))
                    storm_meta[seq_id] = seq_entry
        else:
            for s in raw.get("storms", raw if isinstance(raw, list) else []):
                sid = s.get("storm_id", "")
                if sid:
                    storm_meta[sid] = s
        logger.info("Loaded metadata for %d storms from %s",
                    len(storm_meta), Path(storms_json_path).name)
    except Exception as exc:
        logger.warning("Could not read storms metadata: %s", exc)
    return storm_meta


def _iter_gauge_records_from_files(gauge_files: List[Path]):
    """Yield ``(gauge_id, gaugets_doc)`` from on-disk gaugets/GAUGE-*.json files,
    skipping any that fail to parse (the file backend stores gaugets as files)."""
    for gf in gauge_files:
        try:
            data = json.loads(gf.read_text())
        except Exception as exc:
            logger.warning("Skipping %s: %s", gf.name, exc)
            continue
        # gauge_id is the file's top-level field; individual responses don't repeat it
        yield data.get("gauge_id", gf.stem), data


def _iter_gauge_records_from_seam():
    """Yield ``(gauge_id, gaugets_doc)`` from the database seam for the active
    catchment (the Postgres backend stores gaugets as rows, so no files exist)."""
    import database
    catchment = database.active_catchment()
    for gid in database.iter_gauge_timeseries_ids(catchment):
        if not gid.startswith("GAUGE-"):
            continue
        data = database.get_gauge_timeseries(catchment, gid)
        yield data.get("gauge_id", gid), data


def scan_gauge_responses(
    gaugets_dir: Path,
) -> tuple[Dict[str, List[Dict]], Set[str]]:
    """Scan the per-gauge timeseries and build storm_id → list of responses.

    Reads from ``gaugets_dir`` when GAUGE-*.json files are present (the file backend
    writes them there); otherwise falls back to the database seam for the active
    catchment (the Postgres backend stores gaugets as rows, so the directory is
    empty). Raises if neither source yields a gauge.

    Returns:
        (all_responses, alert_storm_ids):
            - all_responses[storm_id] = list of per-gauge response dicts
            - alert_storm_ids = set of storm IDs where any gauge exceeded alert
    """
    gauge_files = sorted(gaugets_dir.glob("GAUGE-*.json"))
    if gauge_files:
        # Files present (file backend): all-corrupt is tolerated -> empty result.
        records = _iter_gauge_records_from_files(gauge_files)
        raise_if_none = False
    else:
        # No files (Postgres backend, or genuinely empty): read the seam, and treat
        # an empty seam as the legacy "nothing to scan" error.
        records = _iter_gauge_records_from_seam()
        raise_if_none = True

    all_responses: Dict[str, List[Dict]] = {}
    alert_storm_ids: Set[str] = set()
    n_scanned = 0

    for gauge_id, data in records:
        n_scanned += 1
        responses = data.get("storm_responses", {}).get("responses", [])
        for resp in responses:
            sid = resp.get("storm_id", "")
            if not sid:
                continue
            # Attach gauge_id so the assembled record is self-contained
            enriched = dict(resp)
            enriched["gauge_id"] = gauge_id
            all_responses.setdefault(sid, []).append(enriched)
            if resp.get("exceeded_alert", False):
                alert_storm_ids.add(sid)

    if raise_if_none and n_scanned == 0:
        raise FileNotFoundError(
            f"No GAUGE-*.json files in {gaugets_dir} and no gauge timeseries in the "
            f"database seam")

    logger.info(
        "Scanned %d gauges: %d total storm IDs, %d breached alert",
        n_scanned, len(all_responses), len(alert_storm_ids),
    )
    return all_responses, alert_storm_ids


def build_storm_records(
    alert_storm_ids: Set[str],
    all_responses: Dict[str, List[Dict]],
    storm_meta: Dict[str, Dict],
    derive_intensity_category: Callable[[int, int], str],
    make_name: Callable[[int], str],
) -> List[Dict]:
    """Assemble per-storm records (trigger summary + metadata + responses).

    Sorts the result descending by (gauges_severe, gauges_warning, max_peak).
    """
    storms: List[Dict] = []
    name_idx = 0

    for storm_id in alert_storm_ids:
        gauge_responses = all_responses.get(storm_id, [])

        # Trigger summary
        g_alert = sum(1 for r in gauge_responses if r.get("exceeded_alert"))
        g_warning = sum(1 for r in gauge_responses if r.get("exceeded_warning"))
        g_severe = sum(1 for r in gauge_responses if r.get("exceeded_severe"))

        if g_severe:
            max_trigger = "severe"
        elif g_warning:
            max_trigger = "warning"
        else:
            max_trigger = "alert"

        trigger_summary = {
            "gauges_alert":    g_alert,
            "gauges_warning":  g_warning,
            "gauges_severe":   g_severe,
            "gauges_impacted": g_alert,
            "max_trigger":     max_trigger,
        }

        # Storm metadata — prefer storms.json, fall back to config defaults
        meta = storm_meta.get(storm_id, {})
        duration_hours = int(
            meta.get("duration_hours", STRESS_STORM_DEFAULT_DURATION_HOURS)
        )
        peak_position = float(
            meta.get("peak_position", STRESS_STORM_DEFAULT_PEAK_POSITION)
        )
        precip_mm = float(meta.get("effective_precipitation_mm", 0.0))
        intensity_category = meta.get(
            "intensity_category",
            derive_intensity_category(g_severe, g_warning),
        )
        name = meta.get("name") or make_name(name_idx)
        name_idx += 1

        storms.append({
            "storm_id":                  storm_id,
            "name":                      name,
            "intensity_category":        intensity_category,
            "duration_hours":            duration_hours,
            "peak_position":             peak_position,
            "effective_precipitation_mm": precip_mm,
            "trigger_summary":           trigger_summary,
            "gauge_responses":           gauge_responses,
        })

    # Sort: most severe first, then most warnings, then highest peak
    def _sort_key(s: Dict):
        ts = s["trigger_summary"]
        max_peak = max(
            (r.get("peak_level_m", 0.0) for r in s["gauge_responses"]),
            default=0.0,
        )
        return (-ts["gauges_severe"], -ts["gauges_warning"], -max_peak)

    storms.sort(key=_sort_key)
    return storms


def write_storm_files(storms: List[Dict], output_dir: Path) -> None:
    """Write per-storm JSON files + lightweight ``_index.json``.

    Wipes ``output_dir`` first to avoid stale files leaking through from
    a previous (longer) run.
    """
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()

    # Build index entries (no gauge_responses — keeps index small)
    index_entries = []
    for storm in storms:
        ts = storm["trigger_summary"]
        max_peak = max(
            (r.get("peak_level_m", 0.0) for r in storm["gauge_responses"]),
            default=0.0,
        )
        # Per-storm file: full record including gauge_responses
        storm_file = output_dir / f"{storm['storm_id']}.json"
        storm_file.write_text(json.dumps(storm, indent=2))

        # Which gauges exceeded alert? (used for gauge-filtered storm lists)
        gauge_ids_alert = [
            r["gauge_id"] for r in storm["gauge_responses"]
            if r.get("exceeded_alert")
        ]

        # Index entry: lightweight metadata for UI dropdowns
        index_entries.append({
            "storm_id":                   storm["storm_id"],
            "name":                       storm["name"],
            "intensity_category":         storm["intensity_category"],
            "duration_hours":             storm["duration_hours"],
            "peak_position":              storm["peak_position"],
            "effective_precipitation_mm": storm["effective_precipitation_mm"],
            "trigger_summary":            ts,
            "max_peak_level_m":           round(max_peak, 3),
            "gauge_ids_alert":            gauge_ids_alert,
        })

    # Write index
    index_payload = {
        "description": (
            "Stress test storm index — lightweight metadata for all storms that "
            "caused a flood alert breach at one or more Thames gauges. "
            "Full per-gauge data is in individual {storm_id}.json files."
        ),
        "generated_at": generated_at,
        "storm_id_prefix": STORM_ID_PREFIX,
        "total_storms": len(storms),
        "storms": index_entries,
    }
    index_path = output_dir / "_index.json"
    index_path.write_text(json.dumps(index_payload, indent=2))
