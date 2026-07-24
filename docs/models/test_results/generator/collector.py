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

"""Pytest plugin that collects structured test results."""

import os

from config import config

from .attribution import model_for_path

_project_root = str(config.get_project_root())


class TestResultCollector:
    """Pytest plugin that collects structured test results."""

    def __init__(self):
        self.results = []

    def pytest_collection_modifyitems(self, items):
        """Cache docstrings and parametrize info at collection time."""
        self._item_info = {}
        for item in items:
            doc = (item.function.__doc__ or '').strip()
            desc_line = doc.split('\n')[0] if doc else ''
            params = ''
            if hasattr(item, 'callspec') and item.callspec.params:
                params = ', '.join(
                    f'{k}={v!r}' for k, v in item.callspec.params.items()
                )
            self._item_info[item.nodeid] = {
                'docstring': doc,
                'description': desc_line,
                'params': params,
            }

    def pytest_runtest_logreport(self, report):
        if report.when == 'call' or (report.when == 'setup' and report.skipped):
            rel_path = report.fspath
            if rel_path.startswith(_project_root):
                rel_path = os.path.relpath(rel_path, _project_root)
            rel_path = rel_path.replace(os.sep, '/')

            parts = report.nodeid.split('::')
            test_class = parts[1] if len(parts) > 2 else ''
            test_name = parts[-1]

            model_id = model_for_path(rel_path)

            info = getattr(self, '_item_info', {}).get(report.nodeid, {})

            result = {
                'nodeid': report.nodeid,
                'file': rel_path,
                'class': test_class,
                'name': test_name,
                'model_id': model_id,
                'outcome': report.outcome,
                'duration': round(report.duration, 4),
                'longrepr': str(report.longrepr) if report.failed else '',
                'description': info.get('description', ''),
                'docstring': info.get('docstring', ''),
                'params': info.get('params', ''),
            }
            self.results.append(result)
