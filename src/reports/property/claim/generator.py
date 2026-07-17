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

"""ClaimReportGenerator — orchestrates the 5-page PDF claim report."""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, SimpleDocTemplate

from .constants import MARGIN
from .layouts import build_header_footer
from .page1_cover import build_page1_cover
from .page2_chronology import build_page2_chronology
from .page3_damage import build_page3_damage
from .page4_rloan import build_page4_rloan
from .page5_determination import build_page5_determination
from .styles import setup_styles

logger = logging.getLogger(__name__)


class ClaimReportGenerator:
    """
    Generates an in-memory PDF flood damage assessment / insurance claim report.

    Call ``generate(prop_data, prop_record, rloan_record, sequence_lookup)``
    which returns raw PDF bytes.
    """

    def __init__(self):
        self.styles = setup_styles()

    def generate(
        self,
        prop_data: dict,
        prop_record: dict,
        rloan_record: Optional[dict],
        sequence_lookup: Dict[str, dict],
    ) -> bytes:
        """
        Generate a flood damage assessment PDF in memory and return bytes.

        Args:
            prop_data:        Dict from PROP-xxx.json
            prop_record:      Dict from property.json PropertyHeader
            rloan_record:  Dict with Mortgage.FinancialTerms + CurrentStatus, or None
            sequence_lookup:  Dict mapping sequence_id -> {'sequence_type': str}

        Returns:
            Raw PDF bytes.
        """
        prop_id = prop_data.get('property_id', 'UNKNOWN')
        today = datetime.now()
        claim_ref = f"CLM-{prop_id[-8:]}-{today.strftime('%Y%m%d')}"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN + 0.25 * inch,
            bottomMargin=MARGIN,
        )

        hf = build_header_footer(claim_ref)

        story: List = []
        story.extend(build_page1_cover(
            prop_data, prop_record, rloan_record, claim_ref, today, self.styles))
        story.append(PageBreak())

        story.extend(build_page2_chronology(prop_data, sequence_lookup, self.styles))
        story.append(PageBreak())

        story.extend(build_page3_damage(
            prop_data, prop_record, sequence_lookup, self.styles))
        story.append(PageBreak())

        story.extend(build_page4_rloan(
            prop_data, prop_record, rloan_record, sequence_lookup, self.styles))
        story.append(PageBreak())

        story.extend(build_page5_determination(
            prop_data, prop_record, rloan_record, sequence_lookup,
            claim_ref, today, self.styles))

        doc.build(story, onFirstPage=hf, onLaterPages=hf)
        return buf.getvalue()
