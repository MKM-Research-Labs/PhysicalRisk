# PRS regulatory characterisation — questions for an owner outside the model team

**Raised:** 2026-10-09, WP0 of the PRS XVA model (MKM-XV-001, `project_plan.md`).
**Needed by:** before any KVA figure is used in a price (WP3).
**Owner:** to be named, from Regulatory Policy, Compliance or Legal. This is not a model choice.

## Why it matters

KVA is the cost of the regulatory capital a trade consumes. For a PRS, that capital
depends on three answers the model team cannot give. Depending on the answers, the
counterparty-risk capital could be a few basis points or a material share of the
spread. The XVA model will compute every alternative, but it cannot choose between them.

The instrument is like a single-name CDS with a flood trigger in place of the credit event:
- The buyer pays a running spread.
- The seller pays the full notional (recovery 0) when a named river gauge passes the severe level.
- The trade is cash-settled and parametric: there is no proof of loss and no insurable-interest test.
- Tenors are 1–5 years; notionals are GBP 5–20m.

## Questions

**Q1. Is a PRS a derivative or an insurance contract?**
- Being parametric points to a derivative. A weather derivative is the closest analogue.
- Being sold to property owners as flood protection points to insurance.
- If it is insurance, the bank may not be allowed to write it at all. If it may, none of SA-CCR, BA-CVA or FRTB applies.

**Q2. If it is a derivative, which SA-CCR asset class applies?**

| candidate | supervisory factor | effect |
|---|---|---|
| Commodity, "other" (climatic or weather underlyings) | 18% | Add-on ≈ 18% × adjusted notional × maturity factor |
| Credit, single name (by analogy with a CDS) | rating-based (0.38%–6%) | Needs a "rating" for a flood trigger, which has no obvious meaning |
| Something else, by supervisory agreement | — | — |

The choice also decides whether the BA-CVA charge treats the counterparty under its own sector risk weight.

**Q3. Does the FRTB residual-risk add-on apply?**
- If PRS trades are in the trading book, natural-disaster and weather underlyings are among the exotic underlyings that attract the RRAO, at 1% of gross notional.
- On a GBP 10m trade that is GBP 100k of own-funds requirement before any other charge, and it applies to both the PRS and any offsetting hedge.
- Banking-book treatment would avoid it, but would raise its own questions.

**Q4. Is the trade eligible for close-out netting and collateral recognition** under the ISDA 2002 Master and a CSA?
- The new CDM fields (`CreditSupport.NettingSets`) assume it is.
- If it is not, every trade is its own netting set and collateral cannot reduce EAD.

## What the model will do meanwhile

- KVA is computed under each answer to Q2 and Q3, with the RRAO as a switch.
- All KVA figures stay ILLUSTRATIVE.
- Nothing from KVA reaches the all-in spread until this paper has an owner and a signed answer.
