# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
