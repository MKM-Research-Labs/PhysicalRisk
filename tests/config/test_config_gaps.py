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

"""Tests for the last uncovered branches in the config package.

Each of these is a fallback, an override or a boundary case: the code that runs when
the environment is not the developer's, which is exactly the code a suite run on the
developer's machine never reaches. They are grouped here rather than scattered because
they share that one property, not because they share a module.
"""

import os
from pathlib import Path

import pytest


class TestThemeResolve:
    """``config.theme.colour`` — the Python lookup for a design token."""

    def test_returns_the_token_value(self):
        from config.theme import THEME, colour
        assert colour("accent") == THEME["accent"]

    def test_an_unknown_token_says_so_and_says_where(self):
        """A bare KeyError from inside a page builder tells you a dict lacked a key.

        This has to say that a *token* does not exist, and where tokens live, because
        the caller is three frames away and the name is usually a typo.
        """
        from config.theme import colour
        with pytest.raises(KeyError) as excinfo:
            colour("acccent")
        message = str(excinfo.value)
        assert "acccent" in message
        assert "config/theme" in message


class TestServerPort:
    def test_port_follows_the_environment(self, monkeypatch):
        """A deployment that cannot choose its own port cannot run two of anything."""
        from config.server import _validated_port

        monkeypatch.setenv("MKM_SERVER_PORT", "6001")
        assert _validated_port() == 6001

    def test_port_defaults_when_unset(self, monkeypatch):
        from config.server import _validated_port

        monkeypatch.delenv("MKM_SERVER_PORT", raising=False)
        assert _validated_port() == 5013


class TestPortfolioPathOverrides:
    """The overrides the e2e Flask subprocess relies on.

    Without them a browser test writes into the real ``data/input`` tree and into the
    version-controlled governance data — both shared, and one of them on an external
    disk that other people's work also lives on.
    """

    @staticmethod
    def _fresh(monkeypatch, tmp_path, **env):
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        monkeypatch.setenv("MKM_PROJECT_ROOT", str(tmp_path))
        from config.path import PortfolioPaths

        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.project_root = tmp_path
        return instance

    def test_catchment_input_override_redirects_the_input_tree(
            self, monkeypatch, tmp_path):
        from config.path import PortfolioPaths

        elsewhere = tmp_path / "scratch-input"
        monkeypatch.setenv("MKM_CATCHMENT_INPUT_OVERRIDE", str(elsewhere))
        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.project_root = tmp_path
        instance._init_paths("thames")
        assert instance.input_dir == elsewhere

    def test_results_path_joins_the_results_dir(self, tmp_path):
        from config.path import PortfolioPaths

        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.results_dir = tmp_path / "results"
        assert instance.get_results_path("x.json") == tmp_path / "results" / "x.json"

    def test_stressm_dir_is_created_on_demand(self, tmp_path):
        """The caller writes into it immediately; a missing directory is a crash."""
        from config.path import PortfolioPaths

        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.input_dir = tmp_path / "in"
        result = instance.get_stressm_dir()
        assert result.is_dir()


class TestDiscountCurveBoundary:
    def test_a_tenor_beyond_the_curve_takes_the_longest_point(self):
        """A 60-year loan is priced off the 50-year point, not extrapolated.

        Extrapolating a discount curve past its longest quoted tenor invents a rate;
        holding the last point flat is the conventional and defensible choice.
        """
        from config.loan import DISCOUNT_CURVE, discount_rate

        longest = max(DISCOUNT_CURVE)
        assert discount_rate(longest + 25) == DISCOUNT_CURVE[longest]


class TestGaugeTitle:
    def test_a_gauge_without_a_name_shows_its_id(self):
        """Formatting is cosmetic: a gauge with no name must still be identifiable."""
        from config.format import gauge_title_py

        assert gauge_title_py("", "GAUGE-001") == "GAUGE-001"

    def test_a_named_gauge_shows_both(self):
        from config.format import gauge_title_py

        assert gauge_title_py("Kingston", "GAUGE-001") == "Kingston (GAUGE-001)"


class TestDiscountCurveShortEnd:
    def test_a_tenor_below_the_curve_takes_the_shortest_point(self):
        """The curve is clamped at both ends; only the long end had a test.

        Extrapolating below the shortest quoted tenor would invent a rate the same way
        extrapolating above the longest would.
        """
        from config.loan import DISCOUNT_CURVE, discount_rate

        shortest = min(DISCOUNT_CURVE)
        assert discount_rate(shortest / 2) == DISCOUNT_CURVE[shortest]

    def test_a_tenor_inside_the_curve_interpolates(self):
        from config.loan import DISCOUNT_CURVE, discount_rate

        tenors = sorted(DISCOUNT_CURVE)
        midpoint = (tenors[0] + tenors[1]) / 2
        low, high = DISCOUNT_CURVE[tenors[0]], DISCOUNT_CURVE[tenors[1]]
        assert min(low, high) <= discount_rate(midpoint) <= max(low, high)


class TestServerPortValidation:
    @pytest.mark.parametrize("value", ["0", "65536", "-1"])
    def test_a_port_outside_the_valid_range_is_rejected(self, monkeypatch, value):
        """Better to refuse at startup than to bind nothing and look healthy."""
        from config.server import _validated_port

        monkeypatch.setenv("MKM_SERVER_PORT", value)
        with pytest.raises(ValueError, match="outside valid range"):
            _validated_port()

    @pytest.mark.parametrize("value", ["1", "65535"])
    def test_the_range_boundaries_are_accepted(self, monkeypatch, value):
        from config.server import _validated_port

        monkeypatch.setenv("MKM_SERVER_PORT", value)
        assert _validated_port() == int(value)


class TestDisplayNameLastResort:
    def test_a_catchment_class_with_no_usable_name_falls_back(self, monkeypatch):
        """A params module can have the right shape and still name nothing.

        The search finds a class carrying DISPLAYNAME, reads it, and gets None. That
        is not an error — it is an incomplete catchment definition — so the label
        degrades to the generic word rather than rendering "None" in a heading.
        """
        import types

        from config import config, visual

        module = types.ModuleType("params")

        class _Catchment:
            DISPLAYNAME = None
            NAME = None

        module.SomeCatchment = _Catchment
        monkeypatch.setattr(config, "load_params_module", lambda: module)
        assert visual.get_catchment_display_name() == "catchment"


class TestStormControlTables:
    """storm_control.json reaches the storm sequence generator (MKM-SS-001 v3.0 Q4).

    The generator reads every table from ``config.port`` on each draw, so patching
    ``config.port`` is all an override needs, whatever was imported first. A control
    file's table rows are laid over the source table, so a file that sets one category
    does not drop the others.
    """

    @staticmethod
    def _apply(monkeypatch, section):
        from config import storm_control

        monkeypatch.setattr(storm_control, "load_storm_control", lambda _c: {"sections": {"s": section}})
        storm_control.apply_storm_control("thames")

    def test_a_table_row_is_laid_over_the_source_table(self, monkeypatch):
        import config.port as cp

        self._apply(monkeypatch, {"duration_params": {"minimal": [3, 7, 14]},
                                  "sequence_probability": {"minimal": 0.1}})
        assert cp.STORM_DURATION_PARAMS["minimal"] == (3, 7, 14)
        assert cp.STORM_DURATION_PARAMS["catastrophic"] == (48, 120, 240)
        assert cp.SEQUENCE_PROBABILITY == {**cp.SEQUENCE_PROBABILITY, "minimal": 0.1}
        assert cp.SEQUENCE_PROBABILITY["catastrophic"] == 0.85

    def test_an_override_reaches_a_generator_imported_before_it(self, monkeypatch):
        from port.src.storm_multi.generators.batch_generator import generate_event_set

        cats = ("moderate", "severe", "extreme", "catastrophic")
        self._apply(monkeypatch, {"sequence_probability": {c: 0.0 for c in cats},
                                  "duration_params": {c: [2, 3, 4] for c in cats}})
        seqs = generate_event_set(200, seed=1)
        assert all(q.num_storms == 1 for q in seqs)
        assert max(s.duration_hours for q in seqs for s in q.storms) <= 4

    def test_no_control_file_is_not_an_error(self, monkeypatch):
        """A deployment that never wrote one runs on the Python defaults."""
        from config import storm_control

        monkeypatch.setattr(storm_control, "load_storm_control", lambda _c: {})
        storm_control.apply_storm_control("thames")

    def test_a_control_file_with_no_sections_is_not_an_error(self, monkeypatch):
        from config import storm_control

        monkeypatch.setattr(storm_control, "load_storm_control",
                            lambda _c: {"sections": {}})
        storm_control.apply_storm_control("thames")


class TestDataRootOverride:
    """``MKM_DATA_ROOT`` moves the whole data tree, not just the input dir.

    Without it the tree resolves under ``<repo>/data``, which on the
    development machine is a symlink to external storage — and because
    ``PortfolioConfig`` is constructed at import time and mkdirs the input dir,
    an absent volume makes even ``phys.py --help`` fail. The override is what
    lets a throwaway portfolio be generated, tested and deleted locally.
    """

    @staticmethod
    def _paths(monkeypatch, project_root, data_root=None):
        from config.path import PortfolioPaths

        if data_root is not None:
            monkeypatch.setenv("MKM_DATA_ROOT", str(data_root))
        else:
            monkeypatch.delenv("MKM_DATA_ROOT", raising=False)
        monkeypatch.delenv("MKM_CATCHMENT_INPUT_OVERRIDE", raising=False)
        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.project_root = project_root
        return instance

    def test_defaults_to_the_repo_data_dir(self, monkeypatch, tmp_path):
        p = self._paths(monkeypatch, tmp_path)
        assert p._data_root() == tmp_path / "data"

    def test_override_moves_the_root(self, monkeypatch, tmp_path):
        elsewhere = tmp_path / "throwaway"
        p = self._paths(monkeypatch, tmp_path, elsewhere)
        assert p._data_root() == elsewhere

    def test_every_branch_of_the_tree_follows(self, monkeypatch, tmp_path):
        """input, output and results must all move together — one left behind
        would still reach for the unmounted volume."""
        elsewhere = tmp_path / "throwaway"
        p = self._paths(monkeypatch, tmp_path, elsewhere)
        p._init_paths("thames")
        assert p.input_dir == elsewhere / "input" / "thames"
        assert p.results_dir == elsewhere / "output" / "results"
        # get_input_dir returns the catchment dir, not its parent
        assert p.get_input_dir() == elsewhere / "input" / "thames"
        assert p.get_output_dir() == elsewhere / "output"
        assert p.get_data_dir() == elsewhere

    def test_the_admin_credential_follows_too(self, monkeypatch, tmp_path):
        """The port gate's credential sits beside the portfolio it guards.

        Anchored to the repo instead, a throwaway root would resolve to
        ``<repo>/data/.port_admin`` — a dangling symlink with the volume
        detached, which crashes the first-run branch on ``mkdir``.
        """
        elsewhere = tmp_path / "throwaway"
        p = self._paths(monkeypatch, tmp_path, elsewhere)
        assert p.get_admin_credential_path() == elsewhere / ".port_admin"

    def test_catch_is_deliberately_exempt(self, monkeypatch, tmp_path):
        """Catchment parameters are the one branch that does NOT follow.

        They are version-controlled generation inputs, so a vendored
        ``catch/`` in the repo is preferred over the data root — that is
        what makes a run possible with the volume detached at all. The
        resolution order itself is covered by
        :class:`TestCatchmentSearchPaths`; what matters here is only that
        the answer is never the unmounted default.
        """
        elsewhere = tmp_path / "throwaway"
        p = self._paths(monkeypatch, tmp_path, elsewhere)
        p._init_paths("thames")
        assert p.catchments_dir in p.catchment_search_paths()
        assert p.catchments_dir != p.project_root / "data" / "catch"

    def test_catchment_input_override_still_wins_for_input(
            self, monkeypatch, tmp_path):
        """The e2e suite points MKM_CATCHMENT_INPUT_OVERRIDE at a tmp catchment
        copy; the narrower override must not be overruled by the broader one."""
        from config.path import PortfolioPaths

        data_root = tmp_path / "throwaway"
        catchment = tmp_path / "just-this-catchment"
        monkeypatch.setenv("MKM_DATA_ROOT", str(data_root))
        monkeypatch.setenv("MKM_CATCHMENT_INPUT_OVERRIDE", str(catchment))
        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.project_root = tmp_path
        instance._init_paths("thames")
        assert instance.input_dir == catchment
        # ...but everything else still follows the data root
        assert instance.results_dir == data_root / "output" / "results"


class TestCatchmentSearchPaths:
    """Catchment parameters are generation INPUTS and configuration, so the
    preferred home is the version-controlled ``catch/`` package. Un-migrated
    catchments must keep resolving under the data root, so both are searched.
    """

    @staticmethod
    def _paths(monkeypatch, project_root, data_root):
        from config.path import PortfolioPaths

        monkeypatch.setenv("MKM_DATA_ROOT", str(data_root))
        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.project_root = project_root
        return instance

    def test_repo_is_searched_before_the_data_root(self, monkeypatch, tmp_path):
        p = self._paths(monkeypatch, tmp_path, tmp_path / "d")
        assert p.catchment_search_paths() == [
            tmp_path / "catch", tmp_path / "d" / "catch"]

    def test_falls_through_while_the_package_is_empty(self, monkeypatch, tmp_path):
        """The vendored package ships with __init__.py and README.md before any
        catchment is migrated. Treating those as content would point every
        consumer at a directory holding no parameters."""
        repo_catch = tmp_path / "catch"
        repo_catch.mkdir()
        (repo_catch / "__init__.py").write_text("")
        (repo_catch / "README.md").write_text("# docs")
        data_catch = tmp_path / "d" / "catch"
        data_catch.mkdir(parents=True)
        (data_catch / "thames.py").write_text("BOUNDS = (0, 0, 1, 1)")

        p = self._paths(monkeypatch, tmp_path, tmp_path / "d")
        assert p._catchments_dir() == data_catch

    def test_repo_wins_once_a_catchment_is_vendored(self, monkeypatch, tmp_path):
        repo_catch = tmp_path / "catch"
        repo_catch.mkdir()
        (repo_catch / "__init__.py").write_text("")
        (repo_catch / "thames.py").write_text("BOUNDS = (0, 0, 1, 1)")
        data_catch = tmp_path / "d" / "catch"
        data_catch.mkdir(parents=True)
        (data_catch / "thames.py").write_text("BOUNDS = (9, 9, 9, 9)")

        p = self._paths(monkeypatch, tmp_path, tmp_path / "d")
        assert p._catchments_dir() == repo_catch

    def test_a_directory_catchment_also_counts(self, monkeypatch, tmp_path):
        """Catchments come as a module or a package; both are selectable."""
        repo_catch = tmp_path / "catch"
        (repo_catch / "halong").mkdir(parents=True)
        (repo_catch / "__init__.py").write_text("")
        p = self._paths(monkeypatch, tmp_path, tmp_path / "d")
        assert p._holds_a_catchment(repo_catch)

    def test_missing_directory_is_not_a_catchment_home(self, monkeypatch, tmp_path):
        from config.path import PortfolioPaths
        assert not PortfolioPaths._holds_a_catchment(tmp_path / "nope")
