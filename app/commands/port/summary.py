# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""End-of-run portfolio summary report.

Orchestrates ``_gather_counts`` (reads every artefact) and the section
printers in ``summary_sections``. Kept under 300 lines by delegating the
section-print logic to its own module.
"""

import json
import statistics
from datetime import datetime
from pathlib import Path

from config import config

from . import summary_sections as sections
from ._report_format import W


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _count_key(path, key):
    return len(_load(path).get(key, {}))


def _count_dir(directory, pattern):
    try:
        return len(list(Path(directory).glob(pattern)))
    except Exception:
        return 0


def _gather_counts(output_dir):
    """Load + count every artefact the report references."""
    gauge_data = _load(output_dir / 'gauge.json')
    gauges = gauge_data.get('flood_gauges', [])

    c = {
        'gauge_count': len(gauges),
        'gauges': gauges,
        'prop_count': _count_key(output_dir / 'property.json', 'properties'),
        'mort_count': _count_key(output_dir / 'loan.json', 'loans'),
        'ctpy_count': _count_key(output_dir / 'counterparty.json', 'counterparties'),
        'gaugets_ct': _count_dir(output_dir / 'gaugets', 'GAUGE-*.json'),
        'gaugehd_ct': _count_dir(output_dir / 'gaugehd', 'gauge_GAUGE-*.json'),
        'propertyts_ct': _count_dir(output_dir / 'propertyts', 'PROP-*.json'),
        'propertytsd_ct': _count_dir(output_dir / 'propertytsd', 'PROP-*.json'),
        'propertytse_ct': _count_dir(output_dir / 'propertytse', 'PROP-*.json'),
        'propertytsb_ct': _count_dir(output_dir / 'propertytsb', 'PROP-*.json'),
        'gcurve_count': _count_key(output_dir / 'gaugehc.json', 'hazard_curves'),
        'pcurve_count': _count_key(output_dir / 'propertyhc.json', 'property_hazard_curves'),
        'shd_count': _count_key(output_dir / 'propertyshd.json', 'property_hazard_curves'),
        'she_count': _count_key(output_dir / 'propertyshe.json', 'property_hazard_curves'),
        'bri_count': _count_key(output_dir / 'propertybri.json', 'property_hazard_curves'),
        'com_count': _count_key(output_dir / 'commercial.json', 'commercial_assets'),
        'com_loan_ct': _count_key(output_dir / 'commercial_loan.json', 'commercial_loans'),
        'commercialts_ct': _count_dir(output_dir / 'commercialts', 'CPROP-*.json'),
        'commercialtsd_ct': _count_dir(output_dir / 'commercialtsd', 'CPROP-*.json'),
        'commercialtse_ct': _count_dir(output_dir / 'commercialtse', 'CPROP-*.json'),
        'commercialtsb_ct': _count_dir(output_dir / 'commercialtsb', 'CPROP-*.json'),
        'com_hc_ct': _count_key(output_dir / 'commercialhc.json', 'property_hazard_curves'),
        'com_shd_ct': _count_key(output_dir / 'commercialshd.json', 'property_hazard_curves'),
        'com_she_ct': _count_key(output_dir / 'commercialshe.json', 'property_hazard_curves'),
        'com_bri_ct': _count_key(output_dir / 'commercialbri.json', 'property_hazard_curves'),
    }

    # Storm sequences + stress storms (split-directory or legacy fallbacks).
    c['seq_summary'] = _load(output_dir / 'sequences_summary.json')
    sg_index = output_dir / 'sequence_gauge' / '_index.json'
    sg_legacy = output_dir / 'sequence_gauge_summary.json'
    if sg_index.exists():
        c['gauge_summary'] = _load(sg_index)
    elif sg_legacy.exists():
        c['gauge_summary'] = _load(sg_legacy)
    else:
        c['gauge_summary'] = {}

    ss_index = output_dir / 'stress_storms' / '_index.json'
    ss_legacy = output_dir / 'stress_storms.json'
    if ss_index.exists():
        ss_data = _load(ss_index)
    elif ss_legacy.exists():
        ss_data = _load(ss_legacy)
    else:
        ss_data = {}
    c['stress_count'] = len(ss_data.get('storms', []))

    # Tidal classification.
    tidal = {}
    for g in gauges:
        fg = g.get('FloodGauge', g)
        ti = (fg.get('SensorDetails', {})
              .get('GaugeInformation', {})
              .get('TidalInfluence', 'Unknown'))
        tidal[ti] = tidal.get(ti, 0) + 1
    c['tidal_counts'] = tidal

    # Seasonal baselines from gaugehd.
    winter_means, summer_means = [], []
    for f in (output_dir / 'gaugehd').glob('gauge_*_hd.json'):
        try:
            hd = _load(f)
            mm = hd.get('statistics', {}).get('monthly_means', {})
            if mm:
                winter_means.append(
                    statistics.mean([float(mm.get(m, 0)) for m in ['12', '01', '02']]))
                summer_means.append(
                    statistics.mean([float(mm.get(m, 0)) for m in ['06', '07', '08']]))
        except Exception:
            continue
    c['winter_means'] = winter_means
    c['summer_means'] = summer_means

    # Classifier summary.
    stressm_dir = output_dir / 'stressm'
    c['classifier_ct'] = _count_dir(stressm_dir, '*.joblib')
    c['ts'] = _load(stressm_dir / 'training_summary.json') if stressm_dir.exists() else {}

    # Trading book.
    prs_dir = config.get_reports_dir('prs')
    c['trade_ct'] = _count_dir(prs_dir, 'PRS-*.json') if prs_dir.exists() else 0
    gauge_trade_ct = prop_trade_ct = 0
    if prs_dir.exists():
        for tf in prs_dir.glob('PRS-*.json'):
            if tf.stem.startswith('PRS-P'):
                prop_trade_ct += 1
            else:
                gauge_trade_ct += 1
    c['gauge_trade_ct'] = gauge_trade_ct
    c['prop_trade_ct'] = prop_trade_ct
    c['eod_ct'] = _count_dir(config.get_eod_dir(), 'EOD-*')
    return c


def _print_port_summary(output_dir):
    """Print a detailed report of the generated portfolio."""
    c = _gather_counts(output_dir)
    now = datetime.now().strftime('%d-%b-%Y %H:%M')

    print(f'\n{"=" * W}')
    print(f'  MKM PORTFOLIO GENERATION REPORT')
    print(f'  {now}')
    print(f'{"=" * W}')

    sections.gauges(c)
    sections.storms(c)
    sections.stress(c)
    sections.hazard(c)
    sections.residential(c)
    sections.commercial(c)
    sections.trading(c)
    sections.output_files(c)
    sections.data_size(output_dir)

    print(f'\n{"=" * W}\n')
