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

"""Configuration for the Event Frequency Model (MKM-EF-001).

Owns every parameter the frequency layer uses: peaks-over-threshold extraction
knobs, declustering separation, arrival-rate fallbacks and the return-period
grid. Values are engineering-judgement seeds documented in ``_schema.py``.

Per rule R4 this module contains no function definitions — only re-exports.
"""

from config.frequency._loader import (
    CONFIG_HASH_CHARS,
    catchment_lambda,
    config_hash,
    load_frequency_config,
)
from config.frequency._schema import (
    ANNUAL_BLOCK_DAYS,
    EVENT_POPULATION_WEIGHTS,
    INTENSITY_SEVERITY_ORDER,
    CATCHMENT_LAMBDA_PER_YEAR,
    DEFAULT_LAMBDA_PER_YEAR,
    DAYS_PER_YEAR,
    MODEL_ID,
    MODEL_VERSION,
    PERIL_FLOOD,
    SEQUENCE_ID_KEY,
    SOURCE_DATASET_GAUGE_DAILY,
    FrequencyConfig,
    PotConfig,
    RateConfig,
    SimulationConfig,
)

__all__ = [
    "FrequencyConfig",
    "PotConfig",
    "RateConfig",
    "SimulationConfig",
    "MODEL_ID",
    "MODEL_VERSION",
    "SOURCE_DATASET_GAUGE_DAILY",
    "PERIL_FLOOD",
    "SEQUENCE_ID_KEY",
    "DAYS_PER_YEAR",
    "ANNUAL_BLOCK_DAYS",
    "EVENT_POPULATION_WEIGHTS",
    "INTENSITY_SEVERITY_ORDER",
    "CATCHMENT_LAMBDA_PER_YEAR",
    "DEFAULT_LAMBDA_PER_YEAR",
    "catchment_lambda",
    "load_frequency_config",
    "config_hash",
    "CONFIG_HASH_CHARS",
]
