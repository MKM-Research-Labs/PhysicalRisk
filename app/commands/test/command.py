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

"""Top-level ``cmd_test`` orchestrator wiring together the test phases."""

import os
import sys
import subprocess as sp

from config import config

from .audit import _check_deps, _parse_coverage_pct, _run_audit_reports
from .e2e import _run_e2e_tests
from .helpers import _cleanup_worktree_data, _resolve_python
from .lineage import _run_data_lineage_tests
from .reports import _write_failures_report


def cmd_test(args):
    """Run tests and produce audit evidence package.

    Suite selectors: --unit, --e2e, --lineage, --all
    Output options:  --audit, --pdf, --params, --check-deps
    Filters:         --model X Y Z
    """
    # ---- Backward compatibility for deprecated flags ----
    if getattr(args, '_compat_test', False):
        print('WARNING: --test is deprecated, use --unit instead', file=sys.stderr)
        args.unit = True
    if getattr(args, '_compat_code', False):
        print('WARNING: --code is deprecated, use --audit instead', file=sys.stderr)
        args.audit = True

    # ---- Pin catchment for all test subprocesses ----
    # An explicit --<catchment> / --catchment-id flag wins; otherwise we
    # leave any existing MKM_CATCHMENT env var (or the 'thames' default)
    # untouched so non-interactive/CI runs keep working. The child pytest
    # and lineage processes inherit os.environ, so setting it here is
    # enough — no interactive prompt is forced for the test command.
    chosen_catchment = getattr(args, 'catchment_id', None)
    if chosen_catchment:
        available = config.list_catchments()
        if available and chosen_catchment not in available:
            print(f"\n  ✗ Unknown catchment '{chosen_catchment}'.")
            print(f"  Available: {', '.join(available)}")
            return 1
        os.environ['MKM_CATCHMENT'] = chosen_catchment
        config.catchment_id = chosen_catchment
    print(f" Catchment: {os.environ.get('MKM_CATCHMENT', 'thames')}")

    # ---- Handle --check-deps early exit ----
    if getattr(args, 'check_deps', False):
        return _check_deps()

    # ---- Handle --params early exit ----
    if getattr(args, 'params', False):
        print('Generating parameter inventory...')
        cmd = [sys.executable, '-m', 'docs.models.parameter_inventory.generator']
        if getattr(args, 'pdf', False):
            cmd.append('--pdf')
        project_root = config.get_project_root()
        result = sp.run(cmd, cwd=str(project_root))
        return result.returncode

    project_root = config.get_project_root()

    # Clean stale worktree data copies before tests start to free disk space
    print('--- Worktree data cleanup (pre-run) ---')
    _cleanup_worktree_data(str(project_root))
    print()

    # All artefacts land in data/output/audit/
    audit_dir = str(config.get_reports_dir('audit'))
    os.makedirs(audit_dir, exist_ok=True)

    junit_xml = os.path.join(audit_dir, 'junit.xml')
    cov_html  = os.path.join(audit_dir, 'coverage')
    cov_xml   = os.path.join(audit_dir, 'coverage.xml')

    # ---- Resolve which suites and outputs to run ----
    has_suite = (getattr(args, 'unit', False) or getattr(args, 'e2e', False)
                 or getattr(args, 'lineage', False) or getattr(args, 'run_all', False))
    has_output = getattr(args, 'audit', False)

    if not has_suite and not has_output:
        # No flags at all → default to everything
        args.run_all = True
        args.audit = True

    do_unit    = getattr(args, 'run_all', False) or getattr(args, 'unit', False)
    do_e2e     = getattr(args, 'run_all', False) or getattr(args, 'e2e', False)
    do_lineage = getattr(args, 'run_all', False) or getattr(args, 'lineage', False)
    do_audit   = getattr(args, 'audit', False)
    do_pdf     = getattr(args, 'pdf', False)

    # ---- Capture git commit SHA ----
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

    # ---- Banner ----
    print('=' * 60)
    print('MKM Research Labs — Test & Audit')
    print('=' * 60)
    if git_sha:
        print(f' Git SHA : {git_sha[:12]}')
    print(f' Output  : {audit_dir}')
    phases = []
    if do_lineage:
        phases.append('lineage')
    if do_unit:
        phases.append('unit')
    if do_e2e:
        phases.append('e2e')
    if do_audit:
        phases.append('audit reports')
    print(f' Phases  : {", ".join(phases)}')
    print()

    _python_exe = _resolve_python(project_root)
    pytest_ok = True
    coverage_pct = None
    data_lineage_results = None
    e2e_results = None

    # ------------------------------------------------------------------
    # 1. Data lineage consistency checks (BCBS 239 P3)
    # ------------------------------------------------------------------
    if do_lineage:
        print('Running data lineage consistency checks...')
        data_lineage_results = _run_data_lineage_tests(project_root, audit_dir)
        if data_lineage_results and data_lineage_results.get('failed', 0) > 0:
            print()
            print('  WARNING: Data lineage checks FAILED.')
            print('  Pipeline data is inconsistent — audit results may be unreliable.')
            print('  Regenerate data in order: port --gauge → port --stressm → port --hazard → port --blotter')
            print()

    # ------------------------------------------------------------------
    # 2. Unit / model tests with coverage
    # ------------------------------------------------------------------
    if do_unit:
        print('Running unit/model tests with coverage...')

        tests_dir = os.path.join(str(project_root), 'tests')
        e2e_dir = os.path.join(tests_dir, 'e2e')
        pytest_cmd = [
            _python_exe, '-m', 'pytest',
            tests_dir,
            f'--ignore={e2e_dir}',
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

        # Coverage core is pinned to ctrace in pyproject.toml [tool.coverage.run]
        # to avoid the sys.monitoring under-count on Python 3.13.x.
        pytest_result = sp.run(pytest_cmd, cwd=str(project_root))
        pytest_ok = pytest_result.returncode == 0
        print()

        # Parse coverage percentage
        coverage_pct = _parse_coverage_pct(cov_xml)
        if coverage_pct is not None:
            print(f' Coverage: {coverage_pct:.1f}%')

        # Write test failures report
        _write_failures_report(junit_xml, audit_dir)

    # ------------------------------------------------------------------
    # 3. E2E browser tests (Playwright)
    # ------------------------------------------------------------------
    if do_e2e:
        print('\nRunning E2E browser tests (Playwright)...')
        e2e_results = _run_e2e_tests(project_root, audit_dir, _python_exe)

    # ------------------------------------------------------------------
    # 4. Audit reports (doc generators)
    # ------------------------------------------------------------------
    if do_audit:
        _run_audit_reports(project_root, audit_dir, _python_exe,
                           coverage_pct, git_sha, do_pdf)

    # ------------------------------------------------------------------
    # 5. Summary
    # ------------------------------------------------------------------
    print('\n' + '=' * 60)
    print('Audit Package Contents')
    print('=' * 60)
    artefacts = [
        ('JUnit XML',              junit_xml),
        ('Coverage XML',           cov_xml),
        ('Coverage HTML',          cov_html),
        ('Data Lineage Results',   os.path.join(audit_dir, 'data_lineage_results.json')),
        ('Data Lineage JUnit',     os.path.join(audit_dir, 'data_lineage_junit.xml')),
        ('E2E Results',            os.path.join(audit_dir, 'e2e', 'e2e_results.json')),
        ('E2E JUnit',              os.path.join(audit_dir, 'e2e', 'e2e_junit.xml')),
        ('Test Report PDF',        os.path.join(audit_dir, 'test_report.pdf')),
        ('Large File Report PDF',  os.path.join(audit_dir, 'large_file_report.pdf')),
        ('Large Test Report TXT',  os.path.join(audit_dir, 'large_test_report.txt')),
        ('Init Audit Report PDF',  os.path.join(audit_dir, 'init_audit_report.pdf')),
        ('Init Audit Results JSON', os.path.join(audit_dir, 'init_audit_results.json')),
        ('Code Duplication PDF',   os.path.join(audit_dir, 'code_duplication_report.pdf')),
        ('Hard-Coding Audit PDF',  os.path.join(audit_dir, 'hardcoding_report.pdf')),
        ('Embedded JS/CSS PDF',    os.path.join(audit_dir, 'embedded_js_report.pdf')),
        ('Data Lineage PDF',       os.path.join(audit_dir, 'data_lineage_report.pdf')),
        ('Model Risk Report PDF',  os.path.join(audit_dir, 'model_risk_report.pdf')),
        ('Full Audit Report PDF',  os.path.join(audit_dir, 'full_audit_report.pdf')),
    ]
    for label, path in artefacts:
        exists = os.path.exists(path)
        size = ''
        if exists and os.path.isfile(path):
            size = f' ({os.path.getsize(path) / 1024:.1f} KB)'
        status = 'OK' if exists else 'MISSING'
        print(f' [{status}] {label}: {path}{size}')
    print()
    if do_unit:
        print('Status:', 'ALL PASS' if pytest_ok else 'TEST FAILURES — see junit.xml')

    # Clean up any worktree data copies created by E2E tests during this run
    print()
    print('--- Worktree data cleanup (post-run) ---')
    _cleanup_worktree_data(str(project_root))
