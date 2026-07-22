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

"""Loader and hasher for the Event Frequency Model configuration.

The frequency config carries no external seed file — its values are the
dataclass defaults in ``_schema.py``. This module exists to give callers a
single construction point and, more importantly, a stable content hash that
goes into every calibration's provenance record so a fitted rate can be traced
back to the exact knobs that produced it (BCBS 239).
"""

from dataclasses import asdict
from hashlib import sha256
from json import dumps
from typing import Optional

from config.frequency._schema import FrequencyConfig, PotConfig, RateConfig

# Characters of the SHA-256 digest retained as the config hash. Sixteen hex
# characters is 64 bits — ample to distinguish the handful of configurations a
# calibration campaign will ever use, and short enough to read in a report.
CONFIG_HASH_CHARS: int = 16


def load_frequency_config(
    pot: Optional[PotConfig] = None,
    rate: Optional[RateConfig] = None,
) -> FrequencyConfig:
    """Build a frequency configuration, optionally overriding either block.

    Args:
        pot: replacement peaks-over-threshold block; defaults to ``PotConfig()``.
        rate: replacement rate block; defaults to ``RateConfig()``.

    Returns:
        A ``FrequencyConfig``.
    """
    return FrequencyConfig(
        pot=pot if pot is not None else PotConfig(),
        rate=rate if rate is not None else RateConfig(),
    )


def config_hash(config: FrequencyConfig) -> str:
    """Return a stable content hash of *config* for provenance records.

    The hash is a pure function of the configuration values: two runs with
    equal configuration produce equal hashes, in this process or any other.

    Args:
        config: the configuration to hash.

    Returns:
        The leading ``CONFIG_HASH_CHARS`` hex characters of the SHA-256 digest
        of the configuration's canonical JSON form.
    """
    canonical = dumps(asdict(config), sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()[:CONFIG_HASH_CHARS]
