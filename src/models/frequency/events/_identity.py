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

"""Event identity for the Event Frequency Model (MKM-EF-001).

Which hours-clause event a storm belongs to. This lives in the frequency
package rather than beside the loader that writes the tag, because the event
is a frequency-model concept and because the hazard chain must be free to
import the frequency layer — the dependency runs hazard → frequency → config,
one way and downhill.
"""

from typing import Any, Dict, Sequence

from config.frequency import SEQUENCE_ID_KEY


def event_id(storm: Dict[str, Any]) -> str:
    """Return the hours-clause event a storm belongs to.

    Args:
        storm: a storm dict from ``load_storms_from_sequences``.

    Returns:
        The parent sequence identifier, falling back to the storm's own
        identifier when the storm carries no tag. An untagged catalogue
        therefore degrades to one event per storm — the platform's behaviour
        before events existed — rather than collapsing into a single event.
    """
    return storm.get(SEQUENCE_ID_KEY) or storm["storm_id"]


def count_events(storms: Sequence[Dict[str, Any]]) -> int:
    """Count the distinct hours-clause events a storm list represents.

    Args:
        storms: storm dicts from ``load_storms_from_sequences``.

    Returns:
        The number of distinct events.
    """
    return len({event_id(storm) for storm in storms})
