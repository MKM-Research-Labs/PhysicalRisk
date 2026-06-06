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
