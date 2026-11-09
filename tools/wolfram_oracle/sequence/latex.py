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

"""LaTeX for the MKM-SS-001 benchmark document, generated from a run."""

from datetime import date

from tools.wolfram_oracle._latex import GENERATED, esc, longtab, outcome, sci, tab, write_files
from tools.wolfram_oracle._latex import macros as as_macros

from config.models import (
    ORACLE_SS_AUC_STATED,
    ORACLE_SS_CODE_TOL,
    ORACLE_SS_GAUGES_STATED,
    ORACLE_SS_TABLE9,
    ORACLE_SS_TABLE_PREFIX,
    ORACLE_SS_WOLFRAM_TOL,
    ORACLE_SS_Z_LIMIT,
)

_TYPES = ("isolated", "doublet", "cluster", "persistent")


def findings(r):
    rp, mc, v = r["replay"], r["mc"], r["validator"]
    z = f"{ORACLE_SS_Z_LIMIT:.0f}"
    out = [
        (f"Replay, {rp['sequences']:,} sequences: types or storm counts that differ from the reference's",
         str(rp["structure_off"]), "0", rp["structure_off"] == 0),
        ("Replay: worst relative error over durations, gaps, start times, intensities, precipitation, "
         "peak positions and Eqs.~16--20", sci(rp["worst"]), sci(ORACLE_SS_CODE_TOL), rp["worst"] <= ORACLE_SS_CODE_TOL),
        (f"Type mix over {mc['seeds']} seeds of 10{{,}}000 against Eq.~4 and Table~2's exact law "
         "(standard errors)", f"{mc['z_types']:.2f}", z, mc["z_types"] <= ORACLE_SS_Z_LIMIT),
        ("Storm counts in the default batch against the exact law (standard errors)", f"{mc['z_counts']:.2f}", z,
         mc["z_counts"] <= ORACLE_SS_Z_LIMIT),
        ("Multi-storm sequences with every storm capped, against the exact share (standard errors)",
         f"{mc['z_pinned']:.2f}", z, mc["z_pinned"] <= ORACLE_SS_Z_LIMIT),
        (f"\\S5.4, the validator on all {v['total']:,} sequences generated: invalid", str(v["invalid"]), "0",
         v["invalid"] == 0),
        ("\\S5.4, the validator: injected faults caught (late end, overlap, gap count, type, short gap)",
         f"{v['caught']} of {v['faults']}", f"{v['faults']} of {v['faults']}", v["caught"] == v["faults"]),
    ]
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_SS_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram agrees with the reference", sci(r["wolfram"]), sci(ORACLE_SS_WOLFRAM_TOL),
                    r["wolfram"] <= ORACLE_SS_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "met" if met else "\\textbf{not met}"


def _files(fs):
    dash = "-{}-"  # a command-line flag, not an en dash
    return ", ".join("\\texttt{" + esc(f).replace("--", dash) + "}" for f in fs)


def _counts(d):
    return ", ".join(f"{d[t]:,.0f}" for t in _TYPES)


def _exact(d):
    return ", ".join(f"{d[t]:,.2f}".rstrip("0").rstrip(".") for t in _TYPES)


def _override(o):
    runs = o["runs"]
    if any("error" in x for x in runs.values()):
        return "exercising it failed"

    def took(r):
        return "both take effect" if r["probability"] and r["durations"] else (
            "the probability only" if r["probability"] else "neither takes effect")
    return (f"applied by {_files(o['callers'])}. Applied before the generator is imported, {took(runs['after'])}; "
            f"after, {took(runs['before'])}")


def _least(rec):
    return ", ".join(f"{t} {rec['least'][t]:g}\\,h" for t in ("doublet", "cluster", "persistent"))


def rows(c, e, v):
    rec, cor, pr = c["recovery"], c["correlation"], c["precipitation"]
    cap, sc, cl = c["cap"], c["scaling"], e["classifier"]
    return [
        ("Eq.~4, Tables~1--6, 8", "the parameters in \\texttt{config.port}", "all as stated" if c["parameters"]["met"]
         else "differ: " + ", ".join(c["parameters"]["differ"]), _met(c["parameters"]["met"])),
        ("Eq.~5, \\S3.5", "durations and raw gaps are whole hours; a capped duration takes the cap",
         f"{c['whole']['whole']:,} of {c['whole']['durations']:,} uncapped durations are whole", _met(c["whole"]["met"])),
        ("\\S3.1, \\S3.4.1, \\S3.5.1", "every sequence ends by 156\\,h, leaving 12\\,h to drain",
         f"latest end {c['window']['end']:.1f}\\,h; least drainage {c['window']['drain']:.1f}\\,h",
         _met(c["window"]["met"])),
        ("\\S3.5, Table~4, \\S6.3", "every gap is at least 24\\,h (doublet, cluster) or 6\\,h (persistent); every "
         "storm is capped, holding each gap at that minimum, in 3.1\\% of multi-storm sequences",
         f"least gap {_least(rec)}; {rec['pinned']:.1f}\\% exactly, {rec['seen']:.1f}\\% in the default batch",
         _met(rec["met"])),
        ("Table~8", "a later storm is at least as strong as the first with probability 0.85",
         f"{cor['exact']:.2f} exactly; the code {cor['seen']:.3f} over {cor['storms']:,} storms", _met(cor["met"])),
        ("Table~7", "$P_{\\mathrm{base}}$: Thames 35, Mekong 90, Ha Long 100\\,mm; 35\\,mm where a catchment "
         "has no storm module", "the code: " + ", ".join(f"{x:g}" for x in pr["got"].values())
         + f"; {pr['fallback']:g} for the Rhine", _met(pr["met"])),
        ("\\S6.1, Table~9", f"expected counts {_counts(ORACLE_SS_TABLE9)} (isolated, doublet, cluster, persistent)",
         f"exactly {_exact(c['table9']['exact'])}", _met(c["table9"]["met"])),
        ("\\S7.2", "pooled over 100 seeds, every type within 1\\% of Table~9",
         f"worst {c['seeds']['worst_pct']:.2f}\\% off (one seed: {c['seeds']['per_seed_pct']:.1f}\\%)",
         _met(c["seeds"]["met"])),
        ("\\S6.2", "the cap never binds on an isolated storm; most often on catastrophic persistent "
         "durations, 77.7\\%; on 8.6\\% of all draws",
         f"{cap['isolated']:.1f}\\%; {cap['worst']:.2f}\\%, the most of any configuration; {cap['share']:.2f}\\%",
         _met(cap["met"])),
        ("\\S6.3", "gaps are shortened in 35.4\\% of multi-storm sequences; 4.7\\% of moderate-to-severe "
         "persistent ones, 99.7\\% of catastrophic", f"{sc['all']:.2f}\\%; {sc['modsev']:.2f}\\%, "
         f"{sc['cat']:.2f}\\%", _met(sc["met"])),
        ("Q6", "at the baseline the cap rate is within 50\\%, and shortening within 70\\% for every type: "
         "doublet 0.8, cluster 52.3, persistent 47.9\\%", ", ".join(f"{t} {x:.2f}\\%" for t, x in
         c["thresholds"]["by_type"].items()) + ("; within both" if c["thresholds"]["within"] else "; breached"),
         _met(c["thresholds"]["met"])),
        ("\\S5.3", "a fixed seed reproduces the batch", "it does" if c["reproducible"]["met"] else "it does not",
         _met(c["reproducible"]["met"])),
        ("\\S5.4, \\S7.1", "the validator finds no invalid sequence",
         f"{v['invalid']} of {v['total']:,}; it catches {v['caught']} of {v['faults']} injected faults",
         _met(v["invalid"] == 0)),
        ("Q2", "10{,}000 sequences in under 60\\,s", f"{e['speed']['seconds']:.1f}\\,s", _met(e["speed"]["met"])),
        ("\\S5.1", "the package holds the modules and functions listed", "all present" if e["modules"]["met"]
         else "missing: " + _files(e["modules"]["missing"]), _met(e["modules"]["met"])),
        ("\\S2.2, \\S5.5", "the consumers' paths, the command line and its output files",
         "do not exist: " + _files(e["paths"]["gone"]) if e["paths"]["gone"] else "all exist", _met(e["paths"]["met"])),
        ("Q4", "\\texttt{storm\\_control.json} overrides every table, applied on importing \\texttt{config} and when "
         "the screen saves, whichever was imported first", _override(e["override"]), _met(e["override"]["met"])),
        ("\\S7.3, \\S7.4", f"the training summary on file: {ORACLE_SS_GAUGES_STATED} Thames gauges, mean AUC-ROC {ORACLE_SS_AUC_STATED}; "
         "GAUGE-1aaf8b08",
         (f"{cl['trained']} gauges, mean {cl['auc']}; GAUGE-1aaf8b08 {'present' if cl['example'] else 'absent'}")
         if cl["found"] else "no training summary", _met(cl["met"])),
    ]


def _mets(c, e, v):
    return [x["met"] for x in c.values()] + [v["invalid"] == 0] + [x["met"] for x in e.values()]


def macros(provs, r, version, mode, c, e):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    mets = _mets(c, e, r["validator"])
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{max(provs, key=lambda p: p['last_commit'])['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram, computing each probability independently, agrees with the reference to "
                              f"{sci(r['wolfram'])}." if version else "Wolfram has not been run."),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmReplayN": f"{r['replay']['sequences']:,}".replace(",", "{,}"),
        "bmCodeErr": sci(r["replay"]["worst"]),
        "bmPinnedPct": f"{c['recovery']['pinned']:.1f}\\%",
        "bmCapPct": f"{c['cap']['share']:.1f}\\%",
        "bmShortPct": f"{c['scaling']['all']:.1f}\\%",
        "bmSubsequent": f"{c['correlation']['exact']:.2f}",
        "bmSeasonMonths": str(r["season"]),
        "bmIsolated": f"{c['table9']['exact']['isolated']:,.0f}".replace(",", "{,}"),
        "bmClaims": str(len(mets)), "bmClaimsMet": str(sum(m is True for m in mets)),
        "bmClaimsFailed": str(sum(m is False for m in mets)),
    })


def write_tables(out, provs, r, version, mode, c, e):
    return write_files(out, ORACLE_SS_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c, e),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{96mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + longtab("The model document's claims, tested", "tab:bm-claims",
                                      "p{19mm}p{46mm}p{68mm}l", "Claim & Stated & Benchmark finds & Outcome",
                                      rows(c, e, r["validator"])),
    })
