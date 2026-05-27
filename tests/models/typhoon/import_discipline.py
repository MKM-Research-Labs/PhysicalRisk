# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Import-discipline tests for the typhoon model.

Architectural rule: code under src/models/typhoon/ must be
catchment-agnostic. It must not:
  1. Import from data/catch/* (catchment-specific values)
  2. Import from the catchment-routing modules of the config package
     (config.catch is the routing surface; the typhoon parameter schema
     lives in config.typhoon and is allowed)
  3. Contain any catchment-name string literal in source code (these
     belong only in data/catch/<id>/ and tests/catch/<id>/)
  4. Import from port/* or app/* (orchestration layers)

Catchment-specific values reach the model only as a CatchmentTyphoonConfig
instance constructed by the boundary adapter in app/commands/port/stages/.
"""

import ast
from pathlib import Path

import pytest

import models.typhoon as typhoon_pkg


# Top-level packages the model must never import from.
FORBIDDEN_TOP_LEVELS = {"catch", "port", "app"}

# Catchment-name string literals that must not appear in model source.
# Add new catchments here as they're added under data/catch/.
FORBIDDEN_CATCHMENT_NAMES = {
    "halong", "Halong", "HALONG",
    "thames", "Thames", "THAMES",
    "hanoi", "Hanoi", "HANOI",
}


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


def _config_subpackages_imported(source: str):
    """Return the set of second-level names imported from the config package."""
    tree = ast.parse(source)
    sub: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None:
                parts = node.module.split(".")
                if parts[0] == "config" and len(parts) >= 2:
                    sub.add(parts[1])
    return sub


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

    def test_only_typhoon_subpackage_of_config_is_imported(self):
        """Within the config package, only config.typhoon (the parameter
        schema) is permitted. Catchment routing surfaces like config.catch
        or config.path are off-limits for the model."""
        allowed_config_subpackages = {"typhoon"}
        offenders: dict[str, set[str]] = {}
        for path in _typhoon_source_files():
            source = path.read_text()
            sub = _config_subpackages_imported(source)
            bad = sub - allowed_config_subpackages
            if bad:
                offenders[str(path)] = bad
        assert not offenders, (
            f"src/models/typhoon/ imported config subpackages other than "
            f"'typhoon': {offenders}"
        )

    @pytest.mark.parametrize("catchment_name", sorted(FORBIDDEN_CATCHMENT_NAMES))
    def test_no_catchment_name_in_source(self, catchment_name):
        """No catchment name may appear in src/models/typhoon/ source.

        Comments, docstrings, identifiers, string literals — all must be
        catchment-agnostic.
        """
        offenders: list[str] = []
        for path in _typhoon_source_files():
            if catchment_name in path.read_text():
                offenders.append(str(path))
        assert not offenders, (
            f"Found catchment-name '{catchment_name}' in src/models/typhoon/ "
            f"source: {offenders}. Catchment names belong only in "
            f"data/catch/<id>/ and tests/catch/<id>/."
        )

    def test_imports_are_only_from_allowed_namespaces(self):
        """Top-level imports should come from stdlib, well-known third-party
        libraries, the config schema, or the typhoon package itself.
        """
        ALLOWED_THIRD_PARTY = {
            "numpy", "scipy", "pandas", "pytest",
        }
        STDLIB_HINTS = {
            "ast", "collections", "dataclasses", "datetime", "enum",
            "functools", "itertools", "json", "math", "os", "pathlib",
            "random", "re", "sys", "time", "typing", "uuid", "warnings",
            "abc", "copy", "io", "logging",
        }
        ALLOWED = ALLOWED_THIRD_PARTY | STDLIB_HINTS | {"models", "config"}

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
