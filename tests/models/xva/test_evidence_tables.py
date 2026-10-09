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

"""The model document's tables come from the committed evidence JSON
(docs/xva/validation_evidence.json) through docs/xva/_evidence_latex.py.

Regenerating them must reproduce every case, with LaTeX specials escaped --
a bare % once swallowed two rows of the sensitivity table.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "docs" / "xva"))

from _evidence_latex import _esc, write_tables  # noqa: E402

EVIDENCE = json.loads((ROOT / "docs/xva/validation_evidence.json").read_text())


@pytest.fixture(scope="module")
def tables(tmp_path_factory):
    out = tmp_path_factory.mktemp("tables")
    write_tables(EVIDENCE, out)
    return {p.name: p.read_text() for p in out.iterdir()}


def test_escape():
    assert _esc("R_C 20%") == r"R\_C 20\%"
    assert _esc("a & b") == r"a \& b"


def test_the_committed_evidence_passes_every_check():
    assert EVIDENCE["all_pass"] and not EVIDENCE["audit"]["quick"]
    assert EVIDENCE["audit"]["n_paths"] == 10_000


def test_every_table_file_is_written(tables):
    assert set(tables) == {f"evidence_tables_{n}.tex" for n in
                           ("macros", "checks", "mc_recon", "results", "sens")}


def test_every_sensitivity_case_is_a_row(tables):
    rows = [r for r in tables["evidence_tables_sens.tex"].splitlines() if r.endswith("\\\\")]
    cases = {r["case"] for r in EVIDENCE["sensitivities"]["rows"]}
    assert len(rows) == len(cases) + 1                    # + the header
    assert not any("%" in r.replace(r"\%", "") for r in rows)


def test_capital_table_reports_kva_in_bp_of_running_spread(tables):
    first = EVIDENCE["results"]["capital"]["rows"][0]
    assert f"{first['kva_bps']:.2f}" in tables["evidence_tables_results.tex"]
    assert first["kva_bps"] > 10                          # the 4.3bp slip was 10x too small
