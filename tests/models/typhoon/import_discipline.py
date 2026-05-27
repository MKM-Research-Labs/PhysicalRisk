# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Import-discipline tests for the typhoon model.

Architectural rule: code under src/models/typhoon/ must be
catchment-agnostic. It must not import from:
  - data/catch/* (catchment-specific values)
  - config/* (catchment-routing layer)
  - port/* (storm orchestration)
  - app/* (CLI / orchestrator)

Catchment-specific values reach the model only as a CatchmentTyphoonConfig
instance constructed by the boundary adapter in app/commands/port/stages/.

This test inspects the actual source files with the AST so the guarantee
holds even when new files are added to src/models/typhoon/.
"""

import ast
from pathlib import Path

import pytest

import models.typhoon as typhoon_pkg


FORBIDDEN_TOP_LEVELS = {"catch", "config", "port", "app"}


def _typhoon_source_files():
    """Yield every .py file under src/models/typhoon/ except __pycache__."""
    pkg_dir = Path(typhoon_pkg.__file__).parent
    for path in sorted(pkg_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _imported_modules(source: str):
    """Return the set of top-level module names imported by source."""
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                modules.add(node.module.split(".")[0])
    return modules


class TestImportDiscipline:

    def test_at_least_one_source_file_exists(self):
        files = list(_typhoon_source_files())
        assert len(files) >= 1, "expected at least one .py file under src/models/typhoon/"

    @pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_TOP_LEVELS))
    def test_no_source_file_imports_forbidden_package(self, forbidden):
        offenders: list[str] = []
        for path in _typhoon_source_files():
            source = path.read_text()
            if forbidden in _imported_modules(source):
                offenders.append(str(path))
        assert not offenders, (
            f"src/models/typhoon/ files imported '{forbidden}': {offenders}. "
            f"The typhoon model must remain catchment-agnostic."
        )

    def test_imports_are_only_from_allowed_namespaces(self):
        """Top-level imports should come from stdlib, well-known third-party
        libraries, or the typhoon package itself. Anything else is flagged
        for review so future drift is caught.
        """
        # Conservative allowlist — extend deliberately when new deps are added.
        ALLOWED_THIRD_PARTY = {
            "numpy", "np", "scipy", "pandas", "pytest",
        }
        STDLIB_HINTS = {
            "ast", "collections", "dataclasses", "datetime", "enum",
            "functools", "itertools", "json", "math", "os", "pathlib",
            "random", "re", "sys", "time", "typing", "uuid", "warnings",
            "abc", "copy", "io", "logging",
        }
        ALLOWED = ALLOWED_THIRD_PARTY | STDLIB_HINTS | {"models"}

        unknown: dict[str, set[str]] = {}
        for path in _typhoon_source_files():
            source = path.read_text()
            mods = _imported_modules(source)
            bad = mods - ALLOWED
            if bad:
                unknown[str(path)] = bad
        assert not unknown, (
            f"Unexpected top-level imports in src/models/typhoon/: {unknown}. "
            f"If these are intended, extend the allowlist in this test."
        )
