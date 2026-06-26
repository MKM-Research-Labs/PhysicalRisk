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

"""Dependency check, coverage parsing and audit-report doc generators."""

import os
import sys
import shutil
import subprocess as sp


def _check_deps():
    """Verify required Python dependencies are installed."""
    required = [
        "flask", "flask_cors", "folium", "pandas", "numpy",
        "geopandas", "reportlab", "scipy", "sklearn",
        "rasterio", "geopy", "shapely", "matplotlib", "seaborn"
    ]

    print("Checking Python dependencies...")
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ✗ {package}")

    if missing:
        print(f"\nMissing packages: {missing}")
        print(f"Install with: pip install {' '.join(missing)}")
        return 1
    print("\n✓ All dependencies satisfied")
    return 0


def _parse_coverage_pct(cov_xml: str):
    """Return line coverage as a percentage from a coverage.xml, or None."""
    if not os.path.exists(cov_xml):
        return None
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(cov_xml).getroot()
        return float(root.get('line-rate', 0)) * 100
    except Exception:
        return None


def _run_audit_reports(project_root, audit_dir, python_exe, coverage_pct,
                       git_sha, do_pdf):
    """Phase 4: generate the audit doc artefacts — LaTeX/PDF model docs plus
    the modularisation, duplication, hard-coding, lineage and full-audit
    reports. ``python_exe`` (the venv Python) runs the model-doc generator;
    the code analyses run under ``sys.executable``, matching the original."""
    # If unit tests weren't run this time, fall back to an existing coverage xml.
    if coverage_pct is None:
        coverage_pct = _parse_coverage_pct(os.path.join(audit_dir, 'coverage.xml'))
        if coverage_pct is not None:
            print(f' Coverage (from existing xml): {coverage_pct:.1f}%')

    # 4a. Model test documentation (LaTeX)
    print('\nGenerating model documentation...')
    doc_cmd = [python_exe, '-m', 'docs.models.test_results.generator']
    if do_pdf:
        doc_cmd.append('--pdf')
    if git_sha:
        doc_cmd.extend(['--git-sha', git_sha])
    if coverage_pct is not None:
        doc_cmd.extend(['--coverage-pct', f'{coverage_pct:.2f}'])
    e2e_xml = os.path.join(audit_dir, 'e2e', 'e2e_junit.xml')
    if os.path.exists(e2e_xml):
        doc_cmd.extend(['--e2e-junit', e2e_xml])
    sp.run(doc_cmd, cwd=str(project_root))

    # Copy generated PDF into audit directory
    _test_report_pdf = os.path.join(
        str(project_root),
        'docs', 'models', 'test_results', 'test_results', 'test_report.pdf')
    if os.path.exists(_test_report_pdf):
        dest = os.path.join(audit_dir, 'test_report.pdf')
        shutil.copy2(_test_report_pdf, dest)
        print(f' Copied test_report.pdf → {dest}')

    # 4b-4f. Code analyses + consolidated audit
    for label, module in (
        ('code modularisation analysis',   'docs.models.project'),
        ('__init__.py substantive-code audit', 'docs.models.init_audit'),
        ('code duplication analysis',      'docs.models.duplication'),
        ('hard-coding parameter audit',    'docs.models.hardcoding'),
        ('embedded JS/CSS audit',          'docs.models.embedded_js'),
        ('json-file audit',                'docs.models.json_files'),
        ('data lineage report (BCBS 239)', 'docs.models.data_lineage'),
        ('model risk governance report',   'docs.models.model_risk'),
        ('full audit report',              'docs.models.full_audit'),
    ):
        print(f'\nGenerating {label}...')
        sp.run([sys.executable, '-m', module], cwd=str(project_root))
