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

"""pytest collection hook and non-prefixed test directory registry."""

import pytest

# All subpackage directories whose .py files (without test_ prefix) are tests.
_NON_PREFIXED_DIRS = {
    # models
    "models", "mortgage", "schedule", "book", "delta", "pnl",
    "intensity", "stormgauge", "prs", "floodrisk", "valuation",
    "typhoon", "wind_field", "windspeed", "winddamage",
    # port
    "gauge", "property", "storm", "hazard", "cdm",
    "pipeline", "propertyhc", "stress", "counterparty",
    "eod", "stormts",
    # reports
    "pdf", "risk", "pages",
    # routes
    "routes", "data", "governance",
    # visual
    "phase", "integration", "popup", "ghc", "utils", "layer", "core",
    # shared names used in multiple trees
    "trading",
    # standalone
    "services", "catch", "loaders", "mortgage", "rloan",
    # split sub-packages (non-prefixed files)
    "property_generator", "data_loader", "storm_stress", "gauge_generator",
    "property_popup", "claim_report", "visualizer", "naming_conventions",
    "risk_report_generator", "historical_eod", "gaugehd", "propertyts",
}


def pytest_collect_file(parent, file_path):
    """Collect .py files without test_ prefix from all designated subpackages."""
    if (
        file_path.suffix == ".py"
        and not file_path.name.startswith(("_", "conftest", "test_"))
        and file_path.parent.name in _NON_PREFIXED_DIRS
    ):
        return pytest.Module.from_parent(parent, path=file_path)
