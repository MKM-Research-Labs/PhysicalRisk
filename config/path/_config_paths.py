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

"""Path methods for the lightweight Config class."""

import os
from pathlib import Path


class ConfigPaths:
    """Path methods for the simple Config class."""

    def _get_project_root(self) -> Path:
        """Get project root directory."""
        env_root = os.getenv('MKM_PROJECT_ROOT')
        if env_root:
            return Path(env_root)

        current = Path(__file__).resolve().parent.parent.parent  # config/path/ → root
        markers = ['setup.py', 'pyproject.toml', '.git', 'requirements.txt']

        for _ in range(10):
            if any((current / m).exists() for m in markers):
                return current
            if current.parent == current:
                break
            current = current.parent

        return Path(__file__).resolve().parent.parent.parent

    def _get_catchment_input_dir(self) -> Path:
        """Get catchment-specific input directory."""
        catchment = os.getenv('MKM_CATCHMENT', 'thames')
        return self._get_project_root() / os.getenv('MKM_INPUT_DIR', 'data/input') / catchment

    def get_input_dir(self) -> Path:
        """Get input data directory."""
        return self._get_project_root() / os.getenv('MKM_INPUT_DIR', 'data/input')

    def get_output_dir(self) -> Path:
        """Get output directory for UI-generated reports."""
        return self._get_project_root() / os.getenv('MKM_OUTPUT_DIR', 'data/output')

    def get_reports_dir(self, report_type: str = None) -> Path:
        """Get reports directory, optionally for a specific report type."""
        base = self._get_project_root() / 'data' / 'output'
        if report_type:
            return base / report_type
        return base

    def get_property_reports_dir(self) -> Path:
        """Get property reports directory."""
        return self._get_project_root() / 'data' / 'output' / 'property'

    def get_gauge_reports_dir(self) -> Path:
        """Get gauge reports directory."""
        return self._get_project_root() / 'data' / 'output' / 'gauge'

    def get_results_dir(self) -> Path:
        """Get results directory."""
        return self._get_project_root() / 'data' / 'output' / 'results'

    def get_project_root(self) -> Path:
        """Get project root directory (public accessor)."""
        return self._get_project_root()

    def get_catch_dir(self, catchment: str = None) -> Path:
        """Catchment-definition directory (``data/catch`` or ``data/catch/<catchment>``).

        Holds per-catchment definition modules (e.g. ``tc.py``) and snapped-river
        geometry caches — distinct from the per-catchment *input* tree. Without
        ``catchment`` returns the parent ``data/catch``.
        """
        base = self._get_project_root() / 'data' / 'catch'
        return base / catchment if catchment else base

    def get_static_dir(self) -> Path:
        """Static web assets directory (``src/static``) — JS/CSS served by the app."""
        return self._get_project_root() / 'src' / 'static'

    def get_data_dir(self) -> Path:
        """Top-level ``data`` directory (the shared data root containing input/output/catch)."""
        return self._get_project_root() / 'data'
