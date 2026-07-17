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
Import-isolation tests for port.src — part 1.

Covers: TestPackageDoesNotEagerlyImportBook,
TestGeneratorsImportableWithoutQuantLib, TestBookRequiresQuantLib.
"""

import importlib
import sys

import pytest

from tests.port.conftest_import_isolation import (
    _simulate_no_quantlib,
    _drop_port_src_cache,
)


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
            "port/src/__init__.py eagerly imports .book -- this forces QuantLib "
            "to be present even for non-book pipeline steps."
        )

    def test_port_src_init_source_has_no_generate_thames_central(self):
        """Package __init__.py must not expose generate_thames_central_book."""
        import port.src as _pkg
        assert not hasattr(_pkg, "generate_thames_central_book"), (
            "generate_thames_central_book is exported from port.src -- "
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
            f"Book symbols in port.src.__all__: {overlap} -- remove them so "
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
        not at module level.
        """
        _simulate_no_quantlib(monkeypatch)
        for key in list(sys.modules.keys()):
            if key.startswith("port.src.book") or key == "models.hazard.pricing":
                monkeypatch.delitem(sys.modules, key, raising=False)

        # Should NOT raise
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
