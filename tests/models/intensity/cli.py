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
Tests for models.intensity.cli — CLI and comparison utilities.

Covers: compare_scenarios (default, named subset),
main() (compare mode, scenario mode, samples, return-period,
exceedance, json mode, default describe mode).
"""

import json
import sys

import pytest


# ===========================================================================
# compare_scenarios
# ===========================================================================

class TestCompareScenarios:

    def test_returns_string(self):
        from models.intensity.cli import compare_scenarios
        result = compare_scenarios()
        assert isinstance(result, str)

    def test_contains_header(self):
        from models.intensity.cli import compare_scenarios
        result = compare_scenarios()
        assert "Scenario Comparison" in result

    def test_contains_scenario_names(self):
        from models.intensity.cli import compare_scenarios
        from models.intensity.parameters import SCENARIO_FAMILIES
        result = compare_scenarios()
        for name in SCENARIO_FAMILIES:
            assert name in result

    def test_single_scenario(self):
        from models.intensity.cli import compare_scenarios
        from models.intensity.parameters import SCENARIO_FAMILIES
        first_name = list(SCENARIO_FAMILIES.keys())[0]
        result = compare_scenarios([first_name])
        assert first_name in result

    def test_two_scenarios(self):
        from models.intensity.cli import compare_scenarios
        from models.intensity.parameters import SCENARIO_FAMILIES
        names = list(SCENARIO_FAMILIES.keys())[:2]
        result = compare_scenarios(names)
        for name in names:
            assert name in result

    def test_none_uses_all_scenarios(self):
        from models.intensity.cli import compare_scenarios
        from models.intensity.parameters import SCENARIO_FAMILIES
        result = compare_scenarios(None)
        assert len(result) > 50  # Non-trivial output


# ===========================================================================
# main()
# ===========================================================================

class TestMain:

    def _run_main(self, args, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["prog"] + args)
        from models.intensity import cli
        # Need to reload to pick up fresh argparse state
        cli.main()

    def test_compare_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--compare"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        assert "Scenario Comparison" in captured.out

    def test_return_period_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--return-period", "100"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        assert "100" in captured.out

    def test_return_period_json_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--return-period", "50", "--json"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert "return_period_years" in data
        assert "intensity" in data

    def test_exceedance_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--exceedance", "70"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        assert "70" in captured.out

    def test_exceedance_json_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--exceedance", "80", "--json"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert "exceedance_probability" in data

    def test_samples_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--samples", "5"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        assert "5 samples" in captured.out

    def test_samples_json_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--samples", "3", "--json"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert "samples" in data
        assert len(data["samples"]) == 3

    def test_scenario_mode(self, monkeypatch, capsys):
        from models.intensity.parameters import SCENARIO_FAMILIES
        first = list(SCENARIO_FAMILIES.keys())[0]
        monkeypatch.setattr(sys, "argv", ["prog", "--scenario", first])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_json_default_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--json"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert "summary_statistics" in data

    def test_default_describe_mode(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog"])
        from models.intensity.cli import main
        main()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_seed_reproducible(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["prog", "--samples", "3", "--seed", "42", "--json"])
        from models.intensity.cli import main
        main()
        out1 = capsys.readouterr().out
        monkeypatch.setattr(sys, "argv", ["prog", "--samples", "3", "--seed", "42", "--json"])
        main()
        out2 = capsys.readouterr().out
        assert out1 == out2
