# MKM-GH-001 Wolfram Benchmark — Project Brief

**Model:** GEV Hazard Curve Model (MKM-GH-001), `GEVFitter` in `src/models/hazard/gev.py`
**Tool:** `tools/wolfram_oracle` (`python -m tools.wolfram_oracle gh001`)
**Current evidence:** `docs/models/gev_hazard_benchmark/MKM-GH-001_wolfram_benchmark.pdf` v0.1 (19-Oct-2026)
**Status of this brief:** consolidated review and requirements, 20-Oct-2026. Feed this to the project that generates the benchmark output.

---

## 1. Purpose and scope

The benchmark answers **validation question Q8** (does the implementation compute its formulae correctly?). It does not answer **Q9** (is a GEV fitted to per-storm peaks the right model for the hazard?). Keep that line explicit in every output.

Two questions are asked of the code, each against references that share none of its numerics:

1. **Arithmetic.** Given (μ, σ, ξ), are return levels and exceedance probabilities correct?
   References: an mpmath closed form at 50 digits, and Wolfram.
2. **Estimation.** Given a peak series, does the maximum-likelihood fit reach the maximum?
   References: an independent multi-start Nelder–Mead fit on a likelihood written from the density, and Wolfram's `EstimatedDistribution`.

Wolfram is a **reference implementation**, not a production dependency. It is called by the benchmark tool only. Production code never calls it.

---

## 2. Wolfram set-up

1. **Kernel.** Install Wolfram Engine (free for developers), or use Mathematica / Wolfram|One.
2. **Activate.** `wolframscript -activate` with a Wolfram ID. An unactivated kernel will not start under `wolframclient`.
3. **Python client.** `pip install wolframclient` in the PhysicalRisk environment.
4. **Kernel path and timeout.** These are already in config:
   - `ORACLE_WOLFRAM_KERNEL` = `/Applications/Wolfram Engine.app/Contents/MacOS/WolframKernel` (override with `WOLFRAM_KERNEL`).
   - `ORACLE_WOLFRAM_STARTUP_TIMEOUT` = 180 s. The Engine takes about 37 s to start, and the wolframclient default of 20 s never connects.
5. **Smoke test.**
   ```python
   from wolframclient.evaluation import WolframLanguageSession
   from wolframclient.language import wlexpr
   with WolframLanguageSession(kernel_path) as s:
       print(s.evaluate(wlexpr("$Version")))
   ```
6. **Version pinning.** Current kernel: `15.0.0 for Mac OS X ARM (64-bit) (May 26, 2026)`. `$Version` is read from the live kernel on every run and written into the evidence. Treat a Wolfram upgrade as a change to a reference implementation: re-run the benchmark and confirm no result moves beyond tolerance.
7. **Licence.** The free Engine's terms are aimed at development and non-production use. Confirm with Wolfram whether benchmarking a commercial model for regulatory evidence is covered, or buy a commercial licence. **Action: owner to confirm.**

### How the kernel is reached

- `wolframclient` starts the local kernel and talks to it over local sockets (ZeroMQ, localhost only).
- Expressions go across as Wolfram Language text via `wlexpr`, wrapped as `ToString[(expr), InputForm, NumberMarks -> False]`. Results return as strings, so 30-digit values survive the trip.
- All computation happens on the local machine. The only outbound traffic is the Engine's licence check. No MCP server and no LLM is involved.
- Each run also writes `return_levels.wl` and `fit.wl`. These can be replayed with `wolframscript -file`, and the output matches a live run's.
- Only parameters, probabilities, thresholds and synthetic samples are sent. No PhysicalRisk code and no production data is sent today.

**MCP is not used for evidence.** The hosted Wolfram MCP service suits exploratory checks only. Evidence must come from the pinned local kernel, which is deterministic and versioned.

---

## 3. Instruction set sent to Wolfram (current run)

There are 97 expressions in one session:

| # | Group | Count | Template |
|---|---|---|---|
| 1 | Version | 1 | `$Version` |
| 2 | Return level | 36 (6 cases × 6 T) | `N[Quantile[<dist>, 1 - 1/T], 30]` |
| 3 | Exceedance | 36 | `N[SurvivalFunction[<dist>, SetPrecision[<x_T exact>, 60]], 30]` |
| 4 | LL at model params | 8 (4 series × GEV/Gumbel) | `N[LogLikelihood[<dist at model params>, {<data, 60-digit>}], 30]` |
| 5 | Wolfram fit | 8 | `{ξ, μ, σ} &[List @@ EstimatedDistribution[{<data, machine>}, <family>, ParameterEstimator -> "MaximumLikelihood"]]` |
| 6 | LL at Wolfram fit | 8 | `LogLikelihood[EstimatedDistribution[…], {<data, machine>}]` |

`<dist>` is `MaxStableDistribution[μ, σ, ξ]`, or `ExtremeValueDistribution[μ, σ]` when ξ = 0.

**Precision rules** (in `_wl.py`; keep them):
- Each double is sent as its **exact binary value**, `SetPrecision[p/q, 60]`, so Wolfram computes with the number the model computed with.
- Do **not** send exact rationals unwrapped. An exact exponent such as −1/ξ (with a denominator of about 2^60) sends `SurvivalFunction` into exact arithmetic, and the kernel dies.
- Do **not** send Python `repr` strings. `1e-09` parses as `1*e - 9` in Wolfram Language. Machine reals use the `*^` form (`wl_machine`).
- Machine reals cap `N[expr, 30]` at machine precision. This is why inputs are raised to 60 digits.

Example from `return_levels.wl`:
```
N[SurvivalFunction[ExtremeValueDistribution[100, 20],
    SetPrecision[5101992436497429/35184372088832, 60]], 30]
```

---

## 4. Distribution mapping (must be stated in the model spec)

| Wolfram | Parameters | CDF F(x) | Law for | Use for flood peaks | scipy |
|---|---|---|---|---|---|
| `GumbelDistribution` | [α, β] | 1 − exp(−e^((x−α)/β)) | **minima** | **No** | `gumbel_l` |
| `ExtremeValueDistribution` | [α, β] | exp(−e^(−(x−α)/β)) | maxima | Yes (ξ = 0) | `gumbel_r` |
| `MaxStableDistribution` | [μ, σ, ξ] | exp(−[1 + ξ(x−μ)/σ]^(−1/ξ)) | maxima | Yes (general GEV) | `genextreme`, **c = −ξ** |
| `MinStableDistribution` | [μ, σ, ξ] | 1 − exp(−[1 − ξ(x−μ)/σ]^(−1/ξ)) | minima | No | negate data, then `genextreme` |

**Identities:**
- X ~ `ExtremeValueDistribution[μ, σ]` ⇔ −X ~ `GumbelDistribution[−μ, σ]`.
- X ~ `MaxStableDistribution[−μ, σ, ξ]` ⇔ −X ~ `MinStableDistribution[μ, σ, ξ]`.
- Wolfram's ξ has the same sign as the EVT convention (ξ > 0 is a heavy Fréchet tail). scipy's `c` is −ξ.

**Two silent traps.** Neither raises an error.

| Trap | μ = 100, σ = 20, 1-in-1000 | Correct value |
|---|---|---|
| `GumbelDistribution` used for maxima | 138.65 | 238.15 (`ExtremeValueDistribution`) |
| ξ = 0.2 passed unflipped to scipy | 174.88 | 398.07 |

Library names are not reliable. The mapping above is the authority.

**Sources:** Wolfram documentation for [GumbelDistribution](https://reference.wolfram.com/language/ref/GumbelDistribution.html) ("asymptotic distribution of the minimum value"; maximum is `ExtremeValueDistribution`) and [MinStableDistribution](https://reference.wolfram.com/language/ref/MinStableDistribution.html) (negative scaling gives `MaxStableDistribution`). The `MinStableDistribution` CDF above is derived from that identity; the documentation shows its formula only as an image. Empirical confirmation: in v0.1, Wolfram and the 50-digit reference agree to 5.0e-30 across all 72 arithmetic checks.

**Requirement:** confirm the mapping from the kernel itself, not from the documentation (see B-10).

---

## 5. Feeding production into the benchmark

Wolfram never sees code. It gets **specification**, **production inputs** and **production outputs**.

### A. Specification (written once, translated into Wolfram Language by hand)
- Distribution family and sign convention (Section 4).
- Estimator: maximum likelihood.
- Fitted quantity: per-storm peak levels per gauge, rounded to 4 dp (as persisted by the hazard io `_save`).
- Special rules: the Gumbel switch at |ξ| < 1e-10, force-Gumbel flags, minimum-n rules.
- **Return-period definition.** If production fits per-storm peaks, a 1-in-T level is per storm unless production converts it to annual using a storm rate λ, e.g. `P_annual = 1 − exp(−λ · p_storm)` under a Poisson arrival assumption. Wolfram must apply exactly the same conversion. **Open question Q-1.**

### B. Production inputs: a versioned, hashed snapshot
- Per gauge: the exact peak series fitted, n, and record length or storm count (if λ is used).
- The run config: return periods, thresholds, force-Gumbel flags.

### C. Production outputs to compare
- Per gauge: the fitted ξ, μ, σ as stored.
- The published return levels and hazard-curve points.
- Exceedance probabilities at the thresholds used downstream (e.g. PRS trigger levels).

### Export schema (proposed; extends `--gauges`)
```json
{
 "model_id": "MKM-GH-001",
 "code_commit": "<full 40-char>",
 "snapshot_sha256": "<full 64-char>",
 "return_periods": [10, 100, 200, 1000],
 "storm_rate_conversion": "none | poisson_annual",
 "gauges": {
  "<gauge_id>": {
   "peaks": [ ... ],
   "n_storms": 41,
   "record_years": 25,
   "force_gumbel": false,
   "fitted": {"xi": 0.18, "mu": 3.02, "sigma": 0.41},
   "return_levels": {"100": 0.0, "1000": 0.0},
   "exceedance": [{"x": 5.2, "p": 0.0}]
  }
 }
}
```

### Two tests per gauge
| Test | Wolfram input | Wolfram call | Compare with | Shows |
|---|---|---|---|---|
| Arithmetic | production `fitted` | `Quantile`, `SurvivalFunction` | production `return_levels`, `exceedance` | the formulae are computed correctly in production |
| Estimation | production `peaks` | `EstimatedDistribution`, then `Quantile` | production `fitted`, `return_levels` | the fit reaches the same maximum on real data |

**Gap today:** `--gauges` feeds only the estimation test. The arithmetic test still uses the synthetic `ORACLE_GEV_CASES`. It must also iterate over production's stored parameters (B-11).

---

## 6. Change backlog

Priority: **H** = blocks use as validation evidence; **M** = should fix before v1.0; **L** = tidy-up.

### Model under test — `src/models/hazard/gev.py`
| ID | Pri | Change | Reason |
|---|---|---|---|
| M-1 | M | Use `genextreme.isf(p)` / `.sf(x)` in place of `ppf(1 − p)` / `1 − cdf(x)` | Precision loss grows as p → 0 (about 1e-13 at T = 10,000; up to 9.7e-10 at T = 10^6). `isf` stays at about 1e-16. Removes the "beyond the operating range" caveat. |
| M-2 | M | Replace the |ξ| < 1e-10 Gumbel switch with a single `expm1`-based formula valid as ξ → 0 | It is the only non-machine-precision result (3.0e-11 level, 9.7e-10 exceedance at T = 10^6, just inside the 1e-9 tolerance). Removes a branch. |

### Benchmark tool — `tools/wolfram_oracle`
| ID | Pri | Change | Where |
|---|---|---|---|
| B-1 | H | Exit non-zero when any check fails. Today only a PDF build failure returns 1, so `--no-pdf` always returns 0. | `_run.py: finish`; `gev/run.py:79` |
| B-2 | H | Add `--require-wolfram`: fail if Wolfram is not run, rather than reporting "pending". | `gev/run.py`, `_run.py` |
| B-3 | H | Judge `ll_wolfram_vs_mp` (Wolfram LogLikelihood vs `loglik_mp`) as a seventh check. It is computed but never tested, and it is what validates the independent optimiser's objective. | `gev/fit.py:172`, `gev/latex.py: findings` |
| B-4 | H | Write the fitted series to `fit_data.csv`. Regeneration from seed 20261019 depends on numpy/scipy RNG versions. | `gev/run.py:76` |
| B-5 | M | Hash the exact bytes executed: `load_module` returns the sha256 of what it loaded, and that hash goes in provenance. Today the file is read twice, and the hash is taken after the run. | `gev/_code.py`, `_model.py` |
| B-6 | M | Emit the full sha256 and full commit hash in the macros; shorten for display only. | `gev/latex.py:102-103` |
| B-7 | M | Add the Gumbel-fit 1-in-1000 ratio range as its own macro (currently 0.59×–0.86× of true), alongside the GEV range. `_ratios()` filters to GEV only. | `gev/latex.py:83` |
| B-8 | M | Add `ORACLE_FIT_HEADLINE_T` in config. Remove the hard-coded `1000`, which raises KeyError if `ORACLE_FIT_CHECK_T` drops it. | `gev/latex.py:84, 156`; `config/models/_wolfram_oracle.py` |
| B-9 | M | Replicate study: run several hundred samples per (n, ξ) and report bias, spread and interval coverage of ξ̂ and x_1000. One draw per case does not measure sampling variation. | `gev/fit.py`, config |
| B-10 | M | Symbolic mapping check: `Simplify[CDF[MaxStableDistribution[μ,σ,ξ], x] − <spec>] == 0` and the same for `ExtremeValueDistribution`, recorded with `$Version`. | new group in `gev/` |
| B-11 | M | Arithmetic test over production parameters from the export (Section 5). | `gev/return_levels.py`, `gev/run.py` |
| B-12 | L | Carry pass/fail as booleans; stop matching the string `"FAIL"` in rendered LaTeX. | `gev/latex.py:90` |
| B-13 | L | Keep a fixed set of checks: show the Wolfram fit check as "pending" rather than dropping it. | `gev/latex.py: findings` |
| B-14 | L | Evaluate `EstimatedDistribution` once per row: `With[{d = EstimatedDistribution[…]}, {params, LogLikelihood[d, data]}]`. It currently runs twice. | `gev/fit.py: wl_items` |
| B-15 | L | Add a `\bmDataIsSynthetic` macro so the limitations section states the data source plainly. | `gev/latex.py: macros` |

### Benchmark document — `MKM-GH-001_wolfram_benchmark.tex`
| ID | Pri | Change |
|---|---|---|
| D-1 | H | Executive summary and limitations: state that a forced Gumbel understates the 1-in-1000 level when ξ > 0 (0.59× and 0.86× of true in Table 3). Uses B-7. |
| D-2 | M | Replace "1.02 to 4.46 times" (one draw per case) with replicate-study statistics from B-9. |
| D-3 | M | Show full hashes (B-6). |
| D-4 | M | Cite or define the Q8/Q9 validation framework. |
| D-5 | M | Eq. 3: add the ξ = 0 log-likelihood, −n log σ − Σ z_i − Σ e^(−z_i). |
| D-6 | M | §4.3: state that "LL gain W." uses machine-precision data, so it cannot resolve below about 1e-14. |
| D-7 | L | Replace "Unless a gauge export is named under Evidence…" with a plain statement driven by B-15. |
| D-8 | L | Legal notice: "Governed by the laws of England and Wales". The UK has no single legal system. |

### Methodology findings for Q9 (not in this benchmark's scope; record them)
- **Shape overshoot at small n:** ξ̂ = 0.66 (true 0.3, n = 50); ξ̂ = 0.71 (true 0.4, n = 30). ξ > 0.5 means infinite variance, which is implausible for flood peaks. Consider bounds on ξ or penalised MLE (Coles & Dixon), and document the choice.
- **Parameter uncertainty dominates:** add profile-likelihood or bootstrap intervals to `GEVFitter` outputs.
- **Gumbel by force vs by test:** use a likelihood-ratio test of ξ = 0, not a caller flag.
- **Per-storm peaks vs block maxima:** the GEV is the limiting law for block maxima. Justify per-storm fitting, or move to a peaks-over-threshold (GPD) model with a Poisson rate.

---

## 7. Acceptance criteria for v1.0 of the benchmark

1. All H items closed. The CLI exits non-zero on any failed check or missing Wolfram run (with `--require-wolfram`).
2. Every check in Table 1 has a tolerance and a boolean outcome. The set of checks is the same whether or not Wolfram ran.
3. Evidence directory contains: `.wl` scripts, `*_wolfram.json` with `$Version`, `return_levels.csv`, `fit.csv`, `fit_data.csv`, the PDF, and full code and data hashes.
4. A third party can replay the Wolfram leg with `wolframscript -file` and reproduce `*_wolfram.json` exactly.
5. The arithmetic and estimation tests run on a production export (Section 5), not only on synthetic cases.
6. The distribution mapping (Section 4) is confirmed symbolically by the kernel (B-10).

---

## 8. Open questions

| ID | Question | Owner |
|---|---|---|
| Q-1 | Does production convert per-storm return periods to annual ones? If so, how: λ estimate, Poisson assumption, record length? | David |
| Q-2 | Does the Wolfram Engine licence cover this use, or is a commercial licence needed? | David |
| Q-3 | Operating range: is T ≤ 10,000 the right limit for PRS pricing and capital use? | David |
| Q-4 | Production thresholds to include in the exceedance comparison (PRS triggers)? | David |

---

## 9. Reference values (for regression tests)

μ = 100, σ = 20 (50-digit reference, matches Wolfram):

| Case | ξ | T = 100 | T = 1,000 | T = 10,000 |
|---|---|---|---|---|
| gumbel | 0 | 192.002984535532 | 238.145101410474 | 284.205807397854 |
| frechet_moderate | 0.2 | 250.936528171716 | 398.067345230813 | 630.951034675384 |
| frechet_heavy | 0.5 | 458.997067605108 | 1324.59474401879 | 4059.89999708318 |
| weibull_bounded | −0.2 | 160.149285268038 | 174.878622625522 | 184.150909578673 |
