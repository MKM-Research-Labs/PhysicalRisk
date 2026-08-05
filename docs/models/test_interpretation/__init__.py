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

"""Test Result Interpretation Agent — v0 deterministic spine.

This package implements phase v0 of docs/test-interpretation-agent-spec.md: it
reads the runner's machine-readable artefacts (``junit.xml`` + ``coverage.xml``
already written into the audit reports dir) and renders a templated assessment
PDF alongside ``full_audit_report.pdf``. No model is involved at this phase —
every section is mechanically derived, and everything that requires
interpretation is declared under **Uncertainties** rather than guessed.

Run with ``python -m docs.models.test_interpretation``.

Per coding-rule 4, this ``__init__`` defines no functions; the entry point lives
in ``report.py`` and is invoked via ``__main__.py``.
"""

__all__: list = []
