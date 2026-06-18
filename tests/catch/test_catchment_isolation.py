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

"""Cross-catchment isolation tests.

Locks down the wiring that lets the platform switch between thames and
halong (and any future catchment) cleanly: each catchment exposes the
same symbol surface, the global ``config.catchment_id`` setter refreshes
data paths, and downstream generators (SequenceGenerator etc.) read
calibration from the correct catchment's storm.py — not from a global
default and not from each other.

Catches "we accidentally hardcoded thames again" regressions.
"""

import pytest

from config import config


# All catchments expected to expose the full storm+config symbol surface.
# Add to this list when a new catchment is given a storm.py.
CATCHMENTS_WITH_STORM = ["thames", "halong"]


@pytest.fixture(autouse=True)
def restore_catchment():
    """Snapshot catchment_id before each test and restore after.

    Tests in this module mutate `config.catchment_id`; without this
    fixture, ordering would leak state into siblings.
    """
    original = config.catchment_id
    yield
    config.catchment_id = original


# ---------------------------------------------------------------------------
# 1) Symbol surface — every catchment with a storm.py exposes the same
#    four storm constants.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("catchment_id", CATCHMENTS_WITH_STORM)
def test_storm_module_exposes_required_constants(catchment_id):
    import importlib
    storm = importlib.import_module(f"catch.{catchment_id}.storm")
    for name in ("BASE_PRECIPITATION_MM", "TRACK_START", "TRACK_END", "INTENSITY_WEIGHTS"):
        assert hasattr(storm, name), f"catch.{catchment_id}.storm missing {name}"


@pytest.mark.parametrize("catchment_id", CATCHMENTS_WITH_STORM)
def test_storm_constants_are_well_typed(catchment_id):
    import importlib
    storm = importlib.import_module(f"catch.{catchment_id}.storm")
    assert isinstance(storm.BASE_PRECIPITATION_MM, (int, float))
    assert storm.BASE_PRECIPITATION_MM > 0

    assert isinstance(storm.TRACK_START, tuple) and len(storm.TRACK_START) == 2
    assert isinstance(storm.TRACK_END, tuple) and len(storm.TRACK_END) == 2

    assert isinstance(storm.INTENSITY_WEIGHTS, dict)
    assert set(storm.INTENSITY_WEIGHTS.keys()) == {
        "moderate", "severe", "extreme", "catastrophic"
    }
    assert sum(storm.INTENSITY_WEIGHTS.values()) == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# 2) SequenceGenerator pulls BASE_PRECIPITATION_MM from the right
#    catchment's storm.py, not from a global default or a hardcoded value.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("catchment_id", CATCHMENTS_WITH_STORM)
def test_sequence_generator_reads_catchment_base_precip(catchment_id):
    import importlib
    from port.src.storm_multi.generators.sequence_generator import SequenceGenerator

    expected = importlib.import_module(f"catch.{catchment_id}.storm").BASE_PRECIPITATION_MM
    gen = SequenceGenerator(catchment_id=catchment_id)
    assert gen.base_precipitation == expected


def test_unknown_catchment_falls_back_to_thames_baseline():
    """No catch.<id>.storm module → 35 mm fallback (thames baseline)."""
    from port.src.storm_multi.generators.sequence_generator import SequenceGenerator
    gen = SequenceGenerator(catchment_id="nonexistent_river")
    assert gen.base_precipitation == 35.0


# ---------------------------------------------------------------------------
# 3) Switching catchments at runtime refreshes data paths (regression
#    test for the path-snapshot bug we fixed earlier).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("catchment_id", CATCHMENTS_WITH_STORM)
def test_catchment_switch_refreshes_input_dir(catchment_id):
    config.catchment_id = catchment_id
    assert config.input_dir.name == catchment_id
    assert config.CATCHMENT == catchment_id

    # Derived dirs follow input_dir
    assert catchment_id in str(config.get_gaugets_dir())
    assert catchment_id in str(config.get_classifiers_dir())
    assert catchment_id in str(config.get_trading_dir())


def test_catchment_switch_does_not_leak_paths():
    """Switching thames→halong→thames should land us back exactly where
    we started — no halong directories left in the input_dir path."""
    config.catchment_id = "thames"
    thames_input = config.input_dir
    config.catchment_id = "halong"
    assert config.input_dir != thames_input
    config.catchment_id = "thames"
    assert config.input_dir == thames_input


# ---------------------------------------------------------------------------
# 4) Catchments produce distinct output for the same seed + recipe
#    (proves the calibration isn't being shared across catchments).
# ---------------------------------------------------------------------------

def test_thames_and_halong_storms_diverge_with_same_seed():
    from port.src.storm_multi.generators.sequence_generator import SequenceGenerator

    t = SequenceGenerator(catchment_id="thames", seed=42).generate(
        intensity_category="severe", base_intensity=1.5)
    h = SequenceGenerator(catchment_id="halong", seed=42).generate(
        intensity_category="severe", base_intensity=1.5)

    # Same seed → same sequence shape (this is the seeded-RNG contract;
    # if it breaks we'd want to know).
    assert t.num_storms == h.num_storms
    assert t.sequence_type == h.sequence_type

    # … but precipitation must be scaled by the catchment's base value.
    # Halong base (100mm) is ~2.86x thames (35mm); first-storm precip
    # should track that ratio.
    ratio = h.storms[0].precipitation_mm / t.storms[0].precipitation_mm
    assert 2.5 < ratio < 3.2, (
        f"Expected halong storm to be ~2.86x thames precipitation; "
        f"got {ratio:.2f}x  ({h.storms[0].precipitation_mm} / "
        f"{t.storms[0].precipitation_mm})"
    )


# ---------------------------------------------------------------------------
# 5) Geography is non-overlapping — thames gauges in the UK, halong
#    gauges in Vietnam. If a test ever sees overlap, something stuck.
# ---------------------------------------------------------------------------

def test_thames_and_halong_gauges_are_geographically_distinct():
    from catch.thames import GAUGE_POINTS as T_GP
    from catch.halong import GAUGE_POINTS as H_GP

    t_lats = [p[0] for p in T_GP]
    h_lats = [p[0] for p in H_GP]
    t_lons = [p[1] for p in T_GP]
    h_lons = [p[1] for p in H_GP]

    # Thames around 51°N, halong around 21°N — comfortably separated.
    assert min(t_lats) > 30, "Thames gauges should be in northern hemisphere mid-latitudes"
    assert max(h_lats) < 30, "Halong gauges should be in tropics"

    # Thames around 0°E (Greenwich), halong around 105°E.
    assert max(t_lons) < 50
    assert min(h_lons) > 50


# ---------------------------------------------------------------------------
# 6) AREAS / STREETS / AREA_VALUE_FACTORS internal consistency per catchment.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("catchment_id", CATCHMENTS_WITH_STORM)
def test_areas_have_value_factors(catchment_id):
    """Every AREAS entry must have an AREA_VALUE_FACTORS entry, otherwise
    property valuation silently falls back to 1.0 — a hidden bug.

    (We deliberately don't enforce STREETS coverage here: thames currently
    has gaps in its STREETS dict for some downstream-estuary areas, and
    the generator already handles missing-streets gracefully. This is a
    catchment-isolation test, not a data-completeness audit.)
    """
    import importlib
    cat = importlib.import_module(f"catch.{catchment_id}")
    missing_factors = [a for a in cat.AREAS if a not in cat.AREA_VALUE_FACTORS]
    assert not missing_factors, f"{catchment_id}: areas without AREA_VALUE_FACTORS: {missing_factors}"


@pytest.mark.parametrize("catchment_id", CATCHMENTS_WITH_STORM)
def test_gauge_points_and_names_aligned(catchment_id):
    import importlib
    cat = importlib.import_module(f"catch.{catchment_id}")
    assert len(cat.GAUGE_POINTS) == len(cat.GAUGE_NAMES), (
        f"{catchment_id}: {len(cat.GAUGE_POINTS)} gauge points but "
        f"{len(cat.GAUGE_NAMES)} names"
    )
