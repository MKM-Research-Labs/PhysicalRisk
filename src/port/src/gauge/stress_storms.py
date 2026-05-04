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
Stress Storms Catalogue Generator — orchestrator.

Builds data/input/<catchment>/stress_storms/ from the current gaugets/
directory.  Runs four stages from ``_stress_storms_stages.py``:

  1. ``load_storm_metadata``   — optional storms.json lookup
  2. ``scan_gauge_responses``  — fan-in gauge files → per-storm responses
  3. ``build_storm_records``   — assemble records with metadata
  4. ``write_storm_files``     — per-storm JSON + lightweight index

Storm metadata (duration_hours, peak_position, effective_precipitation_mm)
is read from storms.json when the IDs match; otherwise canonical defaults
from config.port are used so hydrograph synthesis in port_stress.py
always has valid inputs.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from . import _stress_storms_stages as _stages

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
    cycle = index // len(greek)
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

    gaugets_dir = Path(gaugets_dir)
    output_dir = Path(output_dir)

    # Stage 1: optional metadata enrichment
    storm_meta = _stages.load_storm_metadata(storms_json_path)

    # Stage 2: scan gaugets — build storm_id → {gauge_id: response} map
    all_responses, alert_storm_ids = _stages.scan_gauge_responses(gaugets_dir)

    # Stage 3: build per-storm records (with intensity + display name)
    storms = _stages.build_storm_records(
        alert_storm_ids,
        all_responses,
        storm_meta,
        derive_intensity_category=_derive_intensity_category,
        make_name=_make_name,
    )

    # Stage 4: write per-storm files + lightweight index
    _stages.write_storm_files(storms, output_dir)

    elapsed = time.time() - t0
    logger.info(
        "Wrote %d stress storms to %s (%.1fs)",
        len(storms), output_dir, elapsed,
    )
    return {
        "total_storms": len(storms),
        "elapsed_s": round(elapsed, 2),
    }
