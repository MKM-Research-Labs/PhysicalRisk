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

"""Section 8: Test & Sensitivity Evidence."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import AMBER, GREEN, RED, section_rule, tbl_style


def build_test_evidence(data, story, S):
    story.append(Paragraph("8. Test &amp; Sensitivity Evidence", S['h2']))
    section_rule(story)

    junit = data['junit']
    coverage = data.get('coverage_pct')
    models = data['models']
    sens = data['sensitivity_generators']
    doc_completeness = data.get('doc_completeness', [])

    # Test summary
    story.append(Paragraph("Test Suite Results:", S['h3']))
    if junit['total'] > 0:
        test_data = [
            ['Metric', 'Value'],
            ['Total tests', str(junit['total'])],
            ['Passed', str(junit['passed'])],
            ['Failed', str(junit['failed'])],
            ['Errors', str(junit['errors'])],
            ['Skipped', str(junit['skipped'])],
            ['Duration', f"{junit['time_s']:.1f}s"],
        ]
        if coverage:
            test_data.append(['Line coverage', f"{coverage:.1f}%"])
        tbl = Table(test_data, colWidths=[2.0 * inch, 2.0 * inch])
        tbl.setStyle(tbl_style())
        story.append(tbl)
    else:
        story.append(Paragraph(
            "Test results not available. Run test --audit.", S['note']))

    # Per-model test coverage
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Per-Model Test Coverage:", S['h3']))
    tc_data = [['Model', 'Unit', 'Integration', 'Benchmark', 'Test File']]
    for m in models:
        tc = m.get('test_coverage', {})
        if not tc:
            continue
        tc_data.append([
            m.get('model_id', ''),
            '\u2713' if tc.get('unit_tests') else '\u2717',
            '\u2713' if tc.get('integration_tests') else '\u2717',
            '\u2713' if tc.get('benchmark_tests') else '\u2717',
            (tc.get('test_file', '') or '')[-35:],
        ])
    if len(tc_data) > 1:
        tbl = Table(tc_data,
                    colWidths=[0.95 * inch, 0.5 * inch, 0.75 * inch,
                               0.7 * inch, 2.5 * inch])
        ts = tbl_style()
        for ri in range(1, len(tc_data)):
            for ci in range(1, 4):
                cell_val = tc_data[ri][ci]
                col = GREEN if cell_val == '\u2713' else RED
                ts.add('TEXTCOLOR', (ci, ri), (ci, ri), col)
                ts.add('ALIGN', (ci, ri), (ci, ri), 'CENTER')
        tbl.setStyle(ts)
        story.append(tbl)

    # Sensitivity generators
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f"Sensitivity Analysis ({len(sens)} generators):", S['h3']))
    if sens:
        for g in sens:
            story.append(Paragraph(f"&bull; {g}", S['note']))
    else:
        story.append(Paragraph("No sensitivity generators found.", S['note']))

    # Documentation completeness table
    if doc_completeness:
        _build_doc_completeness(doc_completeness, story, S)


def _build_doc_completeness(doc_completeness, story, S):
    """Add documentation completeness matrix and remediation actions."""
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Model Documentation Completeness:", S['h3']))
    story.append(Paragraph(
        "Each model requires core documentation, test results, sensitivity "
        "analysis, and an analysis report under SR 11-7 / SS1/23 governance.",
        S['note']))
    story.append(Spacer(1, 0.06 * inch))

    tick = '\u2713'
    cross = '\u2717'

    headers = ['Model ID', 'Directory', 'Core Doc', 'Test Results',
               'Sensitivity', 'Analysis']
    rows = [headers]
    for d in sorted(doc_completeness, key=lambda x: x['model_id']):
        rows.append([
            d['model_id'],
            d['doc_dir'],
            tick if d['has_core_doc'] else cross,
            tick if d['has_test_results'] else cross,
            tick if d['has_sensitivity'] else cross,
            tick if d['has_analysis'] else cross,
        ])

    tbl = Table(rows, colWidths=[
        0.85 * inch, 1.2 * inch, 0.6 * inch, 0.7 * inch,
        0.7 * inch, 0.6 * inch])
    ts = tbl_style()
    # Colour-code tick/cross cells
    for ri in range(1, len(rows)):
        for ci in range(2, 6):
            val = rows[ri][ci]
            col = GREEN if val == tick else RED
            ts.add('TEXTCOLOR', (ci, ri), (ci, ri), col)
            ts.add('ALIGN', (ci, ri), (ci, ri), 'CENTER')
    tbl.setStyle(ts)
    story.append(tbl)

    # Summary counts
    total = len(doc_completeness)
    has_doc = sum(1 for d in doc_completeness if d['has_core_doc'])
    has_test = sum(1 for d in doc_completeness if d['has_test_results'])
    has_sens = sum(1 for d in doc_completeness if d['has_sensitivity'])
    has_analysis = sum(1 for d in doc_completeness if d['has_analysis'])

    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph(
        f"Coverage: Core docs {has_doc}/{total} "
        f"| Test results {has_test}/{total} "
        f"| Sensitivity {has_sens}/{total} "
        f"| Analysis {has_analysis}/{total}",
        S['body']))

    # Remediation actions for gaps
    actions = _build_remediation_actions(doc_completeness)
    if actions:
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(
            "Documentation Remediation Actions:", S['h3']))
        story.append(Paragraph(
            "The following actions are required to achieve full documentation "
            "coverage across all registered models.", S['note']))
        story.append(Spacer(1, 0.06 * inch))

        action_headers = ['Priority', 'Model ID', 'Gap', 'Required Action']
        action_rows = [action_headers]
        for a in actions:
            action_rows.append([
                a['priority'], a['model_id'], a['gap'], a['action']])

        tbl = Table(action_rows, colWidths=[
            0.5 * inch, 0.85 * inch, 0.9 * inch, 3.4 * inch])
        ts = tbl_style()
        for ri in range(1, len(action_rows)):
            pri = action_rows[ri][0]
            col = RED if pri == 'P1' else AMBER if pri == 'P2' else GREEN
            ts.add('TEXTCOLOR', (0, ri), (0, ri), col)
        tbl.setStyle(ts)
        story.append(tbl)
    else:
        story.append(Spacer(1, 0.08 * inch))
        story.append(Paragraph(
            "All models have complete documentation coverage.", S['body']))


def _build_remediation_actions(doc_completeness):
    """Build prioritised remediation actions for documentation gaps."""
    actions = []
    for d in sorted(doc_completeness, key=lambda x: x['model_id']):
        mid = d['model_id']
        ddir = d['doc_dir']

        if not d['has_core_doc']:
            actions.append({
                'priority': 'P1',
                'model_id': mid,
                'gap': 'Core Doc',
                'action': (f'Generate model documentation: compile '
                           f'docs/models/{ddir}/{ddir}.tex to PDF'),
            })

        if not d['has_test_results']:
            actions.append({
                'priority': 'P2',
                'model_id': mid,
                'gap': 'Test Results',
                'action': 'Run: python app.py check tests --pdf',
            })

        if not d['has_sensitivity']:
            actions.append({
                'priority': 'P2',
                'model_id': mid,
                'gap': 'Sensitivity',
                'action': (f'Create sensitivity generator in '
                           f'docs/models/sensitivities/{ddir}/generator/'),
            })

        if not d['has_analysis']:
            actions.append({
                'priority': 'P3',
                'model_id': mid,
                'gap': 'Analysis',
                'action': ('Run: python -m '
                           'docs.models.sensitivities.generate_all_analysis'),
            })

    return actions
