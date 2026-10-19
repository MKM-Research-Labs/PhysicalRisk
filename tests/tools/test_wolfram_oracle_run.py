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

"""Tests for a tools.wolfram_oracle run: the CLI, its LaTeX, and both Wolfram routes.

No Wolfram kernel is needed. The live route is driven through a stand-in for
``wolframclient`` that answers each expression with the value Wolfram would
give; the wolframscript route through a stand-in output file. Either way the
run must fold Wolfram's numbers into the CSVs and the generated LaTeX.
"""

import json
import re
import sys
import types

import pytest

from tools.wolfram_oracle import __main__ as cli
from tools.wolfram_oracle import fit, latex, return_levels
from tools.wolfram_oracle._model import load_gev_fitter, provenance
from tools.wolfram_oracle._wl import evaluate_live, save_wolfram, write_wl

ONE_SERIES = {"n30_xi0.1": (30, 3.0, 0.4, 0.1)}
_SYNTHETIC = fit.synthetic_series


def _series():
    return _SYNTHETIC(ONE_SERIES)


@pytest.fixture(scope="module")
def answers():
    """{id: value} as Wolfram would return it, from the Python reference."""
    gev_fitter = load_gev_fitter()
    out = {}
    for r in return_levels.run(gev_fitter):
        out[r["id"] + "/level"] = r["level_ref"]
        out[r["id"] + "/exc"] = r["exc_ref"].replace("e", "*^")
    for r in fit.run(gev_fitter, _series(), ONE_SERIES):
        out[r["id"] + "/ll_at_model"] = r["ll_model"]
        out[r["id"] + "/fit_xi_loc_scale"] = "{%r, %r, %r}" % tuple(r["indep_xi_loc_scale"])
        out[r["id"] + "/ll_at_fit"] = r["ll_indep"]
    return out


@pytest.fixture
def synthetic(monkeypatch):
    monkeypatch.setattr(fit, "synthetic_series", _series)


def _fake_client(monkeypatch, by_expr, start_error=None):
    """Install a stand-in wolframclient whose session answers from ``by_expr``."""
    class Session:
        def __init__(self, kernel=None):
            self.kernel = kernel

        def set_parameter(self, name, value):
            self.parameters = {name: value}

        def start(self):
            if start_error:
                raise start_error

        def evaluate(self, expr):
            if expr == "$Version":
                return "14.3 (stand-in)"
            return by_expr[re.fullmatch(r"ToString\[\((.*)\), InputForm, NumberMarks -> False\]",
                                        expr, re.S).group(1)]

        def terminate(self):
            pass

    evaluation = types.SimpleNamespace(WolframLanguageSession=Session)
    language = types.SimpleNamespace(wlexpr=lambda s: s)
    monkeypatch.setitem(sys.modules, "wolframclient", types.ModuleType("wolframclient"))
    monkeypatch.setitem(sys.modules, "wolframclient.evaluation", evaluation)
    monkeypatch.setitem(sys.modules, "wolframclient.language", language)


def _by_expr(answers):
    gev_fitter = load_gev_fitter()
    items = return_levels.wl_items(return_levels.run(gev_fitter))
    items += fit.wl_items(fit.run(gev_fitter, _series(), ONE_SERIES))
    return {e: answers[i] for i, e in items}


class TestLiveSession:
    def test_without_wolframclient(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "wolframclient.evaluation", None)
        assert evaluate_live([("a", "1")]) == (None, None)

    def test_kernel_that_will_not_start(self, monkeypatch, capsys):
        _fake_client(monkeypatch, {}, start_error=RuntimeError("not activated"))
        assert evaluate_live([("a", "1")]) == (None, None)
        assert "not activated" in capsys.readouterr().err

    def test_a_live_run_is_folded_in_and_recorded(self, tmp_path, monkeypatch, synthetic, answers):
        _fake_client(monkeypatch, _by_expr(answers))
        assert cli.main(["--out", str(tmp_path), "--no-pdf"]) == 0
        assert "level_model_vs_wolfram" in (tmp_path / "return_levels.csv").read_text()
        assert "Level vs W." in (tmp_path / "evidence_tables_return_levels.tex").read_text()
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert "14.3 (stand-in)" in macros and "live kernel session" in macros
        saved = json.loads((tmp_path / "return_levels_wolfram.json").read_text())
        assert saved["wolfram_version"] == "14.3 (stand-in)"


class TestWolframscriptFile:
    def test_a_file_run_is_folded_in(self, tmp_path, synthetic, answers):
        assert cli.main(["--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        assert "Wolfram pending" in (tmp_path / "evidence_tables_macros.tex").read_text()
        for wl in tmp_path.glob("*.wl"):
            ids = re.findall(r'<\|"id" -> "([^"]+)"', wl.read_text())
            save_wolfram(tmp_path / f"{wl.stem}_wolfram.json", "14.3 (file)",
                         {i: answers[i] for i in ids})
        assert cli.main(["--out", str(tmp_path), "--no-pdf", "--no-live"]) == 0
        macros = (tmp_path / "evidence_tables_macros.tex").read_text()
        assert r"\bmWolfram}{14.3 (file)}" in macros
        assert "via wolframscript file" in macros and r"\bmOutcome}{all pass}" in macros

    def test_stale_output_is_ignored(self, tmp_path, capsys):
        write_wl(tmp_path / "x.wl", [("a", "1")], "x_wolfram.json")
        save_wolfram(tmp_path / "x_wolfram.json", "v", {"old": "1"})
        assert cli._from_file(tmp_path, "x.wl", [("a", "1")]) == (None, None)
        assert cli._wolfram(tmp_path, [("x.wl", [("a", "1")])], live=False) == (None, None, None)
        assert "different inputs" in capsys.readouterr().err


class TestCli:
    def test_gauge_export(self, tmp_path):
        g = tmp_path / "g.json"
        g.write_text(json.dumps({"G1": [float(v) for v in _series()["n30_xi0.1"]]}))
        assert cli.main(["--out", str(tmp_path), "--gauges", str(g), "--no-pdf", "--no-live"]) == 0
        assert "G1/gev" in (tmp_path / "fit.csv").read_text()
        assert "gauge export g.json" in (tmp_path / "evidence_tables_macros.tex").read_text()

    def test_build_failure_is_reported(self, tmp_path, synthetic, capsys):
        assert cli.main(["--out", str(tmp_path), "--no-live"]) == 1
        assert "Could not build" in capsys.readouterr().out

    def test_build_runs_the_makefile(self, tmp_path):
        (tmp_path / "Makefile").write_text("all:\n\ttrue\n")
        assert cli.build_pdf(tmp_path) is True

    def test_provenance_names_the_code(self):
        prov = provenance()
        assert prov["file"] == "src/models/hazard/gev.py" and len(prov["sha256"]) == 64


class TestLatex:
    def test_escaping_and_numbers(self):
        assert latex._esc("a_b & 5%") == r"a\_b \& 5\%"
        assert latex._sci(0) == "0" and latex._sci(2.5e-7) == r"$2.5\times10^{-7}$"

    def test_a_failure_is_marked(self, synthetic):
        rl = return_levels.run(load_gev_fitter(), {"g": (0.0, 1.0, 0.0)}, (100,))
        rl[0]["level_rel_err"] = 1.0
        fr = fit.run(load_gev_fitter(), _series(), ONE_SERIES)
        checks = latex.findings(rl, fr, None)
        assert checks[0][3] == r"\textbf{FAIL}" and checks[2][3] == r"\textbf{pending}"
        assert "1 fail; Wolfram pending" in latex.macros(
            provenance(), "x", rl, fr, None, None, return_levels.sign_trap())
