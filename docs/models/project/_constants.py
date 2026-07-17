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

"""Shared constants and record types for the modularisation reports."""

from collections import namedtuple

CODE_EXTENSIONS = {'.py', '.js', '.css'}

EXCLUDED_FOLDERS = {
    'project',
    '.git',
    '.claude',
    '__pycache__',
    'node_modules',
    '.venv',
    'venv',
    'docs',
    'data',
    'dist',
    'build',
    '.pytest_cache',
    '.mypy_cache',
}

MIN_LINES = 300

# Top-level directories scanned by the repo-wide modularisation report.
# Scope: all non-test source. Tests get their own plain-text report and are
# excluded from the >300-line refactor initiative.
REPO_SCAN_DIRS = ('src', 'app', 'config', 'tools', 'docs')

# Folders pruned during the repo-wide scan. Unlike EXCLUDED_FOLDERS this keeps
# 'docs'/'project' in scope (the report generators are non-test code too) but
# adds 'tests' so the test suite is not double-counted here.
REPO_SCAN_EXCLUDE = {
    '.git',
    '.claude',
    '__pycache__',
    'node_modules',
    '.venv',
    'venv',
    'data',
    'dist',
    'build',
    '.pytest_cache',
    '.mypy_cache',
    'tests',
}

FileInfo = namedtuple('FileInfo', ['path', 'relative_path', 'extension', 'line_count'])

# Findings from the __init__.py audit
InitIssue = namedtuple('InitIssue', [
    'relative_path',   # relative path string
    'line_count',      # total non-empty lines
    'functions',       # list of function names defined at module level
    'classes',         # list of class names defined at module level
    'routes',          # count of @bp.route / @app.route decorators
    'has_blueprint',   # True if Blueprint(...) assigned in this file
])
