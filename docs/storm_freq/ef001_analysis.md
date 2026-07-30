# MKM-EF-001 — Analysis

**Component:** Event Frequency Model — `MKM-EF-001` (governance record v1.1.0)
**Scope:** Empirical analysis of the model's measured behaviour on the halong
catchment — the reprice it produces, the population-coverage correction, the
dispersion regime, and the defects surfaced and fixed during construction.
**Date:** 2026-07-28.

---

## 1. The problem the model corrects

The platform previously priced PRS off `flood_count / num_storms` — a
conditional probability with no time dimension, equivalent to setting the event
arrival rate λ = 1 ("one storm = one year"). The Event Frequency Model supplies
the missing rate: it counts *events* (storm sequences inside the 168-hour hours
clause) and annualises the per-event flood conditional as `1 − exp(−λ·p)`.

## 2. Measured reprice

On halong the annualisation reprices **downward, 0.35–0.56×** the legacy metric.
The severe-flood return period moves from the pre-frequency 8-10 years to 15-22
years; a representative property spread moves ~1100 to ~590 bps. The direction is
not obvious a priori — during development it reversed twice as defects were
found — so the figure is quoted only against the settled mechanism.

## 3. Population-coverage correction

The stress catalogue MKM-SS-001 oversamples severe events (it exists to train the
classifier) and holds no minimal/baseline events at all, though those carry ~73%
of the population mass. Naively resampling it answers *P(flood | event is at
least moderate)*, not *P(flood | event)*. The model reweights the catalogue with
population weights (8% severe-or-worse, owner judgement) and scales the
conditional by the catalogue **coverage**, so events absent from the catalogue
count at zero rather than being renormalised onto the severe tail. Left
uncorrected, a configured 8% severe share read as an effective 29.6% — a 3.7×
overstatement.

## 4. Dispersion regime

The per-gauge chi-square dispersion test finds halong's annual event counts
**under-dispersed** (dispersion index ~0.46–0.97). No family on the
Poisson–Negative-Binomial axis represents under-dispersion below the Poisson
variance floor, and on synthetic data it is a declustering artefact rather than a
physical regularity, so it is flagged and Poisson is selected as the nearest
fittable family. The distributional form is in any case a second-order
sensitivity (see the sensitivity analysis).

## 5. Defects surfaced and fixed

Building the model exposed five pre-existing platform defects, each corrected:

1. **Unseeded gauge response model** — every hazard curve the platform produced
   was irreproducible at ±40%; now seeded per gauge and per (gauge, storm).
2. **Catalogue coverage** (as §3) — the 3.7× tail overstatement.
3. **Two field-naming traps** — `flood_events[].storm_id` holds *sequence* ids;
   `num_storms` was actually the sequence count. Both produced confident wrong
   answers.
4. **A units error in the basis leg** — an annual probability multiplied by an
   event count produced transmission rates near 200% (bounded by 1).
5. **Five missing BRI ratings** on commercial assets.

## 6. What the analysis does not establish

The measured reprice rests on the **unvalidated λ**. On a synthetic catchment
the gauge record is generated from an assumed frequency, so the model recovers
its own input; the per-gauge extraction validates the extraction code, not the
rate. The λ sensitivity analysis shows the book inherits λ's uncertainty roughly
one-for-one, so the reprice magnitude is only as trustworthy as λ's level — which
requires real gauge data to validate (plan §5).

---

*Reproduce: `python app.py port --halong --all` then the propertyhc / gaugehc
outputs; measured figures from the halong build of 2026-07-28.*
