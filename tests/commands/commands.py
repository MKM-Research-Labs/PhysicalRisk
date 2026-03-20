#!/usr/bin/env python3

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

"""
Test command - Audit evidence package generation.
"""

import os
import sys
import subprocess as sp
import shutil

from config import config


def register_parser(subparsers):
    """Register the 'test' subcommand."""
    sp_test = subparsers.add_parser(
        "test", help="Run tests and produce full audit evidence package")
    sp_test.add_argument("--audit", action="store_true",
                        help="Produce JUnit XML + coverage + LaTeX report")
    sp_test.add_argument("--pdf", action="store_true",
                        help="Compile LaTeX report to PDF")
    sp_test.add_argument("--model", nargs="+",
                        help="Filter by model alias (e.g. MP GH TD)")
    sp_test.set_defaults(func=cmd_test)

def cmd_test(args):
    """Run tests and produce a full audit evidence package."""
    project_root = config.get_project_root()
    audit_dir = os.path.join(str(project_root), 'data', 'output', 'audit')
    os.makedirs(audit_dir, exist_ok=True)

    junit_xml = os.path.join(audit_dir, 'junit.xml')
    cov_html  = os.path.join(audit_dir, 'coverage')
    cov_xml   = os.path.join(audit_dir, 'coverage.xml')

    # 1. Capture git commit SHA
    git_sha = None
    try:
        result = sp.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, cwd=str(project_root),
        )
        if result.returncode == 0:
            git_sha = result.stdout.strip()
    except FileNotFoundError:
        pass

    print('=' * 60)
    print('MKM Research Labs — Audit Evidence Package')
    print('=' * 60)
    if git_sha:
        print(f' Git SHA : {git_sha[:12]}')
    print(f' Output  : {audit_dir}')
    print()

    # 2. Run pytest with JUnit XML + coverage
    print('Running test suite with coverage...')
    pytest_cmd = [
        sys.executable, '-m', 'pytest',
        'tests/commands/',              # ← updated
        f'--junitxml={junit_xml}',
        '--cov=src',
        f'--cov-report=html:{cov_html}',
        f'--cov-report=xml:{cov_xml}',
        '--cov-report=term-missing:skip-covered',
        '-q', '--tb=short',
    ]

    model_filter = getattr(args, 'model', None)
    if model_filter:
        pytest_cmd.extend(['--model'] + model_filter)

    pytest_result = sp.run(pytest_cmd, cwd=str(project_root))
    pytest_ok = pytest_result.returncode == 0
    print()

    # 3. Parse coverage percentage
    coverage_pct = None
    if os.path.exists(cov_xml):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(cov_xml)
            root = tree.getroot()
            line_rate = float(root.get('line-rate', 0))
            coverage_pct = line_rate * 100
            print(f' Coverage: {coverage_pct:.1f}%')
        except Exception:
            pass

    # 4. Generate LaTeX / PDF documentation
    print('\nGenerating model documentation...')
    doc_cmd = [sys.executable, '-m', 'docs.models.test_results.generator']

    if getattr(args, 'pdf', False):
        doc_cmd.append('--pdf')
    if git_sha:
        doc_cmd.extend(['--git-sha', git_sha])
    if coverage_pct is not None:
        doc_cmd.extend(['--coverage-pct', f'{coverage_pct:.2f}'])

    sp.run(doc_cmd, cwd=str(project_root))

    # 5. Copy PDF to audit directory
    _test_report_pdf = os.path.join(
        str(project_root),
        'docs', 'models', 'test_results', 'test_results', 'test_report.pdf')
    if os.path.exists(_test_report_pdf):
        dest = os.path.join(audit_dir, 'test_report.pdf')
        shutil.copy2(_test_report_pdf, dest)
        print(f' Copied test_report.pdf → {dest}')

    # 6. Print audit package summary
    print('\n' + '=' * 60)
    print('Audit Package Contents')
    print('=' * 60)
    artefacts = [
        ('JUnit XML',       junit_xml),
        ('Coverage XML',    cov_xml),
        ('Coverage HTML',   cov_html),
        ('Test Report PDF', os.path.join(audit_dir, 'test_report.pdf')),
    ]
    for label, path in artefacts:
        exists = os.path.exists(path)
        size = f' ({os.path.getsize(path) / 1024:.1f} KB)' if exists and os.path.isfile(path) else ''
        status = 'OK' if exists else 'MISSING'
        print(f' [{status}] {label}: {path}{size}')
    print()
    print('Status:', 'ALL PASS' if pytest_ok else 'TEST FAILURES — see junit.xml')
