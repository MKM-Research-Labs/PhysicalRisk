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

"""Standalone database-usage audit report.

Reuses the 4.6 scanner (``docs.models.full_audit.sections_tests.database_usage``)
so the standalone PDF and the consolidated full-audit subsection report identical
numbers. Invoke via ``python -m docs.models.database_usage``."""

from datetime import datetime

from docs.models.full_audit.sections_tests.database_usage import scan_repo
from .pdf import create_pdf_report


def main():
    from config import config
    root = config.get_project_root()

    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    output_path = audit_dir / 'database_usage_report.pdf'

    print('Scanning first-party source for database-seam usage...')
    scan = scan_repo(root)
    print(f"  {scan['scanned']} files scanned")
    print(f"  {len(scan['caller_files'])} module(s) call the database seam "
          f"({len(scan['calls'])} call sites)")
    print(f"  {len(scan['used_funcs'])}/{len(scan['api_names'])} public API "
          f"symbols used ({len(scan['unused_funcs'])} never called)")
    print(f"  {len(scan['json_io_files'])} module(s) still on .json "
          f"(the 4.5 complement); {len(scan['both_files'])} do both")

    generated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    create_pdf_report(scan, output_path, root, generated)
    size_kb = output_path.stat().st_size / 1024
    print(f' Written: {output_path}  ({size_kb:.1f} KB)')
    return output_path
