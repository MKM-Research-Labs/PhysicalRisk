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
Sequence generator for the Storm Sequence Generator (MKM-SS-001 v3.0).

Assembles individual storms into StormSequence objects within the event window.

v3.0 reserves room for the gaps before it caps the storms. Each of the n - 1 gaps is
guaranteed at least its gap type's minimum (6 h short, 24 h medium), so the per-storm
duration cap is (W_P - (n - 1) * g_min) / n. Raw gaps that would overflow what the
storms leave are shortened toward that minimum, never below it. Every sequence fits
without retries, and every multi-storm sequence keeps a gap between its storms. (v2.0
capped at W_P / n, which left no room for gaps in 46% of multi-storm sequences.)
"""

from datetime import datetime

import numpy as np

import config.port as cp

from ..core.data_structures import (
    SequenceStorm,
    SequenceType,
    StormSequence,
    make_sequence_id,
    make_storm_id,
)
from ..utils.validation import precip_end_hour
from .duration_sampler import sample_duration
from .gap_sampler import get_min_gap, sample_gap
from .intensity_sampler import (
    get_storm_count,
    sample_sequence_type,
    sample_storm_intensity,
    should_generate_sequence,
)


def _load_base_precipitation(catchment_id: str) -> float:
    """Read BASE_PRECIPITATION_MM from the active catchment's storm module.

    Falls back to 35.0 mm (thames baseline) if the catchment package has
    no ``storm.py`` yet — happens for the legacy single-module catchments
    under ``data/catch/<name>.py`` that haven't been migrated to the
    package layout.
    """
    import importlib
    try:
        mod = importlib.import_module(f"catch.{catchment_id}.storm")
    except ModuleNotFoundError:
        return 35.0
    return getattr(mod, "BASE_PRECIPITATION_MM", 35.0)


class SequenceGenerator:
    """Generates StormSequence objects from seed intensity parameters.

    Each sequence fits within the event window, with every gap at least its minimum:
    - Storm durations are capped to (W_P - (n - 1) * g_min) / n.
    - Inter-storm gaps are sampled, then shortened toward g_min if they would
      overflow what the storms leave.
    """

    def __init__(
        self,
        catchment_id: str = "thames",
        seed: int = None,
    ):
        self.catchment_id = catchment_id
        self.base_precipitation = _load_base_precipitation(catchment_id)
        self.rng = np.random.RandomState(seed)

    def generate(
        self,
        intensity_category: str,
        base_intensity: float,
        force_sequence_type: str = None,
        event_id: str = "",
        event_seed: int = 0,
    ) -> StormSequence:
        """Generate a StormSequence from a seed storm.

        Args:
            intensity_category: Storm intensity level (moderate, severe, etc.)
            base_intensity: Base intensity factor from distribution sampling.
                This is the severity latent ``z`` persisted on the sequence
                for storm<->typhoon coupling (see coupling_spec.md).
            force_sequence_type: Force a specific type, or None to sample.
            event_id: Shared 1:1 storm<->typhoon key (e.g. "EVT-00001").
                Empty when the caller does not couple events.
            event_seed: Per-event seed persisted for reproducible coupling.

        Returns:
            A valid StormSequence with 1-5 storms fitting within 168h window.
        """
        seq_id = make_sequence_id()
        now = datetime.now().isoformat()

        # Determine sequence type
        if force_sequence_type is not None:
            seq_type = SequenceType(force_sequence_type)
        elif should_generate_sequence(intensity_category, self.rng):
            seq_type = sample_sequence_type(intensity_category, self.rng)
        else:
            seq_type = SequenceType.ISOLATED

        num_storms = get_storm_count(seq_type, self.rng)
        return self._build_sequence(
            seq_id, seq_type, num_storms, intensity_category, base_intensity, now,
            event_id=event_id, event_seed=event_seed,
        )

    def _build_sequence(
        self,
        seq_id: str,
        seq_type: SequenceType,
        num_storms: int,
        intensity_category: str,
        base_intensity: float,
        generated_at: str,
        event_id: str = "",
        event_seed: int = 0,
    ) -> StormSequence:
        """Build a sequence that fits the window with every gap at least g_min.

        Eq. 6: d_i = min(D_i, (W_P - (n - 1) g_min) / n).
        Eqs. 7-8: with R = W_P - sum(d), if sum(G) > R each gap becomes
        g_min + (G_j - g_min) * (R - (n - 1) g_min) / sum(G_k - g_min).
        """
        w_p = precip_end_hour()
        num_gaps = num_storms - 1
        g_min = get_min_gap(seq_type)
        max_dur_per_storm = (w_p - num_gaps * g_min) / num_storms
        if max_dur_per_storm <= 0:
            raise ValueError(
                f"{num_storms} storms with {g_min}h minimum gaps cannot fit in {w_p}h"
            )

        # Sample storm durations (capped) and intensities
        storm_durations = []
        storm_intensities = []
        for i in range(num_storms):
            duration = min(sample_duration(intensity_category, self.rng), max_dur_per_storm)
            intensity = sample_storm_intensity(base_intensity, i, self.rng)
            storm_durations.append(duration)
            storm_intensities.append(intensity)

        # The storms leave R >= num_gaps * g_min; gaps over it shrink toward g_min
        remaining = w_p - sum(storm_durations)
        gaps = [sample_gap(seq_type, self.rng) for _ in range(num_gaps)]
        excess = sum(g - g_min for g in gaps)
        if sum(gaps) > remaining and excess > 0:   # excess 0: every gap already at g_min
            spare = remaining - num_gaps * g_min
            gaps = [g_min + (g - g_min) * spare / excess for g in gaps]

        # Assemble SequenceStorm objects with correct start times
        storms = []
        current_time = 0.0
        for i in range(num_storms):
            precip = self.base_precipitation * storm_intensities[i]
            storms.append(SequenceStorm(
                storm_id=make_storm_id(),
                scenario_id=seq_id,
                storm_index=i,
                start_time_hours=current_time,
                duration_hours=storm_durations[i],
                intensity_category=intensity_category,
                intensity_factor=storm_intensities[i],
                precipitation_mm=precip,
                peak_position=self.rng.beta(2.0, 2.0),
                generated_at=generated_at,
                catchment_id=self.catchment_id,
            ))
            current_time += storm_durations[i]
            if i < len(gaps):
                current_time += gaps[i]

        return self._assemble_sequence(
            seq_id, seq_type, storms, gaps, generated_at, intensity_category,
            base_intensity=base_intensity, event_id=event_id, event_seed=event_seed,
        )

    def _assemble_sequence(
        self,
        seq_id: str,
        seq_type: SequenceType,
        storms: list,
        gaps: list,
        generated_at: str,
        intensity_category: str = "",
        base_intensity: float = 0.0,
        event_id: str = "",
        event_seed: int = 0,
    ) -> StormSequence:
        """Assemble a StormSequence from storms and gaps."""
        intensities = [s.intensity_factor for s in storms]
        precipitations = [s.precipitation_mm for s in storms]
        total_duration = (
            sum(s.duration_hours for s in storms) + sum(gaps)
        )

        return StormSequence(
            sequence_id=seq_id,
            sequence_type=seq_type.value,
            intensity_category=intensity_category,
            sequence_start=generated_at,
            total_duration_hours=total_duration,
            event_window_hours=cp.EVENT_WINDOW_HOURS,
            drainage_window_hours=cp.EVENT_WINDOW_HOURS - total_duration,
            storms=storms,
            num_storms=len(storms),
            inter_storm_gaps_hours=gaps,
            total_precipitation_mm=sum(precipitations),
            max_intensity_factor=max(intensities),
            avg_intensity_factor=sum(intensities) / len(intensities),
            cumulative_intensity_factor=sum(intensities),
            event_id=event_id,
            base_intensity=base_intensity,
            seed=event_seed,
            antecedent_soil_moisture="normal",
            antecedent_groundwater="normal",
            generated_at=generated_at,
            catchment_id=self.catchment_id,
        )
