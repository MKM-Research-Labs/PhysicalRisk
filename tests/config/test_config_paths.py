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

"""Tests for config.path._config_paths — the lightweight ``Config``'s path methods.

This mixin sat at 33% coverage because almost everything in the platform uses
``PortfolioConfig``, whose paths come from ``PortfolioPaths`` instead. "Almost" is the
problem: the lightweight ``Config`` is what a CLI or a script reaches for when it does
not want a whole portfolio, and a path accessor that is wrong there is wrong quietly —
it returns a ``Path`` that simply does not exist, and the caller writes into it.

Every method here is a pure function of the project root and the environment, so the
tests set the environment explicitly rather than depending on where the suite is run
from. ``MKM_PROJECT_ROOT`` is honoured by ``_get_project_root``, which makes the whole
mixin testable against a tmp directory.
"""

import os
from pathlib import Path

import pytest

from config.path import ConfigPaths


@pytest.fixture
def paths(tmp_path, monkeypatch):
    """A ConfigPaths rooted at a tmp directory, with the environment neutralised."""
    monkeypatch.setenv("MKM_PROJECT_ROOT", str(tmp_path))
    for name in ("MKM_INPUT_DIR", "MKM_OUTPUT_DIR", "MKM_CATCHMENT",
                 "MKM_GOVERNANCE_DATA_OVERRIDE"):
        monkeypatch.delenv(name, raising=False)
    return ConfigPaths()


class TestProjectRoot:
    def test_env_var_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MKM_PROJECT_ROOT", str(tmp_path))
        assert ConfigPaths().get_project_root() == tmp_path

    def test_falls_back_to_a_marker_search(self, monkeypatch):
        """Without the env var it walks up looking for setup.py, .git and friends.

        The real repository has those markers, so the search terminates on a directory
        that genuinely is the root rather than on the mixin's own parent.
        """
        monkeypatch.delenv("MKM_PROJECT_ROOT", raising=False)
        root = ConfigPaths().get_project_root()
        assert any((root / marker).exists()
                   for marker in ("setup.py", "pyproject.toml", ".git",
                                  "requirements.txt"))

    def test_the_search_terminates_at_the_filesystem_root(self, monkeypatch):
        """A checkout with no markers must not loop, and must return a usable path.

        The walk is bounded twice — ten levels, and the ``current.parent == current``
        test that only a filesystem root satisfies. Neither bound had a test, and an
        unbounded version of this loop would hang the process rather than fail it.

        Making every ``exists()`` false is what drives it all the way up: no marker is
        ever found, so the climb ends at ``/`` and takes the fallback return.
        """
        monkeypatch.delenv("MKM_PROJECT_ROOT", raising=False)
        monkeypatch.setattr(Path, "exists", lambda self: False)
        result = ConfigPaths()._get_project_root()
        assert isinstance(result, Path)
        assert result.is_absolute()


class TestDirectoryAccessors:
    def test_input_dir(self, paths, tmp_path):
        assert paths.get_input_dir() == tmp_path / "data" / "input"

    def test_output_dir(self, paths, tmp_path):
        assert paths.get_output_dir() == tmp_path / "data" / "output"

    def test_results_dir(self, paths, tmp_path):
        assert paths.get_results_dir() == tmp_path / "data" / "output" / "results"

    def test_data_dir(self, paths, tmp_path):
        assert paths.get_data_dir() == tmp_path / "data"

    def test_static_dir(self, paths, tmp_path):
        assert paths.get_static_dir() == tmp_path / "src" / "static"

    def test_property_reports_dir(self, paths, tmp_path):
        assert paths.get_property_reports_dir() == tmp_path / "data" / "output" / "property"

    def test_gauge_reports_dir(self, paths, tmp_path):
        assert paths.get_gauge_reports_dir() == tmp_path / "data" / "output" / "gauge"


class TestReportsDir:
    def test_without_a_type_returns_the_parent(self, paths, tmp_path):
        assert paths.get_reports_dir() == tmp_path / "data" / "output"

    def test_with_a_type_returns_the_subdirectory(self, paths, tmp_path):
        assert paths.get_reports_dir("audit") == tmp_path / "data" / "output" / "audit"


class TestCatchmentPaths:
    def test_catchment_input_defaults_to_thames(self, paths, tmp_path):
        assert paths._get_catchment_input_dir() == tmp_path / "data/input" / "thames"

    def test_catchment_input_follows_the_environment(self, paths, tmp_path, monkeypatch):
        monkeypatch.setenv("MKM_CATCHMENT", "halong")
        assert paths._get_catchment_input_dir() == tmp_path / "data/input" / "halong"

    def test_catch_dir_without_a_catchment(self, paths, tmp_path):
        assert paths.get_catch_dir() == tmp_path / "data" / "catch"

    def test_catch_dir_with_a_catchment(self, paths, tmp_path):
        assert paths.get_catch_dir("thames") == tmp_path / "data" / "catch" / "thames"


class TestEnvironmentOverrides:
    def test_input_dir_override(self, paths, tmp_path, monkeypatch):
        monkeypatch.setenv("MKM_INPUT_DIR", "elsewhere/in")
        assert paths.get_input_dir() == tmp_path / "elsewhere/in"

    def test_output_dir_override(self, paths, tmp_path, monkeypatch):
        monkeypatch.setenv("MKM_OUTPUT_DIR", "elsewhere/out")
        assert paths.get_output_dir() == tmp_path / "elsewhere/out"

