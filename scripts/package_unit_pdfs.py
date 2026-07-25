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

"""Copy each per-model test_results.pdf to an upload-named file.

The in-repo name test_results.pdf is load-bearing — src/routes/governance/audit.py
serves it and docs/models/model_risk/data.py probes it — so it stays put and the
upload copies are written alongside, flat, under docs/models/test_results/unit/.

Run from the repo root as a module: ``python -m scripts.package_unit_pdfs``.
That puts the root on the path the same way ``python -m
docs.models.test_results.generator`` does, so the root comes from ``config``
rather than being hand-derived from ``__file__``.
"""

import os
import shutil

from docs.models.test_results.generator.models import MODEL_INFO

from config import config

DOCS = os.path.join(str(config.get_project_root()), 'docs', 'models')
OUT = os.path.join(DOCS, 'test_results', 'unit')

os.makedirs(OUT, exist_ok=True)

written, missing = [], []
for model_id, info in sorted(MODEL_INFO.items()):
    d = info.get('dir')
    if not d:
        continue
    src = os.path.join(DOCS, d, 'test_results.pdf')
    if not os.path.isfile(src):
        missing.append((model_id, d))
        continue
    dst = os.path.join(OUT, f'test_unit_{model_id}.pdf')
    shutil.copy2(src, dst)
    written.append((model_id, dst, os.path.getsize(dst)))

for model_id, dst, size in written:
    print(f'  {model_id:14s} {size/1024:7.1f} KB  {dst}')
print(f'\n{len(written)} written to {OUT}')
if missing:
    print('MISSING (no test_results.pdf generated):')
    for model_id, d in missing:
        print(f'  {model_id} -> {d}')
