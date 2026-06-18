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
