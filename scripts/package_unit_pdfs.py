"""Copy each per-model test_results.pdf to an upload-named file.

The in-repo name test_results.pdf is load-bearing — src/routes/governance/audit.py
serves it and docs/models/model_risk/data.py probes it — so it stays put and the
upload copies are written alongside, flat, under docs/models/test_results/unit/.
"""

import os
import shutil
import sys

# Runnable from anywhere, not just the repo root.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from docs.models.test_results.generator.models import MODEL_INFO  # noqa: E402

DOCS = os.path.join(_ROOT, 'docs', 'models')
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
