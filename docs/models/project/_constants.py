# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
