# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Shared paths and thresholds for the duplication report generator."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / 'src'))

from config import config

ROOT_DIR = _root
SRC_DIR = ROOT_DIR / 'src'
AUDIT_DIR = config.get_reports_dir('audit')
OUTPUT_PDF = AUDIT_DIR / 'code_duplication_report.pdf'

MIN_LINES = 8
MIN_TOKENS = 50
