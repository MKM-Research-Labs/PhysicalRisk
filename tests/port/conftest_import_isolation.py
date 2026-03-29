# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Shared helpers for import-isolation tests (used by test_import_isolation_part*.py)."""

import sys


def _simulate_no_quantlib(monkeypatch):
    """
    Block 'QuantLib' in sys.modules so any `import QuantLib` raises ImportError.

    Python treats sys.modules[name] = None as a "blocked" import -- it raises
    ImportError immediately rather than searching for the package.
    """
    for key in list(sys.modules.keys()):
        if key == "QuantLib" or key.startswith("QuantLib."):
            monkeypatch.delitem(sys.modules, key, raising=False)
    monkeypatch.setitem(sys.modules, "QuantLib", None)


def _drop_port_src_cache(monkeypatch):
    """Remove all port.src.* entries from sys.modules so they reimport fresh."""
    for key in list(sys.modules.keys()):
        if key == "port.src" or key.startswith("port.src."):
            monkeypatch.delitem(sys.modules, key, raising=False)
