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

from .duration_sampler import (  # noqa: F401
    DURATION_PARAMS,
    get_duration_range,
    get_max_duration,
    sample_duration,
)
from .gap_sampler import (  # noqa: F401
    GAP_PARAMS,
    get_gap_range,
    sample_gap,
)
from .intensity_sampler import (  # noqa: F401
    SEQUENCE_PROBABILITY,
    SEQUENCE_TYPE_WEIGHTS,
    get_storm_count,
    sample_sequence_type,
    sample_storm_intensity,
    should_generate_sequence,
)
from .sequence_generator import SequenceGenerator  # noqa: F401
from .batch_generator import (  # noqa: F401
    DEFAULT_INTENSITY_WEIGHTS,
    generate_event_set,
)
