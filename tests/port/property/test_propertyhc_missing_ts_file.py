# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""A missing/unreadable per-property timeseries file must skip that property,
not abort the whole hazard-curve build.

Regression: a stale or incomplete peril ts directory (e.g. propertytsfaw/
missing a PROP-*.json that the glob still listed, or a concurrent
regeneration) used to raise FileNotFoundError out of _process_property and
crash the entire port at the wind hazard-curve stage.
"""

import json
from pathlib import Path

from port.src.property.hc.pricing._process import _ProcessMixin


class _Host(_ProcessMixin):
    def __init__(self):
        self.logged = []

    def log(self, msg, *a, **k):
        self.logged.append(msg)


class TestProcessPropertyMissingFile:
    def test_missing_file_returns_none(self):
        host = _Host()
        result = host._process_property(
            Path("/no/such/dir/PROP-deadbeef.json"), {}, lambda *a, **k: None, 100)
        assert result is None
        assert any("PROP-deadbeef.json" in m for m in host.logged)

    def test_corrupt_file_returns_none(self, tmp_path):
        bad = tmp_path / "PROP-corrupt.json"
        bad.write_text("{ this is not json")
        host = _Host()
        assert host._process_property(bad, {}, lambda *a, **k: None, 100) is None
