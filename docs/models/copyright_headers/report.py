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

"""Entry point: audit copyright headers across all source, fix and report.

Running ``python -m docs.models.copyright_headers`` rewrites any non-compliant
header in place and writes ``copyright_headers_report.pdf`` (plus a JSON record)
to the audit reports directory.

A small JSON record is merged across invocations so the report still lists the
files whose headers were corrected even when the actual rewrite happened in an
earlier phase of the same ``app.py test`` run (the pytest self-heal repairs the
tree during the unit phase, before this report generator runs).
"""

import json
from pathlib import Path

from .scanners import fix_repo
from .pdf import create_pdf_report


def _merge_record(record_path: Path, findings: dict) -> dict:
    """Union this run's fixes with any previously recorded ones, persist, and
    return the merged findings used to build the PDF."""
    prior = {}
    if record_path.exists():
        try:
            data = json.loads(record_path.read_text(encoding='utf-8'))
            for rec in data.get('fixed', []):
                prior[rec['file']] = rec
        except (ValueError, OSError):
            prior = {}
    for rec in findings['fixed']:
        prior[rec['file']] = rec

    merged = dict(findings)
    merged['fixed'] = sorted(prior.values(), key=lambda r: r['file'])
    try:
        record_path.write_text(json.dumps(merged, indent=2), encoding='utf-8')
    except OSError:
        pass
    return merged


def main():
    here = Path(__file__).resolve().parent          # docs/models/copyright_headers/
    root = here.parent.parent.parent                # project root

    from config import config
    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    record_path = audit_dir / 'copyright_headers_record.json'
    output_path = audit_dir / 'copyright_headers_report.pdf'

    print("Auditing copyright headers across all .py and .js source...")
    findings = fix_repo(root, apply=True)
    merged = _merge_record(record_path, findings)

    print(f"  {findings['scanned']} files scanned")
    print(f"  {findings['already_compliant']} already compliant")
    print(f"  {len(findings['fixed'])} header(s) replaced this run "
          f"({len(merged['fixed'])} total on record)")
    if findings['remaining']:
        print(f"  WARNING: {len(findings['remaining'])} still non-compliant")

    create_pdf_report(merged, output_path, root)
