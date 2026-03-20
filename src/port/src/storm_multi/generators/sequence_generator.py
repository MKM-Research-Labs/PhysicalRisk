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
Sequence generator for Storm Generator v2.0.

Assembles individual storms into StormSequence objects, respecting
the 168-hour event window and drainage constraints.

Storm durations are capped to a per-storm budget (window / num_storms)
so they always fit.  Gaps are sampled from their natural distribution
and scaled down proportionally if the total would overflow the remaining
budget.  This guarantees every sequence fits without retries or fallbacks.
"""

from datetime import datetime

import numpy as np

from ..core.data_structures import (
    SequenceStorm,
    SequenceType,
    StormSequence,
    make_sequence_id,
    make_storm_id,
)
from .duration_sampler import sample_duration
from .gap_sampler import sample_gap
from .intensity_sampler import (
    get_storm_count,
    sample_sequence_type,
    sample_storm_intensity,
    should_generate_sequence,
)
from config.port import CATCHMENT_BASE_PRECIP
from ..utils.validation import MAX_PRECIP_END_HOUR

# CATCHMENT_BASE_PRECIP imported from config/port.py


class SequenceGenerator:
    """Generates StormSequence objects from seed intensity parameters.

    Each sequence is guaranteed to fit within the 168-hour event window:
    - Storm durations are capped to (window / num_storms).
    - Inter-storm gaps are sampled naturally then scaled to fit the
      remaining budget after storms are placed.
    """

    def __init__(
        self,
        catchment_id: str = "thames",
        seed: int = None,
    ):
        self.catchment_id = catchment_id
        self.base_precipitation = CATCHMENT_BASE_PRECIP.get(catchment_id, 35.0)
        self.rng = np.random.RandomState(seed)

    def generate(
        self,
        intensity_category: str,
        base_intensity: float,
        force_sequence_type: str = None,
    ) -> StormSequence:
        """Generate a StormSequence from a seed storm.

        Args:
            intensity_category: Storm intensity level (moderate, severe, etc.)
            base_intensity: Base intensity factor from distribution sampling.
            force_sequence_type: Force a specific type, or None to sample.

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
        )

    def _build_sequence(
        self,
        seq_id: str,
        seq_type: SequenceType,
        num_storms: int,
        intensity_category: str,
        base_intensity: float,
        generated_at: str,
    ) -> StormSequence:
        """Build a sequence that always fits within the event window.

        Storm durations are capped to (MAX_PRECIP_END_HOUR / num_storms) so
        all storms fit regardless of intensity category.  Gaps are sampled from
        their natural distribution and scaled proportionally if necessary.
        """
        max_dur_per_storm = MAX_PRECIP_END_HOUR / num_storms

        # Sample storm durations (capped) and intensities
        storm_durations = []
        storm_intensities = []
        for i in range(num_storms):
            duration = min(sample_duration(intensity_category, self.rng), max_dur_per_storm)
            intensity = sample_storm_intensity(base_intensity, i, self.rng)
            storm_durations.append(duration)
            storm_intensities.append(intensity)

        # Distribute remaining budget as inter-storm gaps
        total_storm_time = sum(storm_durations)
        remaining = MAX_PRECIP_END_HOUR - total_storm_time
        num_gaps = num_storms - 1

        if num_gaps > 0 and remaining > 0:
            raw_gaps = [sample_gap(seq_type, self.rng) for _ in range(num_gaps)]
            total_raw = sum(raw_gaps)
            if total_raw > remaining:
                # Scale gaps proportionally to fit the remaining budget
                scale = remaining / total_raw
                gaps = [g * scale for g in raw_gaps]
            else:
                gaps = raw_gaps
        else:
            gaps = [0.0] * num_gaps if num_gaps > 0 else []

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
        )

    def _assemble_sequence(
        self,
        seq_id: str,
        seq_type: SequenceType,
        storms: list,
        gaps: list,
        generated_at: str,
        intensity_category: str = "",
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
            event_window_hours=168,
            drainage_window_hours=168 - total_duration,
            storms=storms,
            num_storms=len(storms),
            inter_storm_gaps_hours=gaps,
            total_precipitation_mm=sum(precipitations),
            max_intensity_factor=max(intensities),
            avg_intensity_factor=sum(intensities) / len(intensities),
            cumulative_intensity_factor=sum(intensities),
            antecedent_soil_moisture="normal",
            antecedent_groundwater="normal",
            generated_at=generated_at,
            catchment_id=self.catchment_id,
        )
