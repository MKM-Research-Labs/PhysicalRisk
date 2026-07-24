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

"""Attribution of test files to inventory models, and its reconciliation.

Tests are attributed by *rule* rather than by exact path.  A rule is either

    'tests/models/seismic/'             directory prefix — that directory and
                                        everything beneath it
    'tests/models/typhoon/genesis*.py'  file glob — files matching the pattern
                                        in exactly that directory (the glob
                                        never crosses a directory boundary)

Rules resolve most-specific-first — a file glob beats a directory prefix, and a
longer directory prefix beats a shorter one — so the order they are written in
does not change the outcome.

The glob form exists for survival.  Splitting ``genesis.py`` into
``genesis_part1.py`` .. ``genesis_part4.py`` is routine in this tree, and under
the old exact-path mapping it silently stripped a model of its test evidence:
the renamed files simply missed the map and fell through to the PLATFORM
bucket, with nothing to signal the loss.  Rules absorb splits of that shape;
:func:`reconcile` catches the ones they cannot.
"""

import fnmatch
import importlib.util
import os
from collections import defaultdict

from .models import MODEL_INFO, TEST_MODEL_RULES

# Buckets that exist to catch everything else — they are never rule targets and
# must not be reported as models lacking evidence.
_SYNTHETIC_MODELS = {'PLATFORM', 'E2E-ALL'}

# E2E runs under Playwright in a separate phase, so it is outside every
# reconciliation the unit suite performs.
_EXCLUDED_TOP_LEVEL = ('tests/e2e/',)


# ---------------------------------------------------------------------------
# Rule resolution
# ---------------------------------------------------------------------------

class Resolver:
    """Resolves paths to model IDs under a fixed set of rules."""

    def __init__(self, rules):
        self.rules = list(rules)
        self._globs = defaultdict(list)   # dirname -> [(pattern, model_id), ...]
        self._prefixes = []               # [(prefix, model_id), ...]
        for rule, model_id in self.rules:
            if rule.endswith('/'):
                self._prefixes.append((rule, model_id))
            else:
                dirname, pattern = os.path.split(rule)
                self._globs[dirname].append((pattern, model_id))
        # Longest prefix first, so a rule for a subdirectory wins over one for
        # the tree above it whichever order they were written in.
        self._prefixes.sort(key=lambda rp: len(rp[0]), reverse=True)

    def model_for(self, rel_path):
        """Return the model ID attributed to ``rel_path``, or ``'PLATFORM'``.

        ``rel_path`` is relative to the project root and uses forward slashes.
        File globs are tried before directory prefixes: naming a file is always
        more specific than naming the directory it sits in.
        """
        dirname, basename = os.path.split(rel_path)
        for pattern, model_id in self._globs.get(dirname, ()):
            if fnmatch.fnmatchcase(basename, pattern):
                return model_id
        for prefix, model_id in self._prefixes:
            if rel_path.startswith(prefix):
                return model_id
        return 'PLATFORM'

    def claimed_by(self, rule, model_id, rel_paths):
        """Return the paths ``rule`` claims *and* wins.

        A rule shadowed entirely by a more specific one reads as unused rather
        than as satisfied — it is contributing nothing and should be removed.
        """
        if rule.endswith('/'):
            candidates = (p for p in rel_paths if p.startswith(rule))
        else:
            dirname, pattern = os.path.split(rule)
            candidates = (
                p for p in rel_paths
                if os.path.dirname(p) == dirname
                and fnmatch.fnmatchcase(os.path.basename(p), pattern)
            )
        return [p for p in candidates if self.model_for(p) == model_id]


_DEFAULT_RESOLVER = Resolver(TEST_MODEL_RULES)


def model_for_path(rel_path):
    """Attribute ``rel_path`` using the project's own rules."""
    return _DEFAULT_RESOLVER.model_for(rel_path)


# ---------------------------------------------------------------------------
# Static collection — mirrors what pytest will collect
# ---------------------------------------------------------------------------

def _non_prefixed_dirs(project_root):
    """Load the collection registry from tests/conftest/collection.py.

    Read from the file the pytest hook itself uses rather than restated here:
    a second copy of this set is exactly the kind of drift this module exists
    to prevent.
    """
    path = os.path.join(str(project_root), 'tests', 'conftest', 'collection.py')
    spec = importlib.util.spec_from_file_location('_mkm_test_collection', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._NON_PREFIXED_DIRS


def collectable_paths(project_root):
    """List the test files pytest would collect, relative to the project root.

    Applies the same two rules as ``tests/conftest/collection.py``: any
    ``test_*.py``, plus any other ``.py`` file sitting directly in one of the
    registered non-prefixed directories.  E2E is excluded — it runs under
    Playwright in its own phase.
    """
    non_prefixed = _non_prefixed_dirs(project_root)
    tests_root = os.path.join(str(project_root), 'tests')
    found = []

    for dirpath, dirnames, filenames in os.walk(tests_root):
        dirnames[:] = [d for d in dirnames if d != '__pycache__']
        parent = os.path.basename(dirpath)
        for name in filenames:
            if not name.endswith('.py'):
                continue
            if name.startswith('test_'):
                pass
            elif name.startswith(('_', 'conftest')) or parent not in non_prefixed:
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), str(project_root))
            rel = rel.replace(os.sep, '/')
            if rel.startswith(_EXCLUDED_TOP_LEVEL):
                continue
            found.append(rel)

    return sorted(found)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

class Reconciliation:
    """Outcome of checking the attribution rules against what pytest collects."""

    def __init__(self, unused_rules, models_without_tests, per_model, total_files):
        self.unused_rules = unused_rules                  # [(rule, model_id)]
        self.models_without_tests = models_without_tests  # [model_id]
        self.per_model = per_model                        # model_id -> [rel_path]
        self.total_files = total_files

    @property
    def ok(self):
        return not self.unused_rules and not self.models_without_tests

    @property
    def attributed_files(self):
        return sum(len(v) for k, v in self.per_model.items()
                   if k not in _SYNTHETIC_MODELS)


def reconcile(rel_paths, rules=None):
    """Check every rule and every documented model against ``rel_paths``.

    Two conditions fail, both of which used to pass silently:

      * a rule that claims no collected file — the tests it named were
        renamed, split or deleted, and the model has lost that evidence;
      * a model with a documentation directory but no attributed tests — its
        ``test_results.tex`` would be generated empty.
    """
    rel_paths = list(rel_paths)
    resolver = _DEFAULT_RESOLVER if rules is None else Resolver(rules)

    per_model = defaultdict(list)
    for rel in rel_paths:
        per_model[resolver.model_for(rel)].append(rel)

    unused_rules = [
        (rule, model_id) for rule, model_id in resolver.rules
        if not resolver.claimed_by(rule, model_id, rel_paths)
    ]

    documented = {model_id for _, model_id in resolver.rules}
    if rules is None:
        # A model with its own documentation directory is expected to carry
        # evidence whether or not a rule currently names one of its files.
        documented |= {
            model_id for model_id, info in MODEL_INFO.items()
            if model_id not in _SYNTHETIC_MODELS and info.get('dir')
        }
    models_without_tests = sorted(m for m in documented if not per_model.get(m))

    return Reconciliation(unused_rules, models_without_tests,
                          dict(per_model), len(rel_paths))


def format_reconciliation(rec):
    """Render a reconciliation as an operator-readable block."""
    lines = ['Model test attribution', '-' * 60]

    attributed = rec.attributed_files
    pct = (100.0 * attributed / rec.total_files) if rec.total_files else 0.0
    lines.append(
        f'  {attributed} of {rec.total_files} collected test files attributed '
        f'to a model ({pct:.1f}%)'
    )
    lines.append(f'  {len(rec.per_model.get("PLATFORM", []))} files in the '
                 f'PLATFORM bucket')

    if rec.unused_rules:
        lines.append('')
        lines.append(f'  ✗ {len(rec.unused_rules)} attribution rule(s) match no '
                     f'collected test file:')
        for rule, model_id in rec.unused_rules:
            lines.append(f'      {model_id:14s} {rule}')
        lines.append('')
        lines.append('    The named tests were renamed, split or deleted, and '
                     'that model has')
        lines.append('    lost the evidence. Repoint or remove the rule in')
        lines.append('    docs/models/test_results/generator/models.py.')

    if rec.models_without_tests:
        lines.append('')
        lines.append(f'  ✗ {len(rec.models_without_tests)} model(s) with no '
                     f'attributed tests:')
        for model_id in rec.models_without_tests:
            name = MODEL_INFO.get(model_id, {}).get('name', model_id)
            lines.append(f'      {model_id:14s} {name}')

    if rec.ok:
        lines.append('')
        lines.append('  ✓ every rule resolves and every model has test evidence')

    return '\n'.join(lines)


def paths_for_models(model_ids, project_root):
    """Absolute paths of the collectable test files attributed to ``model_ids``."""
    wanted = set(model_ids)
    return [
        os.path.join(str(project_root), rel)
        for rel in collectable_paths(project_root)
        if model_for_path(rel) in wanted
    ]
