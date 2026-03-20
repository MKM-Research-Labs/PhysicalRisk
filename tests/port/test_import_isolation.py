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
Import-isolation tests for port.src.

Verifies that:
  1. Portfolio generator modules (gauge, property, mortgage, storm) can be
     imported without QuantLib being present in the environment.
  2. port.src.book is the only submodule that requires QuantLib.
  3. The port.src package __init__ does NOT eagerly import book.

These tests protect against regressions where an eager import at package level
would break `app.py port --gauges` (and all other non-book steps) in environments
where QuantLib has not been installed.

QuantLib is a hard requirement for trade pricing (step 11: book generation).
The isolation is achieved by lazy import — port.src.book is imported explicitly
only by app/commands/port.py and app/commands/book.py inside their respective
`if` blocks, not at module load time.
"""

import importlib
import sys

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simulate_no_quantlib(monkeypatch):
    """
    Block 'QuantLib' in sys.modules so any `import QuantLib` raises ImportError.

    Python treats sys.modules[name] = None as a "blocked" import — it raises
    ImportError immediately rather than searching for the package.  This is the
    correct way to simulate a missing package in tests.
    """
    # Remove real QuantLib and any sub-modules from the cache first
    for key in list(sys.modules.keys()):
        if key == "QuantLib" or key.startswith("QuantLib."):
            monkeypatch.delitem(sys.modules, key, raising=False)

    # None in sys.modules → ImportError on next `import QuantLib`
    monkeypatch.setitem(sys.modules, "QuantLib", None)


def _drop_port_src_cache(monkeypatch):
    """Remove all port.src.* entries from sys.modules so they reimport fresh."""
    for key in list(sys.modules.keys()):
        if key == "port.src" or key.startswith("port.src."):
            monkeypatch.delitem(sys.modules, key, raising=False)


# ---------------------------------------------------------------------------
# Tests: package __init__ does not import book
# ---------------------------------------------------------------------------

class TestPackageDoesNotEagerlyImportBook:

    def test_port_src_init_source_has_no_book_import(self):
        """The package __init__.py must not contain `from .book import`."""
        import inspect
        import port.src as _pkg
        src = inspect.getsource(_pkg)
        assert "from .book import" not in src, (
            "port/src/__init__.py eagerly imports .book — this forces QuantLib "
            "to be present even for non-book pipeline steps."
        )

    def test_port_src_init_source_has_no_generate_thames_central(self):
        """Package __init__.py must not expose generate_thames_central_book."""
        import port.src as _pkg
        assert not hasattr(_pkg, "generate_thames_central_book"), (
            "generate_thames_central_book is exported from port.src — "
            "this implies an eager .book import."
        )

    def test_port_src_all_does_not_include_book_symbols(self):
        import port.src as _pkg
        book_symbols = {
            "generate_thames_central_book",
            "generate_market_making_book",
            "generate_trade_pdfs",
            "print_book_summary",
            "THAMES_CENTRAL_AREAS",
        }
        exported = set(getattr(_pkg, "__all__", []))
        overlap = book_symbols & exported
        assert not overlap, (
            f"Book symbols in port.src.__all__: {overlap} — remove them so "
            "QuantLib is not required just to import the package."
        )


# ---------------------------------------------------------------------------
# Tests: generator modules importable without QuantLib
# ---------------------------------------------------------------------------

class TestGeneratorsImportableWithoutQuantLib:
    """
    Simulate a missing QuantLib installation and verify the non-book modules
    still import cleanly.  These are the modules used by pipeline steps 1-10
    and 12 (all steps except book generation).
    """

    def test_gauge_importable_without_quantlib(self, monkeypatch):
        _simulate_no_quantlib(monkeypatch)
        _drop_port_src_cache(monkeypatch)
        mod = importlib.import_module("port.src.gauge")
        assert hasattr(mod, "GaugePortfolioGenerator")

    def test_mortgage_importable_without_quantlib(self, monkeypatch):
        _simulate_no_quantlib(monkeypatch)
        _drop_port_src_cache(monkeypatch)
        mod = importlib.import_module("port.src.mortgage")
        assert hasattr(mod, "MortgagePortfolioGenerator")

    def test_storm_multi_importable_without_quantlib(self, monkeypatch):
        _simulate_no_quantlib(monkeypatch)
        _drop_port_src_cache(monkeypatch)
        mod = importlib.import_module("port.src.storm_multi")
        assert mod is not None

    def test_hazard_builder_importable_without_quantlib(self, monkeypatch):
        """models.hazard.builder must not drag in QuantLib pricing at import."""
        _simulate_no_quantlib(monkeypatch)
        for key in list(sys.modules.keys()):
            if key.startswith("models.hazard"):
                monkeypatch.delitem(sys.modules, key, raising=False)
        mod = importlib.import_module("models.hazard.builder")
        assert mod is not None

    def test_port_src_package_importable_without_quantlib(self, monkeypatch):
        """Importing port.src (package __init__) must not require QuantLib."""
        _simulate_no_quantlib(monkeypatch)
        _drop_port_src_cache(monkeypatch)
        mod = importlib.import_module("port.src")
        assert hasattr(mod, "GaugePortfolioGenerator")


# ---------------------------------------------------------------------------
# Tests: book module correctly requires QuantLib
# ---------------------------------------------------------------------------

_quantlib_available = pytest.mark.skipif(
    importlib.util.find_spec("QuantLib") is None,
    reason="QuantLib not installed in this environment",
)


class TestBookRequiresQuantLib:

    def test_pricing_module_requires_quantlib(self, monkeypatch):
        """
        models.hazard.pricing has `import QuantLib as ql` at module level.
        It must raise ImportError when QuantLib is absent.
        This is the root of the QuantLib dependency for trade pricing.
        """
        _simulate_no_quantlib(monkeypatch)
        for key in list(sys.modules.keys()):
            if key == "models.hazard.pricing":
                monkeypatch.delitem(sys.modules, key, raising=False)

        with pytest.raises((ImportError, AttributeError)):
            importlib.import_module("models.hazard.pricing")

    def test_book_module_importable_without_quantlib(self, monkeypatch):
        """
        port.src.book itself can be imported without QuantLib because
        QuantLib is only used inside functions (via models.hazard.pricing),
        not at module level.  QuantLib is required at *call time* when
        generate_thames_central_book() is executed.
        """
        _simulate_no_quantlib(monkeypatch)
        for key in list(sys.modules.keys()):
            if key.startswith("port.src.book") or key == "models.hazard.pricing":
                monkeypatch.delitem(sys.modules, key, raising=False)

        # Should NOT raise — QuantLib is a runtime dependency, not import-time
        mod = importlib.import_module("port.src.book")
        assert hasattr(mod, "THAMES_CENTRAL_AREAS")

    @_quantlib_available
    def test_book_exports_when_quantlib_present(self):
        """When QuantLib IS available, book must export its public API."""
        from port.src.book import (  # noqa: F401
            THAMES_CENTRAL_AREAS,
            generate_thames_central_book,
            generate_market_making_book,
            generate_trade_pdfs,
            print_book_summary,
        )
        assert isinstance(THAMES_CENTRAL_AREAS, list)
        assert len(THAMES_CENTRAL_AREAS) > 0

    @_quantlib_available
    def test_book_thames_central_areas_count(self):
        """Thames Central book should cover exactly 10 gauge areas."""
        from port.src.book import THAMES_CENTRAL_AREAS
        assert len(THAMES_CENTRAL_AREAS) == 10


# ---------------------------------------------------------------------------
# Tests: cmd_port imports book lazily
# ---------------------------------------------------------------------------

class TestGeopandasIsolation:
    """
    geopandas is an optional GIS dependency used only in FloodRiskModel,
    build_correlation_matrix, and the full depth-damage/calculate_flood_depths
    functions.  scalar_depth_damage (used by propertyts) must not require it.
    """

    def _simulate_no_geopandas(self, monkeypatch):
        for key in list(sys.modules.keys()):
            if key == 'geopandas' or key.startswith('geopandas.'):
                monkeypatch.delitem(sys.modules, key, raising=False)
        monkeypatch.setitem(sys.modules, 'geopandas', None)

    def _drop_floodrisk_cache(self, monkeypatch):
        for key in list(sys.modules.keys()):
            if key.startswith('models.floodrisk'):
                monkeypatch.delitem(sys.modules, key, raising=False)

    def test_spatial_importable_without_geopandas(self, monkeypatch):
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        mod = importlib.import_module('models.floodrisk.spatial')
        assert hasattr(mod, 'haversine_distance')

    def test_depth_damage_importable_without_geopandas(self, monkeypatch):
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        mod = importlib.import_module('models.floodrisk.depth_damage')
        assert hasattr(mod, 'scalar_depth_damage')

    def test_scalar_depth_damage_works_without_geopandas(self, monkeypatch):
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        mod = importlib.import_module('models.floodrisk.depth_damage')
        result = mod.scalar_depth_damage(0.5)
        assert 0.0 < result <= 1.0

    def test_floodrisk_init_does_not_import_flood_risk_model(self):
        """__init__.py must not have an executable FloodRiskModel import statement."""
        import inspect
        import models.floodrisk as pkg
        src = inspect.getsource(pkg)
        # Filter out comment lines — only check non-comment lines
        executable = '\n'.join(
            line for line in src.splitlines()
            if not line.strip().startswith('#')
        )
        assert 'FloodRiskModel' not in executable, (
            'models/floodrisk/__init__.py has an executable import of FloodRiskModel; '
            'this requires geopandas at import time for all floodrisk users.'
        )

    def test_propertyts_importable_without_geopandas(self, monkeypatch):
        """propertyts imports scalar_depth_damage — must work without geopandas."""
        self._simulate_no_geopandas(monkeypatch)
        self._drop_floodrisk_cache(monkeypatch)
        for key in list(sys.modules.keys()):
            if key.startswith('port.src.property.propertyts'):
                monkeypatch.delitem(sys.modules, key, raising=False)
        mod = importlib.import_module('port.src.property.propertyts')
        assert hasattr(mod, 'PropertyTimeSeriesGenerator')


class TestCmdPortLazyBookImport:

    def test_cmd_port_module_importable_without_quantlib(self, monkeypatch):
        """
        Importing app.commands.port must not trigger QuantLib.
        Only calling cmd_port() with --blotter should require it.
        """
        _simulate_no_quantlib(monkeypatch)
        for key in list(sys.modules.keys()):
            if key == "app.commands.port":
                monkeypatch.delitem(sys.modules, key, raising=False)
        mod = importlib.import_module("app.commands.port")
        assert hasattr(mod, "cmd_port")
        assert hasattr(mod, "register_parser")

    def test_book_import_inside_blotter_block(self):
        """
        The `from port.src.book import ...` statement in cmd_port must be
        inside the `if run_all or args.blotter:` block, not at module level.
        """
        import inspect
        from app.commands import port as _port_cmd
        src = inspect.getsource(_port_cmd)

        # The book import must appear after the blotter condition line
        blotter_idx = src.find("if run_all or args.blotter:")
        book_idx = src.find("from port.src.book import")

        assert blotter_idx != -1, "Could not find blotter block in cmd_port source"
        assert book_idx != -1, "Could not find book import in cmd_port source"
        assert book_idx > blotter_idx, (
            "from port.src.book import appears BEFORE the blotter block — "
            "this means QuantLib is required even for non-book steps."
        )
