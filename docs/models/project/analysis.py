# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""File-size scanning and __init__.py substantive-code auditing."""

import ast
from pathlib import Path

from ._constants import (
    CODE_EXTENSIONS,
    EXCLUDED_FOLDERS,
    MIN_LINES,
    FileInfo,
    InitIssue,
)


def count_lines(file_path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as fh:
            return sum(1 for line in fh if line.strip())
    except Exception as exc:
        print(f"Warning: could not read {file_path}: {exc}")
        return 0


def analyze_code_files(root_path: Path,
                       exclude_folders=None,
                       code_extensions=None,
                       min_lines: int = MIN_LINES):
    """Return (all_files, large_files) sorted by line count descending."""
    if exclude_folders is None:
        exclude_folders = EXCLUDED_FOLDERS
    if code_extensions is None:
        code_extensions = CODE_EXTENSIONS

    all_files = []
    for item in root_path.rglob('*'):
        # Match exclusions against the path *below* root_path only, so an
        # ancestor directory (e.g. a .claude worktree) does not exclude the
        # entire tree.
        if any(ex in item.relative_to(root_path).parts for ex in exclude_folders):
            continue
        if item.is_file() and item.suffix.lower() in code_extensions:
            rel = item.relative_to(root_path)
            lc = count_lines(item)
            all_files.append(FileInfo(item, rel, item.suffix.lower(), lc))

    all_files.sort(key=lambda f: f.line_count, reverse=True)
    large_files = [f for f in all_files if f.line_count > min_lines]
    return all_files, large_files


def analyze_init_files(root_path: Path, exclude_folders=None) -> list:
    """Scan every __init__.py and return those with substantive code.

    Acceptable in __init__.py:
      - License header / comments / docstrings
      - import / from … import statements
      - Blueprint(…) assignments, logger = …, __all__ = […], simple constants
      - ``from . import submodule`` re-exports

    Flagged as substantive (should live in a dedicated module):
      - Any function definition (``def``)
      - Any class definition (``class``)
      - Any route / view decorator (``@…route``, ``@…before_request``, etc.)

    Returns a list of InitIssue namedtuples sorted by line_count descending.
    """
    if exclude_folders is None:
        exclude_folders = EXCLUDED_FOLDERS

    issues = []

    for init_path in root_path.rglob('__init__.py'):
        if any(ex in init_path.relative_to(root_path).parts for ex in exclude_folders):
            continue

        src = ''
        try:
            src = init_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        line_count = sum(1 for ln in src.splitlines() if ln.strip())

        # --- AST pass ---
        functions = []
        classes = []
        routes = 0
        has_blueprint = False

        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            # Blueprint assignment anywhere in module scope
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        name = (func.id if isinstance(func, ast.Name)
                                else func.attr if isinstance(func, ast.Attribute)
                                else '')
                        if name == 'Blueprint':
                            has_blueprint = True

        # Only inspect top-level nodes for functions/classes/decorators
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            # Count route/view decorators on top-level functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    dec_src = ast.unparse(dec) if hasattr(ast, 'unparse') else ''
                    if any(kw in dec_src for kw in ('route', 'before_request',
                                                     'after_request', 'errorhandler')):
                        routes += 1

        if functions or classes or routes:
            rel = init_path.relative_to(root_path)
            issues.append(InitIssue(
                relative_path=str(rel),
                line_count=line_count,
                functions=functions,
                classes=classes,
                routes=routes,
                has_blueprint=has_blueprint,
            ))

    issues.sort(key=lambda x: x.line_count, reverse=True)
    return issues
