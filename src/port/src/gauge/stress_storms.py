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
Stress Storms Catalogue Generator.

Builds data/input/<catchment>/stress_storms.json from the current gaugets/
directory.  This replaces the old stress.py pipeline and must be run after
every gaugets regeneration to keep the two datasets in sync.

Algorithm
---------
1. Scan every gaugets/GAUGE-*.json and build a storm_id → gauge_responses
   lookup for all storms.
2. Identify the subset of storm_ids where at least one gauge exceeded alert.
3. For each qualifying storm:
   - Collect gauge_responses (all 52 gauges, not just alert-breaching ones).
   - Derive trigger_summary: gauges_alert / warning / severe counts and
     max_trigger level.
   - Assign intensity_category from the trigger_summary counts.
   - Generate a display name.
4. Sort descending by: gauges_severe → gauges_warning → max peak_level_m.
5. Write stress_storms.json.

Storm metadata (duration_hours, peak_position, effective_precipitation_mm)
is read from storms.json when the IDs match; otherwise canonical defaults
from config.port are used so that hydrograph synthesis in port_stress.py
always has valid inputs.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from config.port import (
    STORM_ID_PREFIX,
    STRESS_STORM_DEFAULT_DURATION_HOURS,
    STRESS_STORM_DEFAULT_PEAK_POSITION,
)

logger = logging.getLogger(__name__)

# Maps trigger count bands to intensity label
_SEVERITY_LABEL = [
    # (min_severe, label)
    (10, "catastrophic"),
    (6,  "extreme"),
    (3,  "severe"),
    (1,  "moderate"),
    (0,  "baseline"),      # alert-only storms
]


def _derive_intensity_category(gauges_severe: int, gauges_warning: int) -> str:
    """Map trigger counts to a named intensity category."""
    for min_sev, label in _SEVERITY_LABEL:
        if gauges_severe >= min_sev:
            return label
    if gauges_warning >= 3:
        return "moderate"
    return "baseline"


def _make_name(index: int) -> str:
    """Generate a display name for a stress storm (Greek letter + number)."""
    greek = [
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta",
        "Theta", "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi",
        "Omicron", "Pi", "Rho", "Sigma", "Tau", "Upsilon", "Phi",
        "Chi", "Psi", "Omega",
    ]
    letter = greek[index % len(greek)]
    cycle  = index // len(greek)
    return f"{letter}-{cycle + 1}" if cycle else letter


def generate_stress_storms(
    gaugets_dir: Path,
    output_dir: Path,
    storms_json_path: Optional[Path] = None,
    *,
    output_path: Optional[Path] = None,
) -> Dict:
    """
    Build stress_storms/ directory from the current gaugets/ directory.

    Each storm is written as an individual JSON file (``{storm_id}.json``) inside
    ``output_dir/``.  A lightweight ``_index.json`` is also written containing
    storm metadata without the bulky ``gauge_responses`` array — this is used by
    the UI to populate dropdowns without loading ~90 MB of per-gauge data.

    Backward compatibility: if the deprecated *output_path* keyword is supplied
    (e.g. from old call-sites that passed a file path), the directory is derived
    from ``output_path.parent / 'stress_storms'``.

    Args:
        gaugets_dir:       Path to gaugets/ (data/input/<catchment>/gaugets/).
        output_dir:        Destination directory for per-storm JSON files.
        storms_json_path:  Optional path to storms.json for metadata enrichment.
        output_path:       **Deprecated** — ignored when *output_dir* is given.

    Returns:
        Summary dict: total_storms, alert_storms written, elapsed_s.
    """
    import time
    t0 = time.time()

    gaugets_dir  = Path(gaugets_dir)
    output_dir   = Path(output_dir)

    # ------------------------------------------------------------------
    # 1. Optional storms.json lookup for metadata enrichment
    # ------------------------------------------------------------------
    storm_meta: Dict[str, Dict] = {}
    if storms_json_path and Path(storms_json_path).exists():
        try:
            raw = json.loads(Path(storms_json_path).read_text())
            # Support both storm_sequences.json (sequences[].storms[])
            # and flat storms.json (storms[]) formats
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

    # ------------------------------------------------------------------
    # 2. Scan gaugets — build storm_id → {gauge_id: response} map
    # ------------------------------------------------------------------
    gauge_files = sorted(gaugets_dir.glob("GAUGE-*.json"))
    if not gauge_files:
        raise FileNotFoundError(f"No GAUGE-*.json files found in {gaugets_dir}")

    # storm_id -> list of per-gauge response dicts
    all_responses: Dict[str, List[Dict]] = {}
    # storm_id -> True if any gauge exceeded alert
    alert_storm_ids: set = set()

    for gf in gauge_files:
        try:
            data = json.loads(gf.read_text())
        except Exception as exc:
            logger.warning("Skipping %s: %s", gf.name, exc)
            continue

        # gauge_id is the file's top-level field; individual responses don't repeat it
        gauge_id = data.get("gauge_id", gf.stem)
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

    logger.info(
        "Scanned %d gauge files: %d total storm IDs, %d breached alert",
        len(gauge_files), len(all_responses), len(alert_storm_ids),
    )

    # ------------------------------------------------------------------
    # 3. Build per-storm records
    # ------------------------------------------------------------------
    storms = []
    name_idx = 0

    for storm_id in alert_storm_ids:
        gauge_responses = all_responses.get(storm_id, [])

        # Trigger summary
        g_alert   = sum(1 for r in gauge_responses if r.get("exceeded_alert"))
        g_warning = sum(1 for r in gauge_responses if r.get("exceeded_warning"))
        g_severe  = sum(1 for r in gauge_responses if r.get("exceeded_severe"))

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
            _derive_intensity_category(g_severe, g_warning),
        )
        name = meta.get("name") or _make_name(name_idx)
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

    # ------------------------------------------------------------------
    # 4. Sort: most severe first, then most warnings, then highest peak
    # ------------------------------------------------------------------
    def _sort_key(s: Dict):
        ts = s["trigger_summary"]
        max_peak = max(
            (r.get("peak_level_m", 0.0) for r in s["gauge_responses"]),
            default=0.0,
        )
        return (-ts["gauges_severe"], -ts["gauges_warning"], -max_peak)

    storms.sort(key=_sort_key)

    # ------------------------------------------------------------------
    # 5. Write per-storm files + lightweight index
    # ------------------------------------------------------------------
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

    elapsed = time.time() - t0
    logger.info(
        "Wrote %d stress storms to %s (%.1fs)",
        len(storms), output_dir, elapsed,
    )
    return {
        "total_storms": len(storms),
        "elapsed_s": round(elapsed, 2),
    }
