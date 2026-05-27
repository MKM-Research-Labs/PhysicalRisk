# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared section renderers for asset reports.

The asset CDM (src/port/cdm/asset/) splits asset records into three
buckets: sections shared by all asset types (Header, Valuation,
Construction, Location, RiskAssessment, EnergyPerformance,
ProtectionMeasures, HistoryAndIncidents, TransactionHistory),
residential-only sections (PropertyAttributes, Contents), and
commercial-only sections (CommercialAttributes, AccessibilityFeatures,
Tenancy).

This package mirrors the *shared* leg: one ``render_<section>``
function per shared section, taking a section dict + a page-style
context and returning ReportLab flowables. Each render function is
catchment- and asset-type-agnostic — the caller (property or
commercial report generator) is responsible for unwrapping the right
CDM path before calling.
"""

from .base import AssetBasePage
from .construction import render_construction
from .energy import render_energy
from .header import render_header
from .history import render_history
from .location import render_location
from .protection import render_protection
from .risk_assessment import render_risk_assessment
from .transactions import render_transactions
from .valuation import render_valuation

__all__ = [
    "AssetBasePage",
    "render_construction",
    "render_energy",
    "render_header",
    "render_history",
    "render_location",
    "render_protection",
    "render_risk_assessment",
    "render_transactions",
    "render_valuation",
]
