# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""Section printers for the end-of-run portfolio report.

Each function takes the counts dict produced by ``summary._gather_counts``
and writes one section to stdout. Kept separate from ``summary.py`` to
keep both files under the 300-line budget.
"""

import statistics

from . import _report_format as fmt


def gauges(c):
    fmt.heading('1. GAUGE NETWORK')
    fmt.row('Gauges generated', f'{c["gauge_count"]}')
    fmt.row('Time series (gaugets)', f'{c["gaugets_ct"]} files')
    fmt.row('Historical daily (gaugehd)', f'{c["gaugehd_ct"]} files')
    if c['tidal_counts']:
        parts = [f'{v} {k.lower()}' for k, v in sorted(c['tidal_counts'].items())]
        fmt.row('Tidal classification', ', '.join(parts))
    if c['winter_means']:
        w_avg = statistics.mean(c['winter_means'])
        s_avg = statistics.mean(c['summer_means'])
        fmt.row('Avg winter baseline (DJF)', f'{w_avg:.3f} m')
        fmt.row('Avg summer baseline (JJA)', f'{s_avg:.3f} m')
        fmt.row('Seasonal range', f'{w_avg - s_avg:.3f} m')


def storms(c):
    fmt.heading('2. STORM SEQUENCES')
    seq_count = c['seq_summary'].get('num_sequences', 0)
    fmt.row('Sequences generated', f'{seq_count:,}')
    tc = c['seq_summary'].get('sequence_type_counts', {})
    if tc:
        parts = [f'{k}: {v:,}' for k, v in sorted(tc.items())]
        fmt.row('Sequence types', ', '.join(parts))
    ic = c['seq_summary'].get('intensity_category_counts', {})
    if ic:
        parts = [f'{k}: {v:,}' for k, v in sorted(ic.items())]
        fmt.row('Intensity categories', ', '.join(parts))
    precip = c['seq_summary'].get('precipitation_mm', {})
    if precip:
        fmt.row('Precipitation (mm)',
                f'min {precip["min"]:.0f} / mean {precip["mean"]:.0f} / max {precip["max"]:.0f}')
    dur = c['seq_summary'].get('duration_hours', {})
    if dur:
        fmt.row('Duration (hours)',
                f'min {dur["min"]:.0f} / mean {dur["mean"]:.0f} / max {dur["max"]:.0f}')


def stress(c):
    fmt.heading('3. STRESS TESTING')
    fmt.row('Alert-breaching sequences', f'{c["stress_count"]:,}')
    gs = c['gauge_summary']
    if gs.get('alert_sequences') is not None:
        fmt.row('Warning sequences', f'{gs.get("warning_sequences", 0):,}')
        fmt.row('Severe sequences', f'{gs.get("severe_sequences", 0):,}')
    fmt.row('GBM classifiers trained', f'{c["classifier_ct"]}')
    if c['ts'].get('avg_auc_roc'):
        fmt.row('Average AUC-ROC', f'{c["ts"]["avg_auc_roc"]:.4f}')


def hazard(c):
    fmt.heading('4. HAZARD CURVES')
    fmt.row('Gauge hazard curves (GEV)', f'{c["gcurve_count"]}')
    fmt.row('Property hazard curves', f'{c["pcurve_count"]}')


def residential(c):
    fmt.heading('5. PROPERTIES & MORTGAGES')
    fmt.row('Properties generated', f'{c["prop_count"]}')
    fmt.row('Flood time series', f'{c["propertyts_ct"]} files')
    if c['propertytsd_ct']:
        fmt.row('Synthetic distance TS', f'{c["propertytsd_ct"]} files')
    if c['propertytse_ct']:
        fmt.row('Synthetic elevation TS', f'{c["propertytse_ct"]} files')
    if c['propertytsb_ct']:
        fmt.row('BRI-adjusted floor TS', f'{c["propertytsb_ct"]} files')
    fmt.row('Mortgages linked', f'{c["mort_count"]}')
    fmt.row('Counterparties', f'{c["ctpy_count"]}')


def commercial(c):
    if not c['com_count']:
        return
    fmt.heading('5b. COMMERCIAL ASSETS')
    fmt.row('Commercial assets generated', f'{c["com_count"]}')
    fmt.row('Commercial loans linked', f'{c["com_loan_ct"]}')
    if c['commercialts_ct']:
        fmt.row('Commercial flood TS', f'{c["commercialts_ct"]} files')
    if c['commercialtsd_ct']:
        fmt.row('Commercial distance TS', f'{c["commercialtsd_ct"]} files')
    if c['commercialtse_ct']:
        fmt.row('Commercial elevation TS', f'{c["commercialtse_ct"]} files')
    if c['commercialtsb_ct']:
        fmt.row('Commercial BRI-adjusted floor TS', f'{c["commercialtsb_ct"]} files')
    if c['com_hc_ct']:
        fmt.row('Commercial hazard curves', f'{c["com_hc_ct"]}')


def trading(c):
    fmt.heading('6. TRADING BOOK')
    fmt.row('PRS gauge trades', f'{c["gauge_trade_ct"]}')
    fmt.row('PRS property trades', f'{c["prop_trade_ct"]}')
    fmt.row('Total PRS trades', f'{c["trade_ct"]}')
    fmt.row('Historical EOD snapshots', f'{c["eod_ct"]}')


def output_files(c):
    fmt.heading('7. OUTPUT FILES')
    seq_count = c['seq_summary'].get('num_sequences', 0)
    fmt.row('gauge.json', f'{c["gauge_count"]} flood gauges')
    fmt.row('property.json', f'{c["prop_count"]} properties')
    fmt.row('mortgage.json', f'{c["mort_count"]} mortgages')
    fmt.row('counterparty.json', f'{c["ctpy_count"]} counterparties')
    fmt.row('storm_sequences.json', f'{seq_count:,} sequences')
    fmt.row('stress_storms/', f'{c["stress_count"]:,} alert storms')
    fmt.row('gaugehc.json', f'{c["gcurve_count"]} hazard curves')
    fmt.row('propertyhc.json', f'{c["pcurve_count"]} property curves')
    if c['shd_count']:
        fmt.row('propertyshd.json', f'{c["shd_count"]} synthetic distance curves')
    if c['she_count']:
        fmt.row('propertyshe.json', f'{c["she_count"]} synthetic elevation curves')
    if c['bri_count']:
        fmt.row('propertybri.json', f'{c["bri_count"]} BRI-adjusted floor curves')
    fmt.row('gaugets/', f'{c["gaugets_ct"]} gauge time series')
    fmt.row('gaugehd/', f'{c["gaugehd_ct"]} historical daily')
    fmt.row('propertyts/', f'{c["propertyts_ct"]} property flood series')
    if c['propertytsd_ct']:
        fmt.row('propertytsd/', f'{c["propertytsd_ct"]} synthetic distance series')
    if c['propertytse_ct']:
        fmt.row('propertytse/', f'{c["propertytse_ct"]} synthetic elevation series')
    if c['propertytsb_ct']:
        fmt.row('propertytsb/', f'{c["propertytsb_ct"]} BRI-adjusted floor series')
    # Commercial outputs — only when a commercial portfolio exists.
    if c['com_count']:
        fmt.row('commercial.json', f'{c["com_count"]} commercial assets')
    if c['com_loan_ct']:
        fmt.row('commercial_loan.json', f'{c["com_loan_ct"]} commercial loans')
    if c['com_hc_ct']:
        fmt.row('commercialhc.json', f'{c["com_hc_ct"]} commercial curves')
    if c['com_shd_ct']:
        fmt.row('commercialshd.json', f'{c["com_shd_ct"]} commercial distance curves')
    if c['com_she_ct']:
        fmt.row('commercialshe.json', f'{c["com_she_ct"]} commercial elevation curves')
    if c['com_bri_ct']:
        fmt.row('commercialbri.json', f'{c["com_bri_ct"]} commercial BRI-adjusted floor curves')
    if c['commercialts_ct']:
        fmt.row('commercialts/', f'{c["commercialts_ct"]} commercial flood series')
    if c['commercialtsd_ct']:
        fmt.row('commercialtsd/', f'{c["commercialtsd_ct"]} commercial distance series')
    if c['commercialtse_ct']:
        fmt.row('commercialtse/', f'{c["commercialtse_ct"]} commercial elevation series')
    fmt.row('stressm/', f'{c["classifier_ct"]} classifiers')
    fmt.row('prs/', f'{c["gauge_trade_ct"]} gauge + {c["prop_trade_ct"]} property trades')
    fmt.row('eod/', f'{c["eod_ct"]} EOD snapshots')


def data_size(output_dir):
    try:
        total_bytes = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
        if total_bytes > 1_073_741_824:
            size_str = f'{total_bytes / 1_073_741_824:.2f} GB'
        else:
            size_str = f'{total_bytes / 1_048_576:.1f} MB'
        fmt.row('Total data size', size_str)
    except Exception:
        pass
