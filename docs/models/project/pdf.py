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

"""PDF rendering for the code-modularisation report."""

import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

from ._constants import CODE_EXTENSIONS, MIN_LINES


def _add_init_audit_section(story, init_issues, styles, heading_style, body_style):
    """Append the __init__.py audit section to the PDF story list."""
    story.append(Paragraph("__init__.py Audit — Substantive Code Detected", heading_style))

    intro = (
        "The following <code>__init__.py</code> files contain function definitions, "
        "class definitions, or route decorators. These should be empty (license header "
        "only) or limited to Blueprint/package setup — substantive code belongs in "
        "dedicated modules.<br/><br/>"
        f"<b>Files with substantive code: {len(init_issues)}</b>"
    )
    story.append(Paragraph(intro, body_style))
    story.append(Spacer(1, 0.15 * inch))

    if not init_issues:
        story.append(Paragraph(
            "<b>All __init__.py files are clean.</b> No substantive code detected.",
            body_style,
        ))
        return

    table_data = [['File', 'Lines', 'Functions', 'Classes', 'Routes', 'Blueprint']]
    for iss in init_issues:
        fn_str = ', '.join(iss.functions) if iss.functions else '—'
        cl_str = ', '.join(iss.classes) if iss.classes else '—'
        table_data.append([
            iss.relative_path,
            str(iss.line_count),
            fn_str,
            cl_str,
            str(iss.routes) if iss.routes else '—',
            'Yes' if iss.has_blueprint else 'No',
        ])

    col_widths = [2.8 * inch, 0.5 * inch, 1.4 * inch, 1.0 * inch, 0.55 * inch, 0.65 * inch]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl_style = TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',         (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN',         (4, 1), (5, -1), 'CENTER'),
        ('WORDWRAP',      (0, 0), (-1, -1), True),
    ])
    # Highlight rows that have routes (most urgent to clean up)
    for row_idx, iss in enumerate(init_issues, start=1):
        if iss.routes:
            tbl_style.add('BACKGROUND', (0, row_idx), (-1, row_idx),
                          colors.HexColor('#fdecea'))
    tbl.setStyle(tbl_style)
    story.append(tbl)
    story.append(Spacer(1, 0.2 * inch))

    # Summary counts
    total_fns = sum(len(i.functions) for i in init_issues)
    total_cls = sum(len(i.classes) for i in init_issues)
    total_routes = sum(i.routes for i in init_issues)
    with_routes = sum(1 for i in init_issues if i.routes)
    story.append(Paragraph(
        f"<b>Summary:</b> {total_fns} function(s), {total_cls} class(es), "
        f"{total_routes} route decorator(s) across {len(init_issues)} file(s). "
        f"{with_routes} file(s) contain route definitions (highlighted in red).",
        body_style,
    ))


def create_pdf_report(large_files, all_files, output_path: Path,
                      root_path: Path, min_lines: int = MIN_LINES,
                      init_issues: list = None):
    """Generate the code-modularisation PDF report."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CTitle', parent=styles['Heading1'],
        fontSize=24, textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30, alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'CHeading', parent=styles['Heading2'],
        fontSize=16, textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12, spaceBefore=12,
    )
    body_style = ParagraphStyle(
        'CBody', parent=styles['BodyText'],
        fontSize=10, leading=14,
    )

    story = []

    story.append(Paragraph("Code Modularisation Analysis", title_style))
    story.append(Spacer(1, 0.2 * inch))

    meta = (
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        f"<b>Project Root:</b> {root_path}<br/>"
        f"<b>Threshold:</b> Files with more than {min_lines} lines<br/>"
        f"<b>File Types Analysed:</b> {', '.join(sorted(CODE_EXTENSIONS))}<br/>"
    )
    story.append(Paragraph(meta, body_style))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Executive Summary", heading_style))

    total_files = len(all_files)
    large_count = len(large_files)
    total_lines = sum(f.line_count for f in all_files)
    large_lines = sum(f.line_count for f in large_files)
    pct = 100 * large_lines / total_lines if total_lines > 0 else 0.0

    summary = (
        f"<b>Total Code Files:</b> {total_files}<br/>"
        f"<b>Total Lines of Code:</b> {total_lines:,}<br/>"
        f"<b>Files Exceeding {min_lines} Lines:</b> {large_count}<br/>"
        f"<b>Lines in Large Files:</b> {large_lines:,} ({pct:.1f}% of total)<br/>"
    )
    if large_count == 0:
        summary += f"<br/><b>Result:</b> No files exceed {min_lines} lines. Project is well-modularised!"
    else:
        summary += f"<br/><b>Recommendation:</b> Consider refactoring the {large_count} file(s) listed below."
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 0.3 * inch))

    if large_count > 0:
        story.append(Paragraph(f"Files Requiring Modularisation (>{min_lines} lines)", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        table_data = [['Rank', 'File Path', 'Type', 'Lines', 'Priority']]
        for idx, fi in enumerate(large_files, 1):
            priority = 'High' if fi.line_count > 1000 else ('Medium' if fi.line_count > 600 else 'Low')
            table_data.append([str(idx), str(fi.relative_path), fi.extension,
                                str(fi.line_count), priority])

        tbl = Table(table_data,
                    colWidths=[0.5 * inch, 3.5 * inch, 0.6 * inch, 0.7 * inch, 0.8 * inch])
        tbl_style = TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR',   (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN',       (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND',  (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR',   (0, 1), (-1, -1), colors.black),
            ('ALIGN',       (0, 1), (0, -1), 'CENTER'),
            ('ALIGN',       (2, 1), (2, -1), 'CENTER'),
            ('ALIGN',       (3, 1), (3, -1), 'RIGHT'),
            ('ALIGN',       (4, 1), (4, -1), 'CENTER'),
            ('FONTNAME',    (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',    (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ])
        for idx, fi in enumerate(large_files, 1):
            if fi.line_count > 1000:
                tbl_style.add('TEXTCOLOR', (4, idx), (4, idx), colors.red)
                tbl_style.add('FONTNAME',  (4, idx), (4, idx), 'Helvetica-Bold')
        tbl.setStyle(tbl_style)
        story.append(tbl)
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("Refactoring Recommendations", heading_style))
        recs = (
            "<b>High Priority (&gt;1000 lines):</b> Immediate refactoring recommended. "
            "These files are doing too much and will benefit from breaking into smaller modules.<br/><br/>"
            "<b>Medium Priority (600–1000 lines):</b> Review for modularisation opportunities. "
            "Look for distinct functional areas that could be separated.<br/><br/>"
            "<b>Low Priority (300–600 lines):</b> Monitor for growth. "
            "Consider refactoring if complexity increases or multiple concerns are mixed.<br/><br/>"
            "<b>General Strategy:</b><br/>"
            "&#8226; Identify distinct responsibilities within each file<br/>"
            "&#8226; Extract cohesive functionality into separate modules<br/>"
            "&#8226; Create clear interfaces between modules<br/>"
            "&#8226; Maintain single responsibility principle<br/>"
            "&#8226; Add tests before and after refactoring"
        )
        story.append(Paragraph(recs, body_style))

    if large_count > 10:
        story.append(PageBreak())
    else:
        story.append(Spacer(1, 0.3 * inch))

    # __init__.py audit section
    if init_issues is not None:
        _add_init_audit_section(story, init_issues, styles, heading_style, body_style)
        story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Complete File Analysis", heading_style))
    by_ext = {}
    for fi in all_files:
        by_ext.setdefault(fi.extension, []).append(fi)

    for ext in sorted(by_ext):
        files = by_ext[ext]
        total = len(files)
        total_ext = sum(f.line_count for f in files)
        avg = total_ext / total if total else 0
        large_c = sum(1 for f in files if f.line_count > min_lines)
        story.append(Paragraph(
            f"<b>{ext} files:</b> {total} files, {total_ext:,} total lines, "
            f"{avg:.0f} avg lines/file, {large_c} file(s) &gt;{min_lines} lines<br/>",
            body_style,
        ))

    doc.build(story)
    print(f"  large_file_report.pdf written to {output_path}")
