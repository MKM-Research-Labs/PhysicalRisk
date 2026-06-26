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

"""Entry point: scan first-party source and write the standalone json-file PDF.

Invoke via ``python -m docs.models.json_files``. Reuses the §4.5 scanner so the
standalone report and the consolidated full-audit subsection report identical
numbers."""

from datetime import datetime
from pathlib import Path

from docs.models.full_audit.sections_tests.json_files import scan_repo
from .pdf import create_pdf_report


def main():
    here = Path(__file__).resolve().parent      # docs/models/json_files/
    root = here.parent.parent.parent            # project root

    from config import config
    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'json_files_report.pdf'

    print('Scanning first-party source for .json file I/O...')
    scan = scan_repo(root)
    print(f"  {scan['scanned']} files scanned")
    print(f"  {len(scan['io_files'])} I/O backlog file(s) "
          f"({scan['reads']} load, {scan['writes']} create/update)")
    print(f"  {scan['refs']} bare path reference(s)")

    generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    create_pdf_report(scan, output_path, root, generated)
    size_kb = output_path.stat().st_size / 1024
    print(f' Written: {output_path}  ({size_kb:.1f} KB)')
    return output_path
