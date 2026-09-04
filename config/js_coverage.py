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

"""Ratchet baseline for JavaScript statement coverage.

The 130-odd served JS modules were unmeasured until 2026-09-01. A 99% gate on
a 2.71% reality gets switched off within the week, so the gate is a ratchet
instead: it fails when coverage drops, and it also fails when coverage rises
past the baseline, asking for the baseline to be raised. A floor that only
ever blocks regressions drifts silently away from the truth; one that insists
on being moved keeps the reported figure honest.

Raise :data:`BASELINE_PCT` in the same commit that adds the tests which earned
the rise — that is the whole ceremony.

The number lives here rather than in ``tests/js/jest.config.js`` so there is a
single source of truth (coding rule R1). ``app/commands/test/js.py`` passes it
to jest as ``--coverageThreshold`` and enforces the upper edge itself.
"""

#: Measured statement coverage the suite must hold, as a percentage.
#: 2026-09-04: 2.71% (276/10167 statements, 4 of 125 files touched, 87 tests).
#: 2026-09-04: 3.76% (383/10167, 6 of 125 files, 110 tests) — tranche 1 covered
#: the two PRS trade-commit paths, the modules the plan ranks first on risk.
#: 2026-09-04: 4.91% (500/10167, 7 of 125 files, 131 tests) — tranche 2 covered
#: the blotter trade actions: view, close-out settlement, contract retrieval.
#:
#: Ceiling note: 83 of the 119 still-uncovered files (5937 statements, 58% of
#: the tree) are concat fragments declaring bare functions, unreachable by
#: require(). Jest can therefore reach roughly 40% at best; the rest needs the
#: browser-side V8 measurement, which reads the bundle the loader assembles.
BASELINE_PCT = 4.9

#: How far above the baseline coverage may sit before the run asks for the
#: baseline to be raised. Wide enough to absorb a statement or two moving
#: between files, narrow enough that a real tranche of new tests trips it.
TOLERANCE_PCT = 0.5


def classify(measured_pct):
    """Return ``(ok, message)`` for a measured statement percentage.

    ``None`` — jest did not run, or wrote no summary — is not a failure here;
    the phase reports its own skip.
    """
    if measured_pct is None:
        return True, 'no JS coverage measured'
    if measured_pct < BASELINE_PCT:
        return False, (
            f'JS statement coverage {measured_pct:.2f}% is below the '
            f'{BASELINE_PCT}% baseline — a regression. Restore the missing '
            f'tests, or lower config.js_coverage.BASELINE_PCT deliberately '
            f'and say why.'
        )
    if measured_pct > BASELINE_PCT + TOLERANCE_PCT:
        return False, (
            f'JS statement coverage {measured_pct:.2f}% is above the '
            f'{BASELINE_PCT}% baseline — raise '
            f'config.js_coverage.BASELINE_PCT to {measured_pct:.1f} to lock '
            f'the gain in. A baseline left behind stops meaning anything.'
        )
    return True, f'JS statement coverage {measured_pct:.2f}% holds the baseline'
