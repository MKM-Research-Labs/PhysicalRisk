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

"""Extract assertion expressions from test source files."""

import ast
import os

from config import config

_project_root = config.get_project_root()


def _extract_assertions(file_path, test_class, test_name):
    """Parse a test file and extract assert statements as acceptance criteria."""
    base_name = test_name.split('[')[0]

    try:
        full_path = os.path.join(_project_root, file_path)
        with open(full_path) as f:
            source = f.read()
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    assertions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name != base_name:
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    try:
                        expr = ast.get_source_segment(source, child.test)
                        if expr:
                            assertions.append(expr.strip())
                    except Exception:
                        pass
    return assertions


def build_criteria_cache(results):
    """Build a cache of assertion expressions for all tests."""
    cache = {}
    for r in results:
        key = (r['file'], r['class'], r['name'])
        if key not in cache:
            cache[key] = _extract_assertions(r['file'], r['class'], r['name'])
    return cache
