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

"""Assemble the BCBS 239 self-assessment LaTeX document (date/data-aware)."""

from datetime import datetime

from ._summary import build_summary
from ._detail import build_principle_sections, build_roadmap_and_appendix


def generate_document(data):
    """Generate the BCBS 239 self-assessment LaTeX document."""
    today = datetime.now().strftime('%d-%B-%Y')
    principles = data.get('principles', [])

    total_score = sum(p['score'] for p in principles)
    total_max = sum(p['max_score'] for p in principles)
    pct = round(total_score / total_max * 100) if total_max > 0 else 0

    categories = [
        ('Governance and Infrastructure', [1, 2]),
        ('Risk Data Aggregation', [3, 4, 5, 6]),
        ('Risk Reporting Practices', [7, 8, 9, 10, 11]),
        ('Supervisory Review', [12, 13, 14]),
    ]

    return (
        build_summary(data, principles, total_score, total_max, pct, categories, today)
        + build_principle_sections(principles, categories)
        + build_roadmap_and_appendix(principles, data, today)
    )
