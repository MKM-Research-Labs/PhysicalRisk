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

"""Tests for config.catch — catchment selection and its module loaders.

The covered half of this mixin is the happy path: the configured catchment exists, its
params module imports, and everything resolves. The uncovered half was every way that
fails, which is the half that matters — a mistyped catchment name should say which ones
exist, not raise a bare ``ModuleNotFoundError`` from three frames down.
"""

import pytest

from config.catch import CatchmentMixin


class _Catch(CatchmentMixin):
    """The mixin with the two attributes its host class supplies."""

    def __init__(self, catchments_dir, catchment_id="thames"):
        self.catchments_dir = catchments_dir
        self._catchment_id = catchment_id
        self._catchment_instance = None


@pytest.fixture
def catch(tmp_path):
    (tmp_path / "thames.py").write_text("catchment = object()\n")
    (tmp_path / "halong").mkdir()
    (tmp_path / "_private.py").write_text("")
    (tmp_path / "base.py").write_text("")
    return _Catch(tmp_path)


class TestCatchmentSelection:
    def test_a_module_file_is_accepted(self, catch):
        catch._set_catchment("thames")
        assert catch._catchment_id == "thames"

    def test_a_directory_is_accepted(self, catch):
        """A catchment may be a package as well as a single module."""
        catch._set_catchment("halong")
        assert catch._catchment_id == "halong"

    def test_an_unknown_catchment_names_the_alternatives(self, catch):
        """The error has to be actionable: a typo is the likeliest cause."""
        with pytest.raises(ValueError) as excinfo:
            catch._set_catchment("thmaes")
        message = str(excinfo.value)
        assert "thmaes" in message
        assert "thames" in message, "the error must list what is available"

    def test_switching_catchment_clears_the_cached_instance(self, catch):
        """A stale instance from the previous catchment would price the wrong river."""
        catch._catchment_instance = object()
        catch._set_catchment("halong")
        assert catch._catchment_instance is None

    def test_setting_the_same_catchment_keeps_the_cached_instance(self, catch):
        sentinel = object()
        catch._catchment_instance = sentinel
        catch._set_catchment("thames")
        assert catch._catchment_instance is sentinel


class TestListCatchments:
    def test_lists_modules_and_packages(self, catch):
        assert set(catch.list_catchments()) >= {"thames", "halong"}

    def test_excludes_private_and_infrastructure_modules(self, catch):
        listed = catch.list_catchments()
        assert "_private" not in listed
        assert "base" not in listed

    def test_a_missing_directory_is_empty_rather_than_an_error(self, tmp_path):
        """A checkout without the catchment tree should degrade, not explode."""
        assert _Catch(tmp_path / "absent").list_catchments() == []


class TestModuleLoaders:
    def test_missing_random_module_raises_a_named_importerror(self, catch):
        with pytest.raises(ImportError) as excinfo:
            catch.load_random_module("no_such_module")
        assert "no_such_module" in str(excinfo.value)
        assert "thames" in str(excinfo.value), "the error must name the catchment"

    def test_missing_params_module_raises_a_named_importerror(self, tmp_path):
        target = _Catch(tmp_path, catchment_id="atlantis")
        with pytest.raises(ImportError) as excinfo:
            target.load_params_module()
        assert "atlantis" in str(excinfo.value)

    def test_currency_falls_back_when_params_cannot_load(self, tmp_path):
        """A catchment that defines no currency is sterling, not a crash.

        This is a display default reached from a bare ``except``: the caller is
        formatting a number, and failing to format it is worse than assuming GBP.
        """
        assert _Catch(tmp_path, catchment_id="atlantis").CURRENCY == "GBP"


class TestCatchmentInstance:
    def test_a_missing_module_raises_importerror(self, tmp_path):
        with pytest.raises(ImportError):
            _Catch(tmp_path, catchment_id="atlantis").get_catchment()

    def test_a_cached_instance_is_returned_without_reimporting(self, catch):
        sentinel = object()
        catch._catchment_instance = sentinel
        assert catch.get_catchment() is sentinel


class TestProperties:
    def test_catchment_id_and_CATCHMENT_agree(self, catch):
        """Two public names for one value; they must not drift apart."""
        assert catch.catchment_id == catch.CATCHMENT == "thames"


class TestUseCatchment:
    """The scoped switch that replaced assigning ``config.catchment_id``.

    An unscoped switch leaks: a port generation that changed catchment and returned
    left every later caller on the wrong river, which is the kind of bug that produces
    plausible numbers for the wrong place.
    """

    def test_activates_for_the_block(self, catch):
        with catch.use_catchment("halong") as value:
            assert value == "halong"
            assert catch.catchment_id == "halong"

    def test_restores_afterwards(self, catch):
        with catch.use_catchment("halong"):
            pass
        assert catch.catchment_id == "thames"

    def test_restores_even_when_the_block_raises(self, catch):
        """The restore is in a finally for exactly this reason."""
        with pytest.raises(RuntimeError):
            with catch.use_catchment("halong"):
                raise RuntimeError("boom")
        assert catch.catchment_id == "thames"

    def test_validates_eagerly(self, catch):
        """An unknown catchment fails at the switch, not at first use inside it."""
        with pytest.raises(ValueError):
            with catch.use_catchment("thmaes"):
                pass
        assert catch.catchment_id == "thames"


class TestGetCatchment:
    def test_loads_and_caches_the_instance(self, catch, monkeypatch):
        import sys
        import types

        module = types.ModuleType("catch.thames")
        module.catchment = object()
        monkeypatch.setitem(sys.modules, "catch.thames", module)
        first = catch.get_catchment()
        assert first is module.catchment
        assert catch.get_catchment() is first, "the second call must not reimport"

    def test_a_module_without_a_catchment_attribute_is_an_error(self, catch, monkeypatch):
        """A params module that forgot to expose ``catchment`` fails clearly.

        Without this the caller gets an AttributeError somewhere later, far from the
        module that is actually incomplete.
        """
        import sys
        import types

        monkeypatch.setitem(sys.modules, "catch.thames",
                            types.ModuleType("catch.thames"))
        with pytest.raises(ImportError, match="must expose a 'catchment' attribute"):
            catch.get_catchment()
