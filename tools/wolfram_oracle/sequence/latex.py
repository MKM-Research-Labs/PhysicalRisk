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
    ORACLE_SS_CODE_TOL,
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
        ("Multi-storm sequences left no room for a gap, against the exact share (standard errors)",
         f"{mc['z_zero']:.2f}", z, mc["z_zero"] <= ORACLE_SS_Z_LIMIT),
        (f"\\S5.4, the validator on all {v['total']:,} sequences generated: invalid", str(v["invalid"]), "0",
         v["invalid"] == 0),
        ("\\S5.4, the validator: injected faults caught (late end, overlap, gap count, type)",
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


def _override(o):
    runs = o["runs"]
    if any("error" in x for x in runs.values()):
        return "an override exists; exercising it failed"
    took = "takes effect" if runs["after"]["probability"] else "does not take effect"
    return (f"\\texttt{{storm\\_control.json}} overrides every table, applied by {_files(o['callers'])} only. "
            f"Applied before the generator is imported, the sequence probability {took}; imported first, "
            f"{'it does not' if not runs['before']['probability'] else 'it does'}; the duration table never does")


def rows(c, e, v):
    cont, rec, cor, pb = c["continuous"], c["recovery"], c["correlation"], c["precipitation"]["got"]
    cap, sc, cl = c["cap"], c["scaling"], e["classifier"]
    return [
        ("Eq.~4, Tables~2--6, 8", "the code's parameters", "all as stated" if c["parameters"]["met"]
         else "differ: " + ", ".join(c["parameters"]["differ"]), _met(c["parameters"]["met"])),
        ("Eq.~5, \\S3.5", "durations and gaps are triangular draws",
         f"rounded to whole hours: {cont['whole']:,} of {cont['durations']:,} uncapped durations are whole; "
         "gaps are rounded before Eq.~8 scales them", _met(cont["met"])),
        ("\\S3.1, \\S3.4.1, \\S3.5.1", "every sequence ends by 156\\,h, leaving 12\\,h to drain",
         f"latest end {c['window']['end']:.1f}\\,h; least drainage {c['window']['drain']:.1f}\\,h",
         _met(c["window"]["met"])),
        ("\\S3.5, Table~4", "gaps of 6--36\\,h or 24--72\\,h let the catchment drain between storms",
         f"{100 * rec['zero']:.1f}\\% of multi-storm sequences have no gap at all ({100 * rec['cat_persistent']:.0f}\\% "
         f"of catastrophic persistent ones); {100 * rec['compressed']:.1f}\\% have gaps shorter than drawn",
         _met(rec["met"])),
        ("Table~8", "a later storm is at least as strong as the first with probability 0.70",
         f"{cor['exact']:.2f} exactly; the code {cor['seen']:.3f} over {cor['storms']:,} storms. 0.70 is "
         "Eq.~13's chance of exceeding the base", _met(cor["met"])),
        ("Table~7", "$P_{\\mathrm{base}}$: Thames 35, Rhine 40, Danube 45, Mississippi 55\\,mm",
         "the code: " + ", ".join(f"{v:g}" for v in pb.values()), _met(c["precipitation"]["met"])),
        ("\\S6.1, Table~9", f"expected counts {_counts(ORACLE_SS_TABLE9)} (isolated, doublet, cluster, persistent)",
         f"exactly {_counts(c['table9']['exact'])}", _met(c["table9"]["met"])),
        ("\\S7.2", "over 100 seeds, every type within 2\\% of Table~9",
         f"worst {c['seeds']['worst_pct']:.0f}\\% off", _met(c["seeds"]["met"])),
        ("\\S6.2", "the cap binds on $\\approx$99\\% of catastrophic durations at $n=5$, and $\\approx$35\\% of all draws",
         f"{cap['cat5']:.0f}\\%, and {cap['share']:.1f}\\%", _met(cap["met"])),
        ("\\S6.3", "gaps are scaled in $\\approx$20\\% of moderate-to-severe persistent sequences, $\\approx$60\\% "
         "of catastrophic ones", f"shorter than drawn in {sc['modsev']:.1f}\\% and {sc['cat']:.0f}\\%",
         _met(sc["met"])),
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
        ("Q4", "no mechanism exists for runtime override of the tables", _override(e["override"]),
         _met(e["override"]["met"])),
        ("\\S7.3, \\S7.4", "classifier AUC-ROC $\\approx$0.993 across all 52 Thames gauges; GAUGE-8f1d368d",
         (f"the training summary: {cl['trained']} gauges, mean {cl['auc']}; "
          f"GAUGE-8f1d368d {'present' if cl['example'] else 'absent'}") if cl["found"] else "no training summary",
         _met(cl["met"])),
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
        "bmZeroPct": f"{100 * c['recovery']['zero']:.0f}\\%",
        "bmCapPct": f"{c['cap']['share']:.0f}\\%",
        "bmModSevPct": f"{c['scaling']['modsev']:.0f}\\%",
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
