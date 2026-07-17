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

"""Shared isolation for data-lineage route tests.

These tests exercise endpoints that **write** PRS trades. The endpoints persist
through the ``database`` seam, which resolves the active catchment to
``config.get_input_dir()`` — so a test that only monkeypatches ``get_reports_dir`` /
``get_trading_dir`` leaves the seam pointed at the real ``data/input/<catchment>``
tree and its commits leak into (and read from) production data on the shared SSD.

``isolated_input_dir`` redirects ``get_input_dir`` (and the related path helpers) to
a per-test scratch dir and copies the real read-only inputs the trading engines need
(hazard curves, gauge + property portfolios) into it. PRS writes then land in the
scratch ``prs/`` dir and are read back from there, while revaluation still sees real
curves. Assert committed trades via ``database.get_prs_trade`` rather than a file path.
"""

import shutil

import pytest


# Real inputs the blotter/delta engines read but never mutate — copied into the
# scratch dir so revaluation behaves exactly as against production data.
_READONLY_INPUTS = ("gaugehc.json", "gauge.json", "property.json")


@pytest.fixture
def isolated_input_dir(tmp_path, monkeypatch):
    """Point every catchment-input path helper at a scratch dir seeded with the real
    read-only inputs. Returns the scratch input dir (its ``prs/`` subdir receives
    committed trades)."""
    from config import config

    input_dir = tmp_path / "input"
    (input_dir / "prs").mkdir(parents=True)
    (input_dir / "blotter").mkdir(parents=True)
    (input_dir / "gaugets").mkdir(parents=True)

    prod_input = config.get_input_dir()
    for fname in _READONLY_INPUTS:
        src = prod_input / fname
        if src.exists():
            shutil.copy(src, input_dir / fname)

    monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
    monkeypatch.setattr(config, "get_input_path", lambda filename: input_dir / filename)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: input_dir / "gaugets")
    monkeypatch.setattr(config, "get_trading_dir", lambda: input_dir / "blotter")
    monkeypatch.setattr(
        config, "get_reports_dir",
        lambda report_type=None: (input_dir / "prs") if report_type == "prs"
        else ((tmp_path / "reports" / report_type) if report_type
              else (tmp_path / "reports")),
    )
    return input_dir


@pytest.fixture
def lineage_app(isolated_input_dir):
    """A Flask app whose data backend (via ``create_app``) resolves to the isolated
    input dir. Construct the test client from this."""
    from server import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app
