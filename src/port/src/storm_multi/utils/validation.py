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
Validation for Storm Generator v2.0 sequences.

Enforces the 168-hour event window, drainage window constraint,
temporal ordering, and structural consistency rules from the spec.
"""

from typing import List

from config.port import EVENT_WINDOW_HOURS, MIN_DRAINAGE_WINDOW_HOURS
from ..core.data_structures import SequenceType, StormSequence
MAX_PRECIP_END_HOUR = EVENT_WINDOW_HOURS - MIN_DRAINAGE_WINDOW_HOURS  # 156

VALID_SEQUENCE_TYPES = {"isolated", "doublet", "cluster", "persistent"}
VALID_INTENSITY_CATEGORIES = {
    "minimal", "baseline", "moderate", "severe", "extreme", "catastrophic"
}


def validate_sequence(sequence: StormSequence) -> List[str]:
    """Validate a StormSequence against all constraints.

    Returns:
        List of error strings. Empty list means valid.
    """
    errors = []

    # Type check
    if sequence.sequence_type not in VALID_SEQUENCE_TYPES:
        errors.append(
            f"Invalid sequence_type: {sequence.sequence_type}"
        )

    # Storm count consistency
    if sequence.num_storms != len(sequence.storms):
        errors.append(
            f"num_storms ({sequence.num_storms}) != "
            f"len(storms) ({len(sequence.storms)})"
        )

    # Storm count range
    if not (1 <= len(sequence.storms) <= 5):
        errors.append(
            f"Storm count {len(sequence.storms)} not in [1, 5]"
        )

    # Gap count = num_storms - 1
    expected_gaps = max(0, len(sequence.storms) - 1)
    if len(sequence.inter_storm_gaps_hours) != expected_gaps:
        errors.append(
            f"Expected {expected_gaps} gaps, "
            f"got {len(sequence.inter_storm_gaps_hours)}"
        )

    # Temporal ordering: each storm starts after previous storm ends
    for i in range(1, len(sequence.storms)):
        prev = sequence.storms[i - 1]
        curr = sequence.storms[i]
        prev_end = prev.start_time_hours + prev.duration_hours
        if curr.start_time_hours < prev_end:
            errors.append(
                f"Storm {i} starts at {curr.start_time_hours}h "
                f"before storm {i-1} ends at {prev_end}h"
            )

    # Drainage window: last storm must end by MAX_PRECIP_END_HOUR
    # Allow 1e-9 tolerance for floating-point accumulation in duration caps.
    _FP_TOL = 1e-9
    if sequence.storms:
        last = sequence.storms[-1]
        last_end = last.start_time_hours + last.duration_hours
        if last_end > MAX_PRECIP_END_HOUR + _FP_TOL:
            errors.append(
                f"Last storm ends at hour {last_end}, "
                f"exceeds MAX_PRECIP_END_HOUR={MAX_PRECIP_END_HOUR}"
            )

        # Drainage window check
        drainage = EVENT_WINDOW_HOURS - last_end
        if drainage < MIN_DRAINAGE_WINDOW_HOURS - _FP_TOL:
            errors.append(
                f"Drainage window {drainage}h < "
                f"minimum {MIN_DRAINAGE_WINDOW_HOURS}h"
            )

    # Intensity categories valid
    for s in sequence.storms:
        if s.intensity_category not in VALID_INTENSITY_CATEGORIES:
            errors.append(
                f"Storm {s.storm_id}: invalid intensity "
                f"category '{s.intensity_category}'"
            )

    # total_duration consistency
    expected_duration = (
        sum(s.duration_hours for s in sequence.storms)
        + sum(sequence.inter_storm_gaps_hours)
    )
    if abs(sequence.total_duration_hours - expected_duration) > 0.5:
        errors.append(
            f"total_duration_hours ({sequence.total_duration_hours}) != "
            f"sum of durations+gaps ({expected_duration})"
        )

    return errors


def validate_event_set(sequences: List[StormSequence]) -> dict:
    """Validate an entire event set.

    Returns:
        Dict with 'total', 'valid', 'invalid', 'errors' keys.
    """
    results = {
        "total": len(sequences),
        "valid": 0,
        "invalid": 0,
        "errors": [],
    }

    for seq in sequences:
        errs = validate_sequence(seq)
        if errs:
            results["invalid"] += 1
            results["errors"].append({
                "sequence_id": seq.sequence_id,
                "errors": errs,
            })
        else:
            results["valid"] += 1

    return results


def fits_in_window(
    storm_durations: List[float],
    gap_durations: List[float],
) -> bool:
    """Check if storms + gaps fit within the precipitation window.

    All precipitation must end by hour MAX_PRECIP_END_HOUR (156).
    """
    total = sum(storm_durations) + sum(gap_durations)
    return total <= MAX_PRECIP_END_HOUR


