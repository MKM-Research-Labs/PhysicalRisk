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

"""SS-001's model document, tested as stated: what the repository holds.

The modules, paths and command line it names; the override control Q4 says does not
exist; the run time Q2 states; and the classifier result s7.3 cites as evidence. The
override is exercised in a separate interpreter, because applying it patches live
configuration modules for the rest of the process.
"""

import json
import os
import subprocess
import sys
import time

from config import config
from config.models import (
    ORACLE_SS_AUC_STATED,
    ORACLE_SS_CATEGORIES,
    ORACLE_SS_CLASSIFIER_SUMMARY,
    ORACLE_SS_COUNT,
    ORACLE_SS_EXAMPLE_GAUGE,
    ORACLE_SS_GAUGES_STATED,
    ORACLE_SS_PACKAGE,
    ORACLE_SS_SECONDS,
    ORACLE_SS_STATED_FILES,
    ORACLE_SS_STATED_MODULES,
    ORACLE_SS_STATED_PATHS,
)

_OVERRIDE = """
import json, pathlib, sys, tempfile
import config.storm_control as sc
if sys.argv[1] == "before":
    from port.src.storm_multi.generators.batch_generator import generate_event_set
path = pathlib.Path(tempfile.mkdtemp()) / "storm_control.json"
cats = json.loads(sys.argv[2])
path.write_text(json.dumps({"sections": {"storm_generation": {
    "sequence_probability": {c: 0.0 for c in cats},
    "duration_params": {c: [2, 3, 4] for c in cats}}}}))
sc._resolve_path = lambda catchment_id="thames": path
sc.apply_storm_control()
if sys.argv[1] == "after":
    from port.src.storm_multi.generators.batch_generator import generate_event_set
seqs = generate_event_set(2000, seed=1)
print(json.dumps({"multi": sum(q.num_storms > 1 for q in seqs),
                  "longest": max(s.duration_hours for q in seqs for s in q.storms)}))
"""


def _grep(pattern, paths, flags=("-lE",)):
    return subprocess.run(["git", "grep", *flags, pattern, "--", *paths], capture_output=True, text=True,
                          cwd=config.get_project_root()).stdout.splitlines()


def _override_run(order):
    root = config.get_project_root()
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(root / "src"), str(root)])}
    out = subprocess.run([sys.executable, "-c", _OVERRIDE, order, json.dumps(ORACLE_SS_CATEGORIES)],
                         capture_output=True, text=True, cwd=root, env=env)
    if out.returncode:
        return {"error": out.stderr.strip().splitlines()[-1]}
    r = json.loads(out.stdout.strip().splitlines()[-1])
    return {**r, "probability": r["multi"] == 0, "durations": r["longest"] <= 4}


def override():
    """Q4: no mechanism exists for runtime override of the tables. Judged by applying a
    storm_control.json that switches sequences off and shortens every storm, with the
    generator imported before it is applied and after."""
    callers = [p for p in _grep(r"apply_storm_control\(", ["src", "app", "phys.py"]) if "storm_control" not in p]
    runs = {o: _override_run(o) for o in ("before", "after")}
    return {"callers": callers, "runs": runs, "met": not callers}


def speed(code):
    """Q2: 10,000 sequences in under 60 seconds."""
    t = time.perf_counter()
    code.batch.generate_event_set(ORACLE_SS_COUNT, seed=1)
    secs = time.perf_counter() - t
    return {"seconds": secs, "met": secs < ORACLE_SS_SECONDS}


def modules():
    """s5.1: the package holds the modules and names it lists."""
    root = config.get_project_root() / ORACLE_SS_PACKAGE
    missing = []
    for rel, names in ORACLE_SS_STATED_MODULES.items():
        path = root / rel
        text = path.read_text() if path.exists() else None
        if text is None:
            missing.append(rel)
            continue
        missing += [f"{rel}:{n}" for n in names
                    if not any(f"{k} {n}" in text for k in ("def", "class")) and f"\n{n} =" not in text]
    return {"missing": missing, "met": not missing}


def paths():
    """s2.2, s5.5: the consumers at the paths given; the command line app.py port --stressm
    [--num-storms N] [--train-classifier]; the output files it names."""
    root = config.get_project_root()
    gone = [p for p in ORACLE_SS_STATED_PATHS if not (root / p).exists()]
    gone += [] if (root / "app.py").exists() else ["app.py"]
    gone += [f for f in ("--num-storms", "--train-classifier") if not _grep(f'"{f}"', ["app", "phys.py"], ("-lF",))]
    gone += [f for f in ORACLE_SS_STATED_FILES if not _grep(f, ["src"], ("-lF",))]
    consumers = sorted({p for p in _grep(r"storm_multi\.generators", ["src"]) if "storm_multi/" not in p})
    return {"gone": gone, "consumers": consumers, "met": not gone}


def classifier():
    """s7.3-s7.4: mean AUC-ROC ~0.993 across all 52 Thames gauges; GAUGE-8f1d368d as the example."""
    path = config.get_classifiers_dir() / ORACLE_SS_CLASSIFIER_SUMMARY
    if not path.exists():
        return {"found": False, "met": False}
    s = json.loads(path.read_text())
    ids = [g["gauge_id"] for g in s.get("gauges", [])]
    trained = s.get("num_trained", 0)
    auc = s.get("avg_auc_roc")
    return {"found": True, "trained": trained, "auc": auc, "example": ORACLE_SS_EXAMPLE_GAUGE in ids,
            "met": trained == ORACLE_SS_GAUGES_STATED and auc is not None
            and round(auc, 3) == ORACLE_SS_AUC_STATED and ORACLE_SS_EXAMPLE_GAUGE in ids}


def assess(code):
    return {"override": override(), "speed": speed(code), "modules": modules(), "paths": paths(),
            "classifier": classifier()}
