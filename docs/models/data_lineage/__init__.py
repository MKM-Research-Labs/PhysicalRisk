# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to
# the terms and conditions of the license agreement provided with this software.

"""
Data Lineage Report — BCBS 239 Data Quality & Provenance Evidence.

Generates a PDF audit report covering BCBS 239 Principles 2, 3, 6 & 7:

  1. Pipeline Topology & Upstream Dependencies  (Principle 2 — Architecture)
  2. Data Quality Metrics                       (Principle 3 — Accuracy)
  3. Data Reconciliation Evidence               (Principle 3 — Integrity)
  4. Content-Hash Freshness / Staleness         (Principle 6 — Timeliness)
  5. Data Source Documentation                  (Principle 7 — Comprehensiveness)
  6. Data Retention Policy                      (Regulatory — FCA/PRA)

Data sources:
  - data/data_lineage.json         — pipeline manifest (SHA-256 hashes)
  - src/lineage/manifest.py        — DEPENDENCY_GRAPH, STEP_IO
  - src/lineage/validation.py      — validate_full_chain()

Output:  data/output/audit/data_lineage_report.pdf

Usage:
    python -m docs.models.data_lineage
"""

from ._constants import (
    NAVY, STEEL, BLUE, GREEN, AMBER, RED, LIGHT_BG, HEADER_BG,
    AUDIT_DIR, OUTPUT_PDF, LINEAGE_PATH,
    STALE_HOURS, RETENTION_DAYS, STEP_OWNERS, FAILURE_METADATA,
)
from .collect import (
    _compute_verdict, _compute_health, _health_colour,
    _load_manifest, _load_lineage_results, collect_all,
)
from .styles import (
    _styles, _header_style, _section_rule, _status_colour, _status_label,
)
from .sections_summary import (
    _build_cover, _build_exec_summary, _build_topology, _build_quality_metrics,
)
from .sections_recon import _build_reconciliation, _build_source_documentation
from .sections_policy import _build_retention_policy, _build_remediation
from .report import create_pdf_report, main

__all__ = [
    'NAVY', 'STEEL', 'BLUE', 'GREEN', 'AMBER', 'RED', 'LIGHT_BG', 'HEADER_BG',
    'AUDIT_DIR', 'OUTPUT_PDF', 'LINEAGE_PATH',
    'STALE_HOURS', 'RETENTION_DAYS', 'STEP_OWNERS', 'FAILURE_METADATA',
    '_compute_verdict', '_compute_health', '_health_colour',
    '_load_manifest', '_load_lineage_results', 'collect_all',
    '_styles', '_header_style', '_section_rule', '_status_colour',
    '_status_label',
    '_build_cover', '_build_exec_summary', '_build_topology',
    '_build_quality_metrics', '_build_reconciliation',
    '_build_source_documentation', '_build_retention_policy',
    '_build_remediation',
    'create_pdf_report', 'main',
]
