# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Gauge Historical Daily CDM package."""

from .directory import main, process_directory  # noqa: F401
from .generator import CDM_AVAILABLE, GaugeHistoricalDaily  # noqa: F401
