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

import json
import sys
from datetime import datetime
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / 'src'))

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import (
        HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
        TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Colours — consistent with full_audit
# ---------------------------------------------------------------------------

NAVY = colors.HexColor('#1A237E')
STEEL = colors.HexColor('#37474F')
BLUE = colors.HexColor('#1565C0')
GREEN = colors.HexColor('#2E7D32')
AMBER = colors.HexColor('#E65100')
RED = colors.HexColor('#B71C1C')
LIGHT_BG = colors.HexColor('#F5F5F5')
HEADER_BG = colors.HexColor('#E8EAF6')

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

AUDIT_DIR = _root / 'data' / 'output' / 'audit'
OUTPUT_PDF = AUDIT_DIR / 'data_lineage_report.pdf'
LINEAGE_PATH = _root / 'data' / 'data_lineage.json'

# ---------------------------------------------------------------------------
# Staleness threshold — aligned with governance route
# ---------------------------------------------------------------------------

STALE_HOURS = 72   # 3 days
RETENTION_DAYS = 365  # 1 year minimum

# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def _load_manifest() -> dict:
    if LINEAGE_PATH.exists():
        try:
            with open(LINEAGE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"runs": {}, "steps": {}}


def _load_lineage_results() -> dict:
    """Load data_lineage_results.json from audit dir (produced by test run)."""
    p = AUDIT_DIR / 'data_lineage_results.json'
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def collect_all() -> dict:
    """Collect all lineage data for the report."""
    # Import the lineage modules
    try:
        from lineage.manifest import DEPENDENCY_GRAPH, STEP_IO
        from lineage.validation import validate_full_chain
    except ImportError:
        # Fallback — define locally
        DEPENDENCY_GRAPH = {}
        STEP_IO = {}
        validate_full_chain = lambda: {
            "is_consistent": False,
            "stale_steps": [],
            "missing_steps": list(DEPENDENCY_GRAPH.keys()),
            "details": {},
        }

    manifest = _load_manifest()
    steps = manifest.get("steps", {})
    runs = manifest.get("runs", {})

    # Validation
    try:
        chain_result = validate_full_chain()
    except Exception:
        chain_result = {
            "is_consistent": False,
            "stale_steps": [],
            "missing_steps": list(DEPENDENCY_GRAPH.keys()),
            "details": {"error": ["Validation could not be run"]},
        }

    # Consistency test results
    lineage_results = _load_lineage_results()

    # Per-step freshness from manifest timestamps
    step_details = []
    for step_name in DEPENDENCY_GRAPH:
        entry = steps.get(step_name, {})
        deps = DEPENDENCY_GRAPH.get(step_name, [])
        io = STEP_IO.get(step_name, {})
        is_stale = step_name in chain_result.get("stale_steps", [])
        is_missing = step_name in chain_result.get("missing_steps", [])

        step_details.append({
            "step": step_name,
            "dependencies": deps,
            "inputs": io.get("inputs", []),
            "outputs": io.get("outputs", []),
            "generator": entry.get("generator", ""),
            "run_id": entry.get("run_id", ""),
            "timestamp": entry.get("timestamp", ""),
            "elapsed_s": entry.get("elapsed_seconds", 0),
            "status": "missing" if is_missing else ("stale" if is_stale else "fresh"),
            "hash_status": entry.get("status", ""),
            "parameters": entry.get("parameters", {}),
            "input_hashes": entry.get("inputs", {}),
            "output_hashes": entry.get("outputs", {}),
        })

    return {
        "manifest": manifest,
        "graph": DEPENDENCY_GRAPH,
        "step_io": STEP_IO,
        "chain_result": chain_result,
        "lineage_results": lineage_results,
        "step_details": step_details,
        "num_runs": len(runs),
        "num_steps": len(DEPENDENCY_GRAPH),
        "num_recorded": len(steps),
    }


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('DLTitle', parent=base['Heading1'],
                                fontSize=22, textColor=NAVY,
                                spaceAfter=8, alignment=TA_CENTER,
                                fontName='Helvetica-Bold'),
        'subtitle': ParagraphStyle('DLSub', parent=base['Normal'],
                                   fontSize=12, textColor=STEEL,
                                   spaceAfter=4, alignment=TA_CENTER),
        'meta': ParagraphStyle('DLMeta', parent=base['Normal'],
                               fontSize=9, textColor=colors.HexColor('#546E7A'),
                               alignment=TA_CENTER, spaceAfter=2),
        'h2': ParagraphStyle('DLH2', parent=base['Heading2'],
                              fontSize=14, textColor=NAVY,
                              spaceBefore=14, spaceAfter=6,
                              fontName='Helvetica-Bold'),
        'h3': ParagraphStyle('DLH3', parent=base['Heading3'],
                              fontSize=11, textColor=STEEL,
                              spaceBefore=8, spaceAfter=4,
                              fontName='Helvetica-Bold'),
        'body': ParagraphStyle('DLBody', parent=base['BodyText'],
                               fontSize=9, leading=13),
        'small': ParagraphStyle('DLSmall', parent=base['Normal'],
                                fontSize=7.5, textColor=colors.HexColor('#78909C'),
                                leading=11),
        'code': ParagraphStyle('DLCode', parent=base['Code'],
                               fontSize=8, leading=11,
                               textColor=colors.HexColor('#333333')),
        'note': ParagraphStyle('DLNote', parent=base['BodyText'],
                               fontSize=8, leading=11,
                               textColor=colors.HexColor('#666666'),
                               leftIndent=12),
    }


def _header_style():
    return TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',      (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, 0), 8.5),
        ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING',  (0, 0), (-1, 0), 8),
        ('BACKGROUND',     (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f4f6f9')]),
        ('FONTNAME',       (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 1), (-1, -1), 8),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('TOPPADDING',     (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING',  (0, 1), (-1, -1), 4),
    ])


def _section_rule(story):
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=1,
                             color=colors.HexColor('#bdc3c7')))
    story.append(Spacer(1, 0.1 * inch))


def _status_colour(status: str):
    return {'fresh': GREEN, 'stale': AMBER, 'missing': RED}.get(status, STEEL)


def _status_label(status: str) -> str:
    return {'fresh': 'FRESH', 'stale': 'STALE', 'missing': 'MISSING'}.get(
        status, status.upper())


# ---------------------------------------------------------------------------
# PDF sections
# ---------------------------------------------------------------------------

def _build_cover(data: dict, story: list, S: dict):
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Data Lineage Report", S['title']))
    story.append(Paragraph(
        "BCBS 239 — Data Quality, Reconciliation & Provenance",
        S['subtitle']))
    story.append(Spacer(1, 0.3 * inch))

    chain = data['chain_result']
    health = 'CONSISTENT' if chain['is_consistent'] else 'ACTION REQUIRED'
    health_col = GREEN if chain['is_consistent'] else RED

    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        S['meta']))
    story.append(Paragraph(
        f"<b>Pipeline Steps:</b> {data['num_steps']} | "
        f"<b>Recorded:</b> {data['num_recorded']} | "
        f"<b>Runs:</b> {data['num_runs']}",
        S['meta']))
    story.append(Spacer(1, 0.15 * inch))

    # Overall health badge
    badge_data = [['Pipeline Health'],
                  [health]]
    badge = Table(badge_data, colWidths=[3 * inch])
    badge.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (0, 0), 10),
        ('FONTSIZE',      (0, 1), (0, 1), 16),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR',     (0, 1), (0, 1), health_col),
        ('BACKGROUND',    (0, 1), (0, 1), colors.HexColor('#FAFAFA')),
        ('BOX',           (0, 0), (-1, -1), 1, NAVY),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(badge)

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "<i>This report provides evidence for BCBS 239 compliance covering "
        "data quality metrics, reconciliation procedures, upstream source "
        "documentation, and data retention policy.</i>",
        S['note']))


def _build_exec_summary(data: dict, story: list, S: dict):
    """Section 1: Executive Summary."""
    story.append(Paragraph("1. Executive Summary", S['h2']))
    _section_rule(story)

    chain = data['chain_result']
    steps = data['step_details']
    fresh = sum(1 for s in steps if s['status'] == 'fresh')
    stale = sum(1 for s in steps if s['status'] == 'stale')
    missing = sum(1 for s in steps if s['status'] == 'missing')

    # Consistency test results
    lr = data['lineage_results']
    tests_total = lr.get('total', 0)
    tests_passed = lr.get('passed', 0)
    tests_failed = lr.get('failed', 0)

    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Pipeline steps', str(data['num_steps']),
         'INFO'],
        ['Steps recorded in manifest', str(data['num_recorded']),
         'PASS' if data['num_recorded'] == data['num_steps'] else 'GAPS'],
        ['Steps with fresh data', str(fresh),
         'PASS' if fresh == data['num_steps'] else 'REVIEW'],
        ['Steps with stale data', str(stale),
         'PASS' if stale == 0 else 'WARNING'],
        ['Steps with missing data', str(missing),
         'PASS' if missing == 0 else 'FAIL'],
        ['Hash-chain consistency',
         'Consistent' if chain['is_consistent'] else 'Broken',
         'PASS' if chain['is_consistent'] else 'FAIL'],
        ['ID consistency tests', f"{tests_passed}/{tests_total}",
         'PASS' if tests_failed == 0 and tests_total > 0 else (
             'FAIL' if tests_failed > 0 else 'NOT RUN')],
    ]

    tbl = Table(summary_data,
                colWidths=[3.0 * inch, 1.5 * inch, 1.5 * inch])
    ts = _header_style()
    for row_idx, row in enumerate(summary_data[1:], 1):
        status = row[2]
        col = (GREEN if status == 'PASS' else
               AMBER if status in ('WARNING', 'REVIEW', 'GAPS') else
               RED if status == 'FAIL' else STEEL)
        ts.add('TEXTCOLOR', (2, row_idx), (2, row_idx), col)
        ts.add('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "This report addresses the following BCBS 239 requirements:<br/>"
        "&bull; <b>Principle 2</b> — Data Architecture & Infrastructure<br/>"
        "&bull; <b>Principle 3</b> — Accuracy & Integrity (quality metrics, "
        "reconciliation)<br/>"
        "&bull; <b>Principle 6</b> — Timeliness (staleness monitoring)<br/>"
        "&bull; <b>Principle 7</b> — Comprehensiveness (source documentation)",
        S['body']))


def _build_topology(data: dict, story: list, S: dict):
    """Section 2: Pipeline Topology & Upstream Dependencies."""
    story.append(Paragraph(
        "2. Pipeline Topology &amp; Upstream Dependencies", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "The portfolio generation pipeline consists of "
        f"{data['num_steps']} steps with defined dependency ordering. "
        "Each step declares its inputs and outputs; the lineage system "
        "tracks content hashes (SHA-256) at each boundary to detect "
        "staleness.<br/><br/>"
        "<b>BCBS 239 Principle 2:</b> Data architecture is documented with "
        "clear ownership of each pipeline stage and its data artefacts.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Dependency table
    topo_data = [['Step', 'Depends On', 'Inputs', 'Outputs']]
    for sd in data['step_details']:
        deps = ', '.join(sd['dependencies']) if sd['dependencies'] else '(root)'
        inputs = ', '.join(sd['inputs']) if sd['inputs'] else '(none)'
        outputs = ', '.join(sd['outputs']) if sd['outputs'] else '(none)'
        topo_data.append([sd['step'], deps, inputs, outputs])

    tbl = Table(topo_data,
                colWidths=[1.3 * inch, 1.5 * inch, 1.8 * inch, 1.9 * inch])
    tbl.setStyle(_header_style())
    story.append(tbl)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Data Source Documentation:</b> All upstream dependencies are "
        "explicitly declared in <i>src/lineage/manifest.py</i> via the "
        "<i>DEPENDENCY_GRAPH</i> and <i>STEP_IO</i> constants. Each step's "
        "generator function, input files, and output artefacts are registered "
        "at code level and verified at runtime via SHA-256 content hashing.",
        S['body']))


def _build_quality_metrics(data: dict, story: list, S: dict):
    """Section 3: Data Quality Metrics (BCBS 239 P3)."""
    story.append(Paragraph("3. Data Quality Metrics", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>BCBS 239 Principle 3 — Accuracy &amp; Integrity:</b> "
        "Data quality is monitored through three complementary mechanisms:"
        "<br/><br/>"
        "<b>a) Content-hash verification:</b> Every pipeline step records "
        "SHA-256 hashes of its inputs and outputs. Downstream consumers "
        "compare their input hashes against the upstream producer's output "
        "hash to detect drift.<br/><br/>"
        "<b>b) Cross-file ID consistency:</b> Automated tests verify that "
        "gauge IDs, property IDs, storm IDs, and trade references are "
        "consistent across all data files in the pipeline.<br/><br/>"
        "<b>c) Staleness monitoring:</b> A 72-hour staleness threshold "
        "flags data that has not been refreshed, with live health checks "
        "available via the governance API.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Per-step quality table
    quality_data = [['Step', 'Last Run', 'Elapsed', 'Hash Status',
                     'Freshness']]
    for sd in data['step_details']:
        ts = sd['timestamp']
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                ts_display = dt.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                ts_display = ts[:16]
        else:
            ts_display = '\u2014'

        elapsed = f"{sd['elapsed_s']:.1f}s" if sd['elapsed_s'] else '\u2014'
        h_status = sd['hash_status'].upper() if sd['hash_status'] else '\u2014'
        freshness = _status_label(sd['status'])

        quality_data.append([sd['step'], ts_display, elapsed,
                             h_status, freshness])

    tbl = Table(quality_data,
                colWidths=[1.3 * inch, 1.5 * inch, 0.8 * inch,
                           1.3 * inch, 1.3 * inch])
    ts = _header_style()
    for row_idx, sd in enumerate(data['step_details'], 1):
        col = _status_colour(sd['status'])
        ts.add('TEXTCOLOR', (4, row_idx), (4, row_idx), col)
        ts.add('FONTNAME', (4, row_idx), (4, row_idx), 'Helvetica-Bold')
        # Highlight hash status
        if sd['hash_status'] == 'success':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), GREEN)
        elif sd['hash_status']:
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), RED)
    tbl.setStyle(ts)
    story.append(tbl)

    # Stale step details
    chain = data['chain_result']
    if chain.get('details'):
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Staleness Details:", S['h3']))
        for step_name, issues in chain['details'].items():
            for issue in issues:
                story.append(Paragraph(
                    f"&bull; <b>{step_name}:</b> {issue}", S['note']))


def _build_reconciliation(data: dict, story: list, S: dict):
    """Section 4: Data Reconciliation Evidence (BCBS 239 P3)."""
    story.append(Paragraph("4. Data Reconciliation Procedures", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>BCBS 239 Principle 3 — Reconciliation:</b> "
        "The platform implements automated reconciliation between all "
        "pipeline data files. These checks run as part of the test suite "
        "and as a pre-flight gate before the audit package is generated."
        "<br/><br/>"
        "Reconciliation procedures are defined in "
        "<i>tests/data/test_id_consistency.py</i> and cover:",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Reconciliation checks documented
    recon_checks = [
        ['Check', 'Files Reconciled', 'Validation Rule'],
        ['Gauge ID consistency',
         'gauge.json \u2194 gaugehc.json',
         'Every gauge in gauge.json has a matching hazard curve; '
         'no orphan IDs in gaugehc.json'],
        ['Trade gauge references',
         'prs/*.json \u2194 gauge.json',
         'Every traded gauge_id exists in the gauge master file'],
        ['Trade hazard curves',
         'prs/*.json \u2194 gaugehc.json',
         'Every traded gauge_id has an associated hazard curve'],
        ['Property ID consistency',
         'property.json \u2194 propertyts/',
         'Property time-series files reference valid property IDs'],
        ['Storm ID consistency',
         'storm_sequences.json \u2194 gaugets/ \u2194 propertyts/',
         'All storm IDs in time-series originate from storm sequences'],
        ['Classifier gauge alignment',
         'GAUGE-*.joblib \u2194 gauge.json',
         'Classifier model files reference current gauge IDs'],
        ['Manifest hash verification',
         'data_lineage.json \u2194 filesystem',
         'Recorded output hashes match current file content on disk'],
        ['Dependency chain integrity',
         'data_lineage.json (all steps)',
         'No step has stale inputs; all upstream steps are recorded'],
        ['Deterministic IDs',
         'gauge.json',
         'Gauge IDs are derived from location, not randomly generated'],
    ]

    tbl = Table(recon_checks,
                colWidths=[1.6 * inch, 1.6 * inch, 3.3 * inch])
    tbl.setStyle(_header_style())
    story.append(tbl)

    # Test results
    lr = data['lineage_results']
    if lr:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Latest Reconciliation Results:", S['h3']))
        total = lr.get('total', 0)
        passed = lr.get('passed', 0)
        failed = lr.get('failed', 0)
        skipped = lr.get('skipped', 0)

        result_data = [
            ['Total Checks', 'Passed', 'Failed', 'Skipped', 'Verdict'],
            [str(total), str(passed), str(failed), str(skipped),
             'PASS' if failed == 0 else 'FAIL'],
        ]
        rtbl = Table(result_data,
                     colWidths=[1.2 * inch, 1.2 * inch, 1.2 * inch,
                                1.2 * inch, 1.2 * inch])
        rts = _header_style()
        verdict_col = GREEN if failed == 0 else RED
        rts.add('TEXTCOLOR', (4, 1), (4, 1), verdict_col)
        rts.add('FONTNAME', (4, 1), (4, 1), 'Helvetica-Bold')
        if failed > 0:
            rts.add('TEXTCOLOR', (2, 1), (2, 1), RED)
            rts.add('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold')
        rtbl.setStyle(rts)
        story.append(rtbl)

        # Show failures if any
        failures = lr.get('failures', [])
        if failures:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("Failed Checks:", S['h3']))
            for f in failures[:15]:
                name = f.get('name', 'unknown')
                msg = f.get('message', '')
                if len(msg) > 150:
                    msg = msg[:150] + '...'
                story.append(Paragraph(
                    f"&bull; <b>{name}:</b> {msg}", S['note']))
    else:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            "<i>Reconciliation test results not available. "
            "Run <b>python app.py test --audit</b> to generate.</i>",
            S['note']))


def _build_source_documentation(data: dict, story: list, S: dict):
    """Section 5: Data Source Documentation."""
    story.append(Paragraph("5. Data Source Documentation", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>BCBS 239 Principle 7 — Comprehensiveness:</b> "
        "Each pipeline step's data sources, generator module, and "
        "parameterisation are documented below. This provides a complete "
        "audit trail of upstream dependencies for every data artefact "
        "in the portfolio risk system.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    for sd in data['step_details']:
        story.append(Paragraph(
            f"<b>{sd['step']}</b>", S['h3']))

        gen = sd['generator'] or '(not yet recorded)'
        run_id = sd['run_id'] or '\u2014'
        ts = sd['timestamp']
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        else:
            ts = '\u2014'

        info_data = [
            ['Property', 'Value'],
            ['Generator', gen],
            ['Last run ID', run_id],
            ['Last executed', ts],
            ['Dependencies',
             ', '.join(sd['dependencies']) if sd['dependencies'] else '(root — no upstream)'],
            ['Input files', ', '.join(sd['inputs']) if sd['inputs'] else '(none)'],
            ['Output files', ', '.join(sd['outputs']) if sd['outputs'] else '(none)'],
            ['Freshness', _status_label(sd['status'])],
        ]

        # Add parameters if recorded
        params = sd.get('parameters', {})
        if params:
            param_str = '; '.join(f"{k}={v}" for k, v in
                                  sorted(params.items())[:8])
            if len(params) > 8:
                param_str += f' ... (+{len(params) - 8} more)'
            info_data.append(['Parameters', param_str])

        tbl = Table(info_data, colWidths=[1.5 * inch, 5.0 * inch])
        ts_style = _header_style()
        # Colour freshness row
        freshness_row = len(info_data) - (2 if params else 1)
        col = _status_colour(sd['status'])
        ts_style.add('TEXTCOLOR', (1, freshness_row), (1, freshness_row), col)
        ts_style.add('FONTNAME', (1, freshness_row), (1, freshness_row),
                     'Helvetica-Bold')
        tbl.setStyle(ts_style)
        story.append(tbl)
        story.append(Spacer(1, 0.08 * inch))


def _build_retention_policy(data: dict, story: list, S: dict):
    """Section 6: Data Retention Policy."""
    story.append(Paragraph("6. Data Retention Policy", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>Regulatory Requirement (FCA/PRA):</b> "
        "Data used in risk model calibration and pricing must be retained "
        "for a minimum period to support audit, backtesting, and regulatory "
        "review. The following policy applies to all data artefacts "
        "in the Physical Risk portfolio system.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    policy_data = [
        ['Data Category', 'Retention Period', 'Storage', 'Policy Basis'],
        ['Pipeline source data\n(gauge, property, mortgage)',
         f'{RETENTION_DAYS} days\n(minimum)',
         'data/input/<catchment>/',
         'FCA SYSC 9 — adequate records'],
        ['Model calibration outputs\n(hazard curves, stress models)',
         f'{RETENTION_DAYS} days\n(minimum)',
         'data/input/<catchment>/',
         'SS1/23 §5.7 — model outputs'],
        ['Trade blotter & PRS\n(pricing, counterparty data)',
         '5 years\n(minimum)',
         'data/input/<catchment>/prs/',
         'FCA COBS 9A — suitability records'],
        ['EOD snapshots\n(daily P&L, market state)',
         '5 years\n(minimum)',
         'data/output/trading/eod/',
         'FCA SUP 17 — transaction reporting'],
        ['Lineage manifest\n(data_lineage.json)',
         f'{RETENTION_DAYS} days\n(minimum)',
         'data/',
         'BCBS 239 P6 — timeliness evidence'],
        ['Audit evidence\n(test reports, coverage)',
         '3 years\n(minimum)',
         'data/output/audit/',
         'SS1/23 §5.14 — validation evidence'],
        ['Classifier models\n(*.joblib, training summaries)',
         'Model lifetime\n+ 1 year',
         'data/output/gauge/',
         'SR 11-7 — model inventory'],
    ]

    tbl = Table(policy_data,
                colWidths=[1.7 * inch, 1.2 * inch, 1.7 * inch, 1.9 * inch])
    tbl.setStyle(_header_style())
    story.append(tbl)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Implementation Notes:</b>", S['h3']))
    story.append(Paragraph(
        "&bull; The lineage manifest records SHA-256 hashes and timestamps "
        "for every pipeline execution, providing immutable evidence of "
        "data provenance.<br/>"
        "&bull; EOD snapshots include a full market state snapshot "
        "(hazard term structures, yield curve, gauge adjustments) enabling "
        "point-in-time reconstruction of risk calculations.<br/>"
        "&bull; The <i>--strict</i> CLI flag refuses pipeline execution if "
        "upstream data is stale, enforcing the staleness threshold of "
        f"{STALE_HOURS} hours.<br/>"
        "&bull; All data files use JSON format with structured schemas "
        "(CDM layer), enabling automated validation and migration.",
        S['body']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Archival Procedure:</b> Pipeline data older than the retention "
        "period should be archived to a separate read-only store. The "
        "lineage manifest preserves the SHA-256 hash of archived data, "
        "enabling integrity verification on retrieval. Archival is currently "
        "a manual process; automated archival with configurable retention "
        "windows is on the development roadmap.",
        S['body']))


def _build_remediation(data: dict, story: list, S: dict):
    """Section 7: Remediation Guidance."""
    story.append(Paragraph("7. Remediation Guidance", S['h2']))
    _section_rule(story)

    chain = data['chain_result']

    if chain['is_consistent'] and not chain.get('missing_steps'):
        story.append(Paragraph(
            "<b>RESULT: COMPLIANT.</b> All pipeline steps are recorded, "
            "content hashes are consistent, and no stale data detected. "
            "No remediation required.",
            S['body']))
        return

    story.append(Paragraph(
        "The following remediation steps are recommended:", S['body']))
    story.append(Spacer(1, 0.08 * inch))

    steps = []
    if chain.get('missing_steps'):
        steps.append(
            f"<b>Missing steps ({len(chain['missing_steps'])}):</b> "
            f"Run the pipeline for: {', '.join(chain['missing_steps'])}. "
            f"Use <i>python app.py port</i> with the appropriate flags.")

    if chain.get('stale_steps'):
        steps.append(
            f"<b>Stale data ({len(chain['stale_steps'])}):</b> "
            f"Regenerate: {', '.join(chain['stale_steps'])}. "
            f"Upstream inputs have changed since these steps were last run. "
            f"Use <i>python app.py port --strict</i> to enforce freshness.")

    if chain.get('details'):
        for step_name, issues in chain['details'].items():
            for issue in issues:
                steps.append(f"<b>{step_name}:</b> {issue}")

    steps.append(
        "<b>Verify fix:</b> Run <i>python app.py test --audit</i> to "
        "regenerate this report and confirm all checks pass.")

    for step in steps:
        story.append(Paragraph(f"&bull; {step}", S['body']))
        story.append(Spacer(1, 0.06 * inch))


# ---------------------------------------------------------------------------
# PDF assembly
# ---------------------------------------------------------------------------

def create_pdf_report(data: dict = None) -> Path:
    """Build the full data lineage report PDF."""
    if data is None:
        data = collect_all()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.6 * inch,
    )
    S = _styles()
    story = []

    # Cover
    _build_cover(data, story, S)
    story.append(PageBreak())

    # 1. Executive Summary
    _build_exec_summary(data, story, S)
    story.append(PageBreak())

    # 2. Pipeline Topology & Upstream Dependencies
    _build_topology(data, story, S)
    story.append(PageBreak())

    # 3. Data Quality Metrics
    _build_quality_metrics(data, story, S)
    story.append(PageBreak())

    # 4. Data Reconciliation Procedures
    _build_reconciliation(data, story, S)
    story.append(PageBreak())

    # 5. Data Source Documentation
    _build_source_documentation(data, story, S)
    story.append(PageBreak())

    # 6. Data Retention Policy
    _build_retention_policy(data, story, S)
    story.append(PageBreak())

    # 7. Remediation
    _build_remediation(data, story, S)

    # Footer
    _section_rule(story)
    story.append(Paragraph(
        f"<i>Report generated by docs.models.data_lineage — "
        f"MKM Research Labs Physical Risk Platform</i>",
        S['small']))

    doc.build(story)
    return OUTPUT_PDF


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("Generating Data Lineage Report (BCBS 239)...")
    data = collect_all()
    print(f"  {data['num_steps']} pipeline steps, "
          f"{data['num_recorded']} recorded")
    chain = data['chain_result']
    print(f"  Consistency: "
          f"{'OK' if chain['is_consistent'] else 'ISSUES FOUND'}")
    if chain.get('stale_steps'):
        print(f"  Stale steps: {', '.join(chain['stale_steps'])}")
    if chain.get('missing_steps'):
        print(f"  Missing steps: {', '.join(chain['missing_steps'])}")

    out = create_pdf_report(data)
    size_kb = out.stat().st_size / 1024
    print(f"  data_lineage_report.pdf written to {out}  ({size_kb:.1f} KB)")
