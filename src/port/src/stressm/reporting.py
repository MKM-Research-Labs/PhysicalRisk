# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Console reporting for the multi-storm stress pipeline (single-gauge mode)."""

import numpy as np


def _print_gauge_progression(gauge: dict, records: list, total: int) -> None:
    """Print a detailed progression report for a single gauge."""
    gid = gauge["gauge_id"]
    alert_l  = gauge["flood_alert"]
    warning_l = gauge["flood_warning"]
    severe_l  = gauge["severe_warning"]
    base_l   = gauge["base_level"]

    cats = ["moderate", "severe", "extreme", "catastrophic"]
    cat_peaks: dict = {c: [] for c in cats}
    cat_peaks["other"] = []

    n_alert = n_warning = n_severe = 0
    all_peaks = []

    for rec in records:
        peak = rec["peaks_m"][0]
        all_peaks.append(peak)
        cat = rec.get("intensity_category", "other") or "other"
        cat_peaks.get(cat, cat_peaks["other"]).append(peak)
        if rec["alert"][0]:
            n_alert += 1
        if rec["warning"][0]:
            n_warning += 1
        if rec["severe"][0]:
            n_severe += 1

    all_peaks_arr = np.array(all_peaks)

    pcts = [50, 75, 90, 95, 99, 99.5]
    pct_vals = np.percentile(all_peaks_arr, pcts)

    W = 62
    print(f"\n{'=' * W}")
    print(f"  Gauge Progression Report — {gid}")
    print(f"{'=' * W}")
    print(f"  Gauge thresholds:")
    print(f"    Base level   : {base_l:.2f} m")
    print(f"    Flood alert  : {alert_l:.2f} m")
    print(f"    Flood warning: {warning_l:.2f} m")
    print(f"    Severe warning:{severe_l:.2f} m")
    print(f"  Sequences: {total:,}  |  peak range: "
          f"{all_peaks_arr.min():.2f} – {all_peaks_arr.max():.2f} m")
    print()

    print(f"  Threshold exceedance:")
    print(f"    Alert    (≥ {alert_l:.2f} m): {n_alert:>6,}  ({n_alert/total*100:5.1f}%)")
    print(f"    Warning  (≥ {warning_l:.2f} m): {n_warning:>6,}  ({n_warning/total*100:5.1f}%)")
    print(f"    Severe   (≥ {severe_l:.2f} m): {n_severe:>6,}  ({n_severe/total*100:5.1f}%)")
    print()

    print(f"  Peak level distribution (all sequences):")
    for p, v in zip(pcts, pct_vals):
        bar_len = int((v - base_l) / max(severe_l - base_l, 0.01) * 30)
        bar = "█" * min(max(bar_len, 0), 30)
        marker = ""
        if v >= severe_l:
            marker = "  ← SEVERE"
        elif v >= warning_l:
            marker = "  ← WARNING"
        elif v >= alert_l:
            marker = "  ← ALERT"
        print(f"    P{p:<4} {v:6.2f} m  {bar}{marker}")
    print()

    print(f"  Peak by intensity category:")
    print(f"    {'Category':<14} {'n':>6}  {'mean':>7}  {'p90':>7}  {'max':>7}  "
          f"{'alert%':>7}  {'warn%':>7}")
    print(f"    {'-'*14}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*7}")
    for cat in cats:
        peaks_c = np.array(cat_peaks[cat]) if cat_peaks[cat] else np.array([base_l])
        n_c = len(cat_peaks[cat])
        if n_c == 0:
            continue
        n_alert_c = int((peaks_c >= alert_l).sum())
        n_warn_c  = int((peaks_c >= warning_l).sum())
        print(f"    {cat:<14}  {n_c:>6,}  "
              f"{peaks_c.mean():>7.2f}  "
              f"{np.percentile(peaks_c, 90):>7.2f}  "
              f"{peaks_c.max():>7.2f}  "
              f"{n_alert_c/n_c*100:>6.1f}%  "
              f"{n_warn_c/n_c*100:>6.1f}%")
    print()

    type_groups: dict = {}
    for rec in records:
        t = rec["sequence_type"]
        type_groups.setdefault(t, []).append(rec["peaks_m"][0])
    print(f"  Peak by sequence type:")
    print(f"    {'Type':<12} {'n':>6}  {'mean':>7}  {'p90':>7}  {'max':>7}")
    print(f"    {'-'*12}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}")
    for st in sorted(type_groups):
        pk = np.array(type_groups[st])
        print(f"    {st:<12}  {len(pk):>6,}  "
              f"{pk.mean():>7.2f}  "
              f"{np.percentile(pk, 90):>7.2f}  "
              f"{pk.max():>7.2f}")
    print(f"{'=' * W}\n")
