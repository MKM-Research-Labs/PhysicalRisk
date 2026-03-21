# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to
# the terms and conditions of the license agreement provided with this software.

"""Data loading for the model risk governance report."""

import json
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

_root = Path(__file__).resolve().parents[3]

DATA_DIR = _root / 'data'
AUDIT_DIR = _root / 'data' / 'output' / 'audit'
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
    }
