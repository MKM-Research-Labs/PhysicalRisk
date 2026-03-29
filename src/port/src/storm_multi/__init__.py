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

"""Storm Generator v2.0 — multi-storm sequence package."""

from .core.data_structures import (  # noqa: F401
    SEQUENCE_GAP_TYPE,
    SEQUENCE_TYPE_STORM_COUNTS,
    GapType,
    SequenceStorm,
    SequenceType,
    StormSequence,
    make_sequence_id,
    make_storm_id,
)
from .generators.batch_generator import (  # noqa: F401
    DEFAULT_INTENSITY_WEIGHTS,
    generate_event_set,
)
from .generators.sequence_generator import SequenceGenerator  # noqa: F401
from .models.hydrology import (  # noqa: F401
    HydrologicalState,
    HydrologyModel,
    HydrologyParams,
)
from .models.sequence_response import (  # noqa: F401
    SequenceGaugeParams,
    compute_sequence_gauge_response,
    compute_storm_peaks,
)
from .models.spatial_correlation import (  # noqa: F401
    SpatialCorrelationModel,
    SpatialCorrelationParams,
    save_spatial_correlation_config,
)
from .utils.serialization import (  # noqa: F401
    SCHEMA_VERSION,
    SEQUENCES_FILENAME,
    SUMMARY_FILENAME,
    load_sequences,
    save_sequences,
    save_summary,
)
from .utils.validation import (  # noqa: F401
    EVENT_WINDOW_HOURS,
    MAX_PRECIP_END_HOUR,
    MIN_DRAINAGE_WINDOW_HOURS,
    fits_in_window,
    validate_event_set,
    validate_sequence,
)
