# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Extract summary statistics and worst-offender tables from a jscpd report."""

from collections import Counter, defaultdict

from ._paths import SRC_DIR


def _analyse(report: dict) -> dict:
    """Extract summary statistics and worst-offender tables."""
    total = report.get('statistics', {}).get('total', {})
    duplicates = report.get('duplicates', [])

    file_counts = Counter()
    file_dup_lines = defaultdict(int)
    for dup in duplicates:
        for key in ('firstFile', 'secondFile'):
            name = dup[key]['name'].replace(str(SRC_DIR) + '/', '').replace('src/', '')
            file_counts[name] += 1
            file_dup_lines[name] += dup.get('lines', 0)

    worst = [(f, file_counts[f], file_dup_lines[f]) for f in file_counts]
    worst.sort(key=lambda x: (-x[1], -x[2]))
    worst = worst[:15]

    by_lines = sorted(duplicates, key=lambda x: -x.get('lines', 0))[:20]
    largest = []
    for dup in by_lines:
        f1 = dup['firstFile']['name'].replace('src/', '')
        f2 = dup['secondFile']['name'].replace('src/', '')
        l1s = dup['firstFile'].get('start', dup['firstFile'].get('startLine', '?'))
        l2s = dup['secondFile'].get('start', dup['secondFile'].get('startLine', '?'))
        largest.append((f1, l1s, f2, l2s, dup.get('lines', 0), dup.get('tokens', 0)))

    fmt_stats = {}
    for fmt, data in report.get('statistics', {}).get('formats', {}).items():
        agg = data.get('total', {})
        if not agg:
            all_files = data.get('sources', {})
            agg = {
                'sources': len(all_files),
                'lines': sum(v.get('lines', 0) for v in all_files.values()),
                'clones': sum(v.get('clones', 0) for v in all_files.values()),
                'duplicatedLines': sum(v.get('duplicatedLines', 0) for v in all_files.values()),
            }
        fmt_stats[fmt] = agg

    return {
        'total': total,
        'worst': worst,
        'largest': largest,
        'fmt_stats': fmt_stats,
        'num_clones': len(duplicates),
    }
