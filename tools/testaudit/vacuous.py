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

"""Find tests that can pass without verifying what they claim.

Four shapes, all drawn from instances actually found in this repo rather than
from a general list of smells:

  NO_ASSERT      the body contains no assertion of any kind — no assert, no
                 pytest.raises, no unittest assertSomething, no mock
                 assert_called*. It cannot fail except by raising.
  ALL_GUARDED    every assertion sits inside an `if`, and nothing asserts on
                 the other branch. When the condition is false the test passes
                 having checked nothing. (The e2e skips were this shape.)
  SKIP_THEN_NOT  `if cond: skip()` followed by an assertion that cond is
                 false — unreachable by construction.
  TAUTOLOGY      `assert True`, `assert x == x`, `assert 1`.

Deliberately NOT reported: a test whose only assertion is inside `with
pytest.raises(...)`, which is a real assertion; parametrised tests; and tests
that call a helper doing the asserting, which cannot be seen from one file.
Those would drown the signal.
"""
import ast, pathlib, sys
from collections import Counter

ASSERT_CALLS = ('raises', 'warns', 'approx')


def _is_assertion(node):
    if isinstance(node, ast.Assert):
        return True
    if isinstance(node, ast.With):
        for item in node.items:
            c = item.context_expr
            if isinstance(c, ast.Call):
                f = c.func
                name = getattr(f, 'attr', getattr(f, 'id', ''))
                if name in ASSERT_CALLS:
                    return True
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        f = node.value.func
        name = getattr(f, 'attr', '')
        if name.startswith('assert'):          # assertEqual, assert_called_with
            return True
    return False


def _assertions(fn):
    return [n for n in ast.walk(fn) if _is_assertion(n)]


def _top_level_assertions(fn):
    """Assertions not nested inside an if/for/while/try-handler."""
    out = []

    def walk(body, guarded):
        for n in body:
            if _is_assertion(n) and not guarded:
                out.append(n)
            if isinstance(n, ast.If):
                walk(n.body, True); walk(n.orelse, True)
            elif isinstance(n, (ast.For, ast.While)):
                walk(n.body, True); walk(n.orelse, True)
            elif isinstance(n, ast.Try):
                walk(n.body, guarded)
                for h in n.handlers: walk(h.body, True)
                walk(n.orelse, True); walk(n.finalbody, guarded)
            elif isinstance(n, ast.With):
                if _is_assertion(n) and not guarded:
                    pass
                walk(n.body, guarded)
    walk(fn.body, False)
    return out


def _skips(fn):
    """`if <cond>: pytest.skip(...)` -> the condition source."""
    found = []
    for n in ast.walk(fn):
        if not isinstance(n, ast.If):
            continue
        for stmt in n.body:
            call = stmt.value if isinstance(stmt, ast.Expr) else None
            if isinstance(call, ast.Call):
                name = getattr(call.func, 'attr', getattr(call.func, 'id', ''))
                if name == 'skip':
                    found.append(n.test)
    return found


def _tautology(a):
    t = a.test
    if isinstance(t, ast.Constant) and t.value in (True, 1):
        return True
    if isinstance(t, ast.Compare) and len(t.comparators) == 1:
        try:
            return (ast.dump(t.left) == ast.dump(t.comparators[0])
                    and isinstance(t.ops[0], (ast.Eq, ast.Is)))
        except Exception:
            return False
    return False




def _is_exact_negation(skip_src, assert_src):
    """True when the assertion is precisely `not <skip condition>`."""
    a, b = skip_src.strip(), assert_src.strip()
    return (a == f"not {b}" or b == f"not {a}"
            or a == f"not ({b})" or b == f"not ({a})")


def _guard_kinds(fn):
    """Which construct guards the assertions: {'if'}, {'loop'} or both."""
    kinds = set()

    def walk(body, guard):
        for n in body:
            if _is_assertion(n) and guard:
                kinds.add(guard)
            if isinstance(n, ast.If):
                walk(n.body, 'if'); walk(n.orelse, 'if')
            elif isinstance(n, (ast.For, ast.While)):
                walk(n.body, 'loop'); walk(n.orelse, 'loop')
            elif isinstance(n, ast.Try):
                walk(n.body, guard)
                for h in n.handlers: walk(h.body, 'if')
                walk(n.orelse, 'if'); walk(n.finalbody, guard)
            elif isinstance(n, ast.With):
                walk(n.body, guard)
    walk(fn.body, None)
    return kinds


def _python_files(root):
    """Every .py under *root*, or *root* itself when it is a file.

    rglob on a file path matches nothing, so passing one file used to scan
    zero files and report "0 findings" — a clean bill of health for work
    never done, which is the shape this whole tool exists to find.
    """
    p = pathlib.Path(root)
    if p.is_file():
        return [p]
    return sorted(p.rglob('*.py'))


def scan(root):
    findings = []
    if not pathlib.Path(root).exists():
        raise SystemExit(f"no such path: {root}")
    for path in _python_files(root):
        if '__pycache__' in str(path):
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not fn.name.startswith('test_'):
                continue
            asserts = _assertions(fn)
            rel = f"{path}:{fn.lineno}"
            if not asserts:
                findings.append(('NO_ASSERT', rel, fn.name, ''))
                continue
            for a in asserts:
                if isinstance(a, ast.Assert) and _tautology(a):
                    findings.append(('TAUTOLOGY', rel, fn.name,
                                     ast.unparse(a)[:70]))
            skips = _skips(fn)
            if skips:
                srcs = {ast.unparse(s) for s in skips}
                for a in asserts:
                    if not isinstance(a, ast.Assert):
                        continue
                    txt = ast.unparse(a.test)
                    for s in srcs:
                        # Only the exact negation. `skip on not pts` followed
                        # by `'elevation_m' in pts` is NOT this shape: the
                        # skip guards absent data and the assertion checks a
                        # different property of it. Substring matching flagged
                        # 30 of those as vacuous when 1 was.
                        if _is_exact_negation(s, txt):
                            findings.append(('SKIP_THEN_NOT', rel, fn.name,
                                             f"skip on `{s}` then `{txt}`"[:90]))
                            break
            if asserts and not _top_level_assertions(fn):
                kinds = _guard_kinds(fn)
                if kinds == {'if'}:
                    findings.append(('IF_GUARDED', rel, fn.name,
                        f"{len(asserts)} assertion(s), all inside if — pass when false"))
                elif kinds == {'loop'}:
                    findings.append(('LOOP_ONLY', rel, fn.name,
                        f"{len(asserts)} assertion(s), all inside a loop — pass when empty"))
    return findings


findings = scan(sys.argv[1] if len(sys.argv) > 1 else 'tests')
counts = Counter(k for k, *_ in findings)
print(f"{len(findings)} findings across {sum(counts.values())} sites\n")
for kind, n in counts.most_common():
    print(f"  {kind:14s} {n}")
print()
for kind in ('TAUTOLOGY', 'SKIP_THEN_NOT', 'IF_GUARDED', 'LOOP_ONLY', 'NO_ASSERT'):
    rows = [f for f in findings if f[0] == kind]
    if not rows:
        continue
    print(f"--- {kind} ({len(rows)}) " + "-" * 40)
    for _, loc, name, detail in rows[:25]:
        print(f"  {loc}  {name}")
        if detail:
            print(f"      {detail}")
    if len(rows) > 25:
        print(f"  … and {len(rows)-25} more")
    print()
