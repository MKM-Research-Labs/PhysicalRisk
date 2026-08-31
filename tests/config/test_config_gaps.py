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

    def test_governance_override_redirects_the_repo_tree(self, monkeypatch, tmp_path):
        from config.path import PortfolioPaths

        elsewhere = tmp_path / "scratch-governance"
        monkeypatch.setenv("MKM_GOVERNANCE_DATA_OVERRIDE", str(elsewhere))
        instance = PortfolioPaths.__new__(PortfolioPaths)
        instance.project_root = tmp_path
        assert instance.get_governance_data_dir() == elsewhere

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
