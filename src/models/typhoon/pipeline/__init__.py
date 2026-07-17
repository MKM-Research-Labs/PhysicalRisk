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
End-to-end typhoon ensemble pipeline.

Submodules:
    results.py      output dataclasses (PropertyPeakWindSummary,
                    TyphoonEventEnsemble)
    aggregation.py  per-property statistics over WindFieldOutput realizations
    event.py        single-event simulation (particle filter + wind-field
                    evaluation at every property point)
    ensemble.py     top-level loop simulate_typhoon_events + JSON export

The pipeline is catchment-agnostic. A boundary adapter in
app/commands/port/stages/typhoon_stage.py assembles the
CatchmentTyphoonConfig from the active catchment's tc.py and calls
simulate_typhoon_events.
"""

from models.typhoon.pipeline.aggregation import aggregate_property_winds
from models.typhoon.pipeline.ensemble import (
    simulate_typhoon_events,
    write_ensemble_json,
    write_event_trajectory,
    write_event_windts,
)
from models.typhoon.pipeline.event import (
    EventResult,
    pick_representative_index,
    pick_representative_trajectory,
    simulate_one_event,
)
from models.typhoon.pipeline.results import (
    PropertyPeakWindSummary,
    TyphoonEventEnsemble,
)


__all__ = [
    "PropertyPeakWindSummary",
    "TyphoonEventEnsemble",
    "EventResult",
    "aggregate_property_winds",
    "pick_representative_index",
    "pick_representative_trajectory",
    "simulate_one_event",
    "simulate_typhoon_events",
    "write_ensemble_json",
    "write_event_trajectory",
    "write_event_windts",
]
