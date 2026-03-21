# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 10: Document & Report Inventory."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import section_rule, tbl_style


def build_document_inventory(data, story, S):
    story.append(Paragraph("10. Document &amp; Report Inventory", S['h2']))
    section_rule(story)

    files = data['audit_files']
    if not files:
        story.append(Paragraph(
            "No audit reports found. Run test --audit.", S['note']))
        return

    story.append(Paragraph(
        f"{len(files)} files in audit directory:", S['body']))
    story.append(Spacer(1, 0.06 * inch))

    doc_data = [['File', 'Size', 'Last Modified']]
    for f in files:
        doc_data.append([
            f['name'],
            f"{f['size_kb']:.1f} KB",
            f['modified'],
        ])
    tbl = Table(doc_data,
                colWidths=[3.0 * inch, 1.0 * inch, 1.5 * inch])
    tbl.setStyle(tbl_style())
    story.append(tbl)
