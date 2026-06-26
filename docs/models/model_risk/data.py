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

"""Data loading for the model risk governance report."""

import json
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

from config import config

_root = config.get_project_root()

# Governance metadata is version-controlled repo content under
# docs/models/governance_data/, not shared data/.
DATA_DIR = config.get_governance_data_dir()
AUDIT_DIR = config.get_reports_dir('audit')
OUTPUT_PDF = AUDIT_DIR / 'model_risk_report.pdf'


def _load_json(path: Path):
    """Load a JSON file, returning {} or [] on failure."""
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    # Default: list for files known to be arrays, dict otherwise
    return {}


def load_inventory() -> dict:
    return _load_json(DATA_DIR / 'model_inventory.json')


def load_meetings() -> list:
    data = _load_json(DATA_DIR / 'mrc_meetings.json')
    return data if isinstance(data, list) else []


def load_bcbs() -> dict:
    return _load_json(DATA_DIR / 'bcbs239_assessment.json')


def load_raci() -> dict:
    return _load_json(DATA_DIR / 'raci_matrix.json')


def load_audit_log() -> list:
    data = _load_json(DATA_DIR / 'model_audit_log.json')
    return data if isinstance(data, list) else []


def load_junit() -> dict:
    """Parse junit.xml into summary."""
    path = AUDIT_DIR / 'junit.xml'
    result = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0,
              'skipped': 0, 'time_s': 0.0}
    if not path.exists():
        return result
    try:
        tree = ET.parse(str(path))
        root = tree.getroot()
        for suite in root.findall('.//testsuite'):
            result['total'] += int(suite.get('tests', 0))
            result['failed'] += int(suite.get('failures', 0))
            result['errors'] += int(suite.get('errors', 0))
            result['skipped'] += int(suite.get('skipped', 0))
            result['time_s'] += float(suite.get('time', 0))
        result['passed'] = (result['total'] - result['failed']
                            - result['errors'] - result['skipped'])
    except Exception:
        pass
    return result


def load_coverage() -> float | None:
    """Parse coverage.xml line-rate."""
    path = AUDIT_DIR / 'coverage.xml'
    if not path.exists():
        return None
    try:
        tree = ET.parse(str(path))
        return float(tree.getroot().get('line-rate', 0)) * 100
    except Exception:
        return None


def list_audit_files() -> list[dict]:
    """List all files in audit directory with size and mtime."""
    if not AUDIT_DIR.exists():
        return []
    results = []
    for f in sorted(AUDIT_DIR.iterdir()):
        if f.name.startswith('.') or f.is_dir():
            continue
        results.append({
            'name': f.name,
            'size_kb': f.stat().st_size / 1024,
            'modified': datetime.fromtimestamp(
                f.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
        })
    return results


def list_sensitivity_generators() -> list[str]:
    """List available sensitivity generator model families."""
    sens_dir = _root / 'docs' / 'models' / 'sensitivities'
    if not sens_dir.exists():
        return []
    return sorted(
        d.name for d in sens_dir.iterdir()
        if d.is_dir() and (d / 'generator' / '__init__.py').exists()
    )


_MODEL_DOC_DIRS = {
    'MKM-SI-001': 'storm_intensity',
    'MKM-SG-001': 'storm_gauge',
    'MKM-GH-001': 'gev_hazard',
    'MKM-PR-001': 'prs_pricing',
    'MKM-DD-001': 'flood_risk',
    'MKM-PV-001': 'property_valuation',
    'MKM-MP-001': 'mortgage_pricer',
    'MKM-RA-001': 'risk_assessment',
    'MKM-DE-001': 'delta_engine',
    'MKM-SP-001': 'spatial_model',
    'MKM-IP-001': 'insurance_premium',
    'MKM-FC-001': 'flood_classifier',
    'MKM-SS-001': 'storm_multi',
    'MKM-GHD-001': 'gaugehd_synthetic',
    'MKM-ST-001': 'stressm_pipeline',
    'MKM-PF-001': 'property_flood_response',
}


def scan_model_documentation() -> list[dict]:
    """Scan documentation completeness for each registered model."""
    docs_dir = _root / 'docs' / 'models'
    results = []
    for model_id, doc_dir in _MODEL_DOC_DIRS.items():
        model_path = docs_dir / doc_dir
        results.append({
            'model_id': model_id,
            'doc_dir': doc_dir,
            'has_core_doc': (model_path / f'{doc_dir}.pdf').is_file(),
            'has_test_results': (model_path / 'test_results.pdf').is_file(),
            'has_sensitivity': (model_path / 'sensitivity_tables.tex').is_file(),
            'has_analysis': (model_path / 'analysis.pdf').is_file(),
        })
    return results


def collect_all() -> dict:
    """Load all data sources into a single dict."""
    inventory = load_inventory()
    models = inventory.get('models', [])

    return {
        'inventory': inventory,
        'models': models,
        'meetings': load_meetings(),
        'bcbs': load_bcbs(),
        'raci': load_raci(),
        'audit_log': load_audit_log(),
        'junit': load_junit(),
        'coverage_pct': load_coverage(),
        'audit_files': list_audit_files(),
        'sensitivity_generators': list_sensitivity_generators(),
        'doc_completeness': scan_model_documentation(),
    }
