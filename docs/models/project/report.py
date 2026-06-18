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

"""Plain-text report and entry point for the modularisation reports."""

from datetime import datetime
from pathlib import Path

from ._constants import MIN_LINES, REPO_SCAN_DIRS
from .analysis import analyze_code_files, analyze_repo_files, analyze_init_files
from .pdf import create_pdf_report


def generate_txt_report(scan_root: Path, output_path: Path,
                        min_lines: int = MIN_LINES) -> None:
    """Write a plain-text large-file report for *scan_root* to *output_path*."""
    all_files, large_files = analyze_code_files(scan_root)

    label = scan_root.name  # e.g. "tests"
    lines = [
        f"FILES OVER {min_lines} LINES — {label}/ ({len(all_files)} files)",
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
        f"Sorted by line count descending.  Threshold: > {min_lines} lines.",
        "=" * 80,
        "",
        f"{'LINES':>6}  FILE",
        f"{'-----':>6}  " + "-" * 71,
    ]
    for fi in large_files:
        lines.append(f"{fi.line_count:>6}  {fi.relative_path}")

    if not large_files:
        lines.append(f"  (no files exceed {min_lines} lines)")

    lines += [
        "",
        "=" * 80,
        f"Total: {len(large_files)} file(s) over threshold  |  "
        f"{len(all_files)} total files scanned",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  large_test_report.txt written to {output_path}")


def main():
    """Run both large-file reports and write them to the audit reports directory."""
    from config import config
    # Resolve project root: this file is at docs/models/project/report.py
    here = Path(__file__).resolve().parent          # docs/models/project/
    project_root = here.parent.parent.parent        # project root

    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. PDF report — scope: all non-test source (src/, app/, config/,
    #    tools/, docs/ generators + root-level files), by raw line count.
    # ------------------------------------------------------------------
    src_root = project_root / 'src'
    pdf_output = audit_dir / 'large_file_report.pdf'

    print(f"Scanning {', '.join(REPO_SCAN_DIRS)}/ for large-file PDF report...")
    all_files, large_files = analyze_repo_files(project_root)
    print(f"  {len(all_files)} files scanned, {len(large_files)} exceed {MIN_LINES} lines")

    print("Auditing __init__.py files for substantive code...")
    init_issues = analyze_init_files(src_root)
    print(f"  {len(init_issues)} __init__.py file(s) contain substantive code")

    create_pdf_report(large_files, all_files, pdf_output, project_root,
                      init_issues=init_issues)

    # ------------------------------------------------------------------
    # 2. TXT report — scope: root/tests/
    # ------------------------------------------------------------------
    tests_root = project_root / 'tests'
    txt_output = audit_dir / 'large_test_report.txt'

    print("Scanning tests/ for large-test TXT report...")
    generate_txt_report(tests_root, txt_output)
