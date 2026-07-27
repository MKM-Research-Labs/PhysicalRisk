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

from dataclasses import asdict, replace
from hashlib import sha256
from json import dumps
from typing import Optional

from config.frequency._schema import (
    CATCHMENT_ANNUAL_GROWTH,
    CATCHMENT_LAMBDA_PER_YEAR,
    CATCHMENT_WIND_LAMBDA_PER_YEAR,
    DECOUPLED_WIND_CATCHMENTS,
    DEFAULT_ANNUAL_GROWTH,
    DEFAULT_LAMBDA_PER_YEAR,
    FrequencyConfig,
    PotConfig,
    RateConfig,
    SelectionConfig,
    SimulationConfig,
)

# Characters of the SHA-256 digest retained as the config hash. Sixteen hex
# characters is 64 bits — ample to distinguish the handful of configurations a
# calibration campaign will ever use, and short enough to read in a report.
CONFIG_HASH_CHARS: int = 16


def catchment_lambda(catchment: Optional[str]) -> float:
    """Return the seeded event arrival rate for *catchment*.

    Args:
        catchment: catchment identifier; matched case-insensitively. ``None``
            or an unseeded catchment returns the default rate.

    Returns:
        Qualifying storm events per year.
    """
    if not catchment:
        return DEFAULT_LAMBDA_PER_YEAR
    return CATCHMENT_LAMBDA_PER_YEAR.get(catchment.lower(), DEFAULT_LAMBDA_PER_YEAR)


def catchment_wind_lambda(catchment: Optional[str]) -> float:
    """Return the WIND event arrival rate for *catchment* (MKM-EF-001, 6f).

    The per-peril arrival rate the plan's §4.14 architected for. It falls back
    to the storm event rate (``catchment_lambda``) whenever the catchment has no
    wind-specific seed — which, with ``CATCHMENT_WIND_LAMBDA_PER_YEAR`` empty, is
    every catchment. That fallback is not a placeholder but the model: under the
    current 1:1 storm-typhoon coupling wind is not an independent arrival
    process, so it shares the storm rate (see the schema note on the registry).

    An explicit entry overrides only the additive wind-loss view; the priced
    wind spread stays on the coupled event rate until the unpaired-typhoon
    counting that a real decoupling needs is built and signed off.

    Args:
        catchment: catchment identifier; matched case-insensitively. ``None`` or
            an unseeded catchment returns the storm event rate.

    Returns:
        Wind events per year.
    """
    if catchment and catchment.lower() in CATCHMENT_WIND_LAMBDA_PER_YEAR:
        return CATCHMENT_WIND_LAMBDA_PER_YEAR[catchment.lower()]
    return catchment_lambda(catchment)


def catchment_annual_growth(catchment: Optional[str]) -> float:
    """Return the annual arrival-rate growth for *catchment* (MKM-EF-001, 6h).

    The fractional change in λ per contract year that makes the multi-year term
    structure non-stationary. Returns a plain number, not a rate process, so
    ``config`` stays a leaf: the ``RateProcess`` is built from this in the model
    layer (``rate_process_for``).

    With ``CATCHMENT_ANNUAL_GROWTH`` empty this is zero for every catchment — a
    stationary rate, leaving the term structure unchanged. A non-zero value is a
    model-risk decision, not a default.

    Args:
        catchment: catchment identifier; matched case-insensitively.

    Returns:
        The fractional annual growth; ``0.0`` when unseeded.
    """
    if catchment and catchment.lower() in CATCHMENT_ANNUAL_GROWTH:
        return CATCHMENT_ANNUAL_GROWTH[catchment.lower()]
    return DEFAULT_ANNUAL_GROWTH


def is_wind_decoupled(catchment: Optional[str]) -> bool:
    """Return whether *catchment* prices wind as an independent process (6i).

    False for every catchment while ``DECOUPLED_WIND_CATCHMENTS`` is empty — the
    coupled 1:1 model, i.e. the behaviour of every stage before 6i. Opting a
    catchment in is a model-risk decision (see the schema note).

    Args:
        catchment: catchment identifier; matched case-insensitively.

    Returns:
        True if wind is decoupled for the catchment.
    """
    return bool(catchment) and catchment.lower() in DECOUPLED_WIND_CATCHMENTS


def load_frequency_config(
    catchment: Optional[str] = None,
    pot: Optional[PotConfig] = None,
    rate: Optional[RateConfig] = None,
    selection: Optional[SelectionConfig] = None,
    simulation: Optional[SimulationConfig] = None,
) -> FrequencyConfig:
    """Build a frequency configuration, optionally overriding either block.

    When *catchment* is given and no explicit *pot* block is supplied, the
    threshold search target is set from that catchment's arrival rate. That
    keeps one source of truth: the qualifying-event threshold and lambda then
    describe the same event population by construction rather than by
    coincidence, which is the alignment the plan's §4.3 requires.

    Args:
        catchment: catchment whose arrival rate drives the threshold target.
        pot: replacement peaks-over-threshold block. Supplied explicitly it
            wins outright, including its rate target.
        rate: replacement rate block; defaults to ``RateConfig()``.
        simulation: replacement simulation block; defaults to
            ``SimulationConfig()``.

    Returns:
        A ``FrequencyConfig``.
    """
    if pot is not None:
        pot_block = pot
    elif catchment:
        pot_block = replace(
            PotConfig(),
            target_exceedance_rate_per_year=catchment_lambda(catchment))
    else:
        pot_block = PotConfig()

    return FrequencyConfig(
        pot=pot_block,
        rate=rate if rate is not None else RateConfig(),
        selection=selection if selection is not None else SelectionConfig(),
        simulation=simulation if simulation is not None else SimulationConfig(),
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
