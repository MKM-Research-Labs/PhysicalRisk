# Satellite-Informed Bayesian Storm Modelling for Parametric Flood Risk Pricing
## A Proposal to the European Space Agency in Partnership with the National Physical Laboratory

**Submitted by:** MKM Research Labs / [Lead Applicant Organisation]
**In partnership with:** National Physical Laboratory (NPL)
**Funding alignment:** ESA FutureEO Programme · EC-ESA Earth System Science Initiative · HORIZON-CL6-2026-03-GOVERNANCE-01
**Date:** June 2026
**Classification:** Confidential — Pre-Submission Draft

***

## Executive Summary

This proposal seeks funding and scientific partnership from the European Space Agency (ESA) to develop a first-of-kind, satellite-driven Bayesian framework for continuously calibrating the storm intensity parameters that underpin the pricing of Physical Risk Swaps (PRS) — a parametric insurance instrument modelled on credit default swap architecture.

The Physical Risk Swap prices the cost of flood hazard protection at both asset level and gauge level. The difference between these two pricing surfaces is the **basis** — a measure of trigger risk that is the central challenge in parametric flood insurance. Currently, both surfaces are calibrated from static, historically derived parameters using a Hybrid Normal-Pareto storm intensity distribution. This stationarity assumption is a known and material limitation: it means that the PRS spread and payout trigger do not reflect evolving storm climatology driven by climate change.

This proposal addresses that limitation through two integrated innovations:

1. **Satellite-Informed Bayesian Parameter Evolution** — replacing static scenario parameters with a Bayesian updating framework in which ESA Copernicus satellite observations of real flood events continuously condition and evolve the four governing storm intensity parameters, anchored and constrained by UK government river gauge data.

2. **AI-Governed Parameter Attribution and Portfolio Impact Engine** — an artificial intelligence system that monitors parameter evolution, attributes change to its satellite-observable causes, and quantifies the downstream impact on every live PRS contract and the aggregate portfolio before any update is committed to production.

Together, these innovations make the full ESA Earth Observation archive financially actionable for the first time, and deliver a governance-grade, metrologically traceable pricing infrastructure for parametric flood risk transfer.

***

## 1. Problem Statement

### 1.1 The Parametric Flood Insurance Challenge

Parametric insurance pays a fixed, pre-agreed sum when a measurable physical event crosses an agreed threshold — automatically, without loss adjustment. For flood risk, the trigger is typically a river gauge level or a satellite-derived inundation extent at a defined location. This mechanism eliminates claims disputes and accelerates capital deployment to affected parties, making parametric instruments increasingly central to sovereign, municipal, and corporate flood risk management.

The Physical Risk Swap (PRS) extends this architecture using the modelling conventions of credit default swaps. The PRS calculates:

- **Asset-level pricing:** the cost of protection against flood damage to a specific physical asset, modelled from its exposure, vulnerability, and local hazard characteristics
- **Gauge-level pricing:** the cost of protection referenced to a specific river gauge trigger, modelled from storm intensity distributions and the gauge's hydrological response
- **The basis:** the spread between these two pricing surfaces, representing the residual trigger risk — the possibility that a flood damages the asset without breaching the gauge trigger, or vice versa

Basis risk is the central commercial and regulatory challenge of parametric flood insurance. A well-calibrated basis requires that both pricing surfaces reflect the same, current understanding of storm behaviour.

### 1.2 The Stationarity Problem

The PRS pricing engine is currently fed by the MKM Storm Intensity Distribution Model (MKM-SI-001), a Hybrid Normal-Pareto probability distribution governed by four parameters:

- **μ (base mean):** Controls the central tendency of storm intensity
- **σ (base standard deviation):** Controls the spread of typical events
- **u (tail threshold):** The intensity level above which extreme Pareto scaling engages
- **ξ (tail index):** Controls the heaviness of the extreme tail — the single most influential parameter for return-period intensities and therefore PRS pricing

These parameters are currently calibrated to a historical storm catalogue using maximum likelihood estimation (body) and Hill estimation (tail), then held constant within each of five pre-defined scenario families. The model documentation explicitly flags stationarity as a primary limitation: it does not account for climate change trends or decadal variability driven by ENSO, NAO, or AMO oscillations.

The consequence for PRS pricing is material:
- **Spread under-pricing** when storm climatology is intensifying — the tail index ξ is too high (thin tail), under-stating extreme event frequency
- **Trigger mis-calibration** when the threshold u does not reflect the gauge level distribution under current climate conditions
- **Basis mis-statement** when asset-level and gauge-level models diverge due to spatially heterogeneous shifts in storm behaviour that a single national parameter set cannot capture

### 1.3 The Data Opportunity

ESA's Copernicus programme provides, for the first time in history, a systematic, continuous, globally consistent archive of satellite observations capable of characterising individual storm events with sufficient fidelity to inform storm intensity distribution parameters. The Sentinel-1 SAR constellation — operating since 2014, cloud-penetrating, day-and-night capable — delivers observed flood extents within hours of inundation onset. The Copernicus Emergency Management Service (CEMS) Global Flood Monitoring (GFM) service produces near-real-time flood maps from every Sentinel-1 acquisition, providing a consistent, near-decade flood event catalogue.

Simultaneously, the UK National River Flow Archive (NRFA), operated by the UK Centre for Ecology and Hydrology, provides freely accessible, quality-controlled daily mean flow and peak flow data from over 1,600 gauging stations across the United Kingdom — precisely the gauge network that underpins PRS trigger calibration.

The scientific and commercial opportunity is to connect these two data streams — satellite-observed flood events and gauge-measured hydrological responses — through an AI-mediated Bayesian framework that continuously updates the PRS pricing parameters to reflect realised storm behaviour.

***

## 2. Proposed Solution

### 2.1 Conceptual Architecture

The proposed system operates as a closed-loop Bayesian calibration engine positioned between the ESA data infrastructure and the PRS pricing stack. Its operation can be described in five stages:

**Stage 1 — Event Detection**
Sentinel-1 SAR acquisitions are continuously monitored via the Copernicus Data Space Ecosystem (CDSE) API. When CEMS GFM produces a new flood extent product, an event is registered. The event is characterised by its spatial footprint, inundation area, onset rate, peak extent, and duration — all derivable from the time-sequential SAR archive using the Copernicus DEM for terrain context.

**Stage 2 — Intensity Scoring (the Hard Problem)**
The observed physical event must be placed on the MKM normalised intensity scale (0–100). This requires a **transfer function** that maps multi-dimensional physical observables (inundation area in km², duration in hours, rate of onset, spatial coherence across the catchment) to a scalar intensity score. This transfer function is the most scientifically challenging component of the system, and the primary locus of NPL's metrological contribution. The function must:
- Produce a traceable, uncertainty-quantified intensity score with defensible confidence intervals
- Be consistent with the existing MKM model's intensity scale so that updates are compatible with the established pricing architecture
- Be anchored by concurrent NRFA gauge observations, which provide an independent physical measurement of flood severity at the trigger point

**Stage 3 — Bayesian Parameter Update**
The intensity score, together with its uncertainty, is used to update the four governing parameters using Bayesian inference. The current parameter set constitutes the prior; the observed intensity score provides the likelihood; the posterior becomes the updated parameter set for the next pricing cycle. This approach is well-established in extreme value hydrology — hierarchical Bayesian GEV frameworks have demonstrated superior flood quantile estimation compared to classical methods, particularly for constraining tail behaviour with limited data.

The update is **event-triggered**, not time-scheduled: parameters evolve in response to observed reality, not the passage of calendar time. Between events, the parameters remain stable. This design preserves the governance integrity of the Tier 1/2 model chain while ensuring that material new information is incorporated promptly.

**Stage 4 — Gauge Constraint**
NRFA gauge data serves a dual role. First, it acts as a **likelihood constraint** on the Bayesian update — if the satellite-derived intensity score implies a 1-in-50-year event but the gauge record indicates a 1-in-10-year event at the relevant station, the update is moderated accordingly. Second, it provides a **direct calibration anchor** for the gauge-level PRS pricing surface, ensuring that the asset-level and gauge-level models remain coherently coupled. This is the mechanism by which basis risk is most directly controlled.

**Stage 5 — Impact Attribution and Portfolio Governance**
Before any updated parameter set is committed to the live PRS pricing engine, the AI attribution system computes the full downstream impact across the model chain: Storm Intensity Distribution → Storm-Gauge Forward Model → GEV Hazard Curve Builder → PRS Pricing Engine. For every live PRS contract, the system produces a delta report showing the change in spread, trigger probability, and expected payout under the proposed updated parameters. The aggregate portfolio net present value change is computed and presented to the governance function for review. Only upon human approval is the update committed.

### 2.2 Workstream Structure

The project is organised into three sequential, interdependent workstreams:

***

**Workstream 1 — Transfer Function Development and Metrological Calibration**

*Objective:* Construct a validated, traceable transfer function mapping ESA satellite observables to the MKM intensity scale, constrained by NRFA gauge data.

*Activities:*
- Ingest the Sentinel-1 GRD archive (2014–present) from CDSE for UK flood catchments, using the S3 and openEO APIs for cloud-native processing at NPL compute infrastructure
- Extract flood event catalogues using CEMS GFM products as the primary detection layer, supplemented by independent Sentinel-1 backscatter change detection
- Characterise each detected event across five physical dimensions: peak inundation extent, total inundation volume (derived with Copernicus DEM EEA-10), event duration, onset rate, and catchment spatial coherence
- Match each satellite-detected event to concurrent NRFA peak flow and gauge level observations at co-located stations, constructing a paired satellite-gauge event dataset
- Train and validate the AI transfer function — mapping the five-dimensional physical feature vector to a scalar intensity score with calibrated uncertainty — using NPL metrological standards for uncertainty propagation
- Validate the transfer function against the existing MKM historical scenario calibration (μ=40, σ=12, u=60, ξ=3.0) to ensure scale consistency

*Key output:* A validated, governance-ready transfer function with traceable uncertainty bounds, certified by NPL as fit for use in a Tier 2 pricing model.

***

**Workstream 2 — Bayesian Parameter Evolution Engine**

*Objective:* Implement and validate the Bayesian updating framework that evolves the four MKM parameters in response to observed events.

*Activities:*
- Establish the Bayesian prior from the existing five MKM scenario families, treating the historical scenario as the initial prior distribution over (μ, σ, u, ξ)
- Define the likelihood function for each parameter, informed by the transfer function output from WS1 and the NRFA gauge constraint
- Implement the posterior update using Markov Chain Monte Carlo (MCMC) sampling, consistent with established Bayesian GEV frameworks for flood frequency analysis
- Test the update mechanics against a held-out set of known UK flood events (e.g. 2019–20 England floods, 2021 Yorkshire flooding) to verify that the Bayesian updates move parameters in physically meaningful directions
- Define and implement governance gates: criteria for classifying an update as material (requiring human review) versus immaterial (logged but not propagated), informed by the model's existing sensitivity analysis showing that ξ changes near 1.0 have non-linear, amplified effects
- Produce a new extended scenario family — a **Dynamic Climate Scenario** — that represents the current posterior parameter distribution as a living, updatable member of the MKM scenario family table

*Key output:* A functioning Bayesian update engine integrated with the MKM Storm Intensity Distribution Model, with documented governance triggers and a validated update audit trail.

***

**Workstream 3 — AI Attribution and Portfolio Impact Engine**

*Objective:* Build the AI system that quantifies the downstream PRS portfolio impact of each proposed parameter update and supports the governance review workflow.

*Activities:*
- Instrument the full MKM model chain (MKM-SI-001 → MKM-STORM-002 → MKM-HAZARD-001 → MKM-PRS-001) to accept parameter perturbations and propagate them to PRS contract-level outputs
- Develop the attribution engine: for any proposed (Δμ, Δσ, Δu, Δξ), compute the partial derivatives of spread, trigger probability, and expected payout with respect to each parameter, attributing total impact to its constituent drivers
- Implement the portfolio delta report: for each live PRS contract, report the change in mark-to-market value, change in spread, change in trigger exceedance probability, and change in expected payout under the proposed updated parameters
- Build the governance workflow interface: present the attribution report and portfolio delta to the approving authority with sufficient context (event summary, satellite evidence, gauge data) for an informed decision; log all approvals and rejections for regulatory audit trail
- Design and implement the model monitoring dashboard: track the evolution of (μ, σ, u, ξ) over time, alert when parameters drift beyond predefined bands relative to the scenario family ladder, and flag any parameter combination that approaches the ξ < 1.5 region where the distribution has infinite variance

*Key output:* A production-grade AI attribution and governance engine, integrated with the PRS platform, capable of processing parameter updates within the existing Tier 1/2 model risk governance framework.

***

## 3. Data Architecture

### 3.1 Primary ESA Data Stack

| Data Layer | Source | Access Method | Role |
|-----------|--------|---------------|------|
| Sentinel-1 GRD (COG_SAFE) | Copernicus Data Space Ecosystem | S3 / openEO API | Event detection, flood extent characterisation |
| Copernicus DEM EEA-10 (10 m) | CDSE | S3 | Inundation volume estimation, flow routing |
| CEMS GFM Products | CEMS Early Warning Data Store | REST API | Primary flood event catalogue, detection benchmark |
| Sentinel-2 L2A | CDSE | STAC / openEO | Pre-event land cover, optical validation (clear sky) |
| Copernicus Land Monitoring — Imperviousness | land.copernicus.eu | WCS | Urban runoff characterisation for catchment context |

All ESA data is available free of charge under the Copernicus open data policy following registration. The cloud-native CDSE infrastructure, holding over 78 petabytes of immediately accessible data, enables processing at scale without bulk data transfer, using the openEO API for server-side computation.

### 3.2 UK Government Gauge Data

| Data Layer | Source | Access Method | Role |
|-----------|--------|---------------|------|
| Daily mean flow | NRFA API (CEH) | REST API / CSV | Gauge constraint on Bayesian update |
| Peak flow dataset | NRFA API (CEH) | REST API / WINFAP | Flood frequency baseline for prior calibration |
| Near-real-time gauge levels | Environment Agency API | REST API | Live trigger monitoring for PRS event detection |

The NRFA API provides freely accessible daily mean flows, catchment daily rainfall, and peak flow data from over 1,600 UK gauging stations in JSON or CSV format. This data is openly licensed under Open Government Licence.

### 3.3 Data Flow Diagram

```
┌─────────────────────────────┐    ┌──────────────────────┐
│   ESA COPERNICUS (CDSE)     │    │  UK GAUGE NETWORK    │
│                             │    │                      │
│  Sentinel-1 GRD (SAR)       │    │  NRFA API            │
│  Copernicus DEM EEA-10      │    │  (1,600 stations)    │
│  CEMS GFM Flood Maps        │    │  EA Real-Time API    │
│  Sentinel-2 L2A             │    │                      │
└─────────────┬───────────────┘    └──────────┬───────────┘
              │                               │
              └──────────────┬────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │   WS1: AI TRANSFER FUNCTION  │
              │   (NPL Metrological Layer)   │
              │                              │
              │  Physical observables →      │
              │  Intensity score [0–100]     │
              │  + uncertainty bounds        │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  WS2: BAYESIAN UPDATE ENGINE │
              │                              │
              │  Prior: current (μ,σ,u,ξ)    │
              │  Likelihood: intensity score │
              │  + gauge constraint          │
              │  Posterior: updated (μ,σ,u,ξ)│
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  WS3: ATTRIBUTION ENGINE     │
              │                              │
              │  MKM-SI-001 (Storm Intensity)│
              │       ↓                      │
              │  MKM-STORM-002 (Gauge Fwd)   │
              │       ↓                      │
              │  MKM-HAZARD-001 (Haz. Curve) │
              │       ↓                      │
              │  MKM-PRS-001 (PRS Pricing)   │
              │       ↓                      │
              │  Portfolio Delta Report      │
              │  → Governance Review         │
              │  → Commit / Reject           │
              └──────────────────────────────┘
```

***

## 4. The NPL Partnership

The National Physical Laboratory's role in this project is not ancillary but foundational. NPL is the UK's National Measurement Institute — the authority on measurement science, calibration, and uncertainty quantification. Its involvement is essential for three reasons:

**Metrological rigour on satellite inputs.** The transfer function that maps satellite observables to the MKM intensity scale is the point at which physical measurement uncertainty enters the pricing chain. An error here propagates through every downstream model in the chain and manifests as mispriced PRS contracts. NPL's expertise in traceable uncertainty quantification — applying SI-traceable measurement standards to remote sensing data — provides the defensible, auditable calibration that a Tier 2 model feeding regulated outputs requires.

**Data science and computational capability.** NPL provides the data scientist resource for model development, validation, and implementation across all three workstreams. This includes the AI transfer function, the MCMC Bayesian update implementation, and the attribution engine. NPL's compute and storage infrastructure supports the large-scale ESA data ingestion required for the UK event catalogue construction.

**Independent validation.** As a national laboratory operating under government mandate, NPL provides a level of independent scientific validation that strengthens the model's governance case. Annual parameter recalibration — already mandated by the MKM model governance framework — gains materially in credibility when the calibration methodology bears NPL certification.

***

## 5. Alignment with ESA Priorities

### 5.1 FutureEO — Earth Action Pillar

This project directly instantiates ESA's Earth Action ambition: translating satellite data into tangible societal and economic decisions. The PRS is a financial mechanism for flood risk transfer — making flood protection economically accessible and efficiently priced. Better-priced parametric insurance instruments accelerate capital deployment to flood-affected communities and assets, reducing the protection gap that represents one of the most significant economic consequences of climate change.

### 5.2 EC-ESA Earth System Science Initiative — HORIZON-CL6-2026

This proposal aligns directly with the open Horizon Europe call HORIZON-CL6-2026-03-GOVERNANCE-01: *"Develop Earth Intelligence solutions using environmental observations and state-of-the-art AI for sustainable competitiveness and policy making"*. Specifically:

- **Intensive use of Copernicus EO data:** Sentinel-1 SAR, Copernicus DEM, and CEMS GFM are the primary data inputs throughout all three workstreams
- **AI-driven decision support tools for private actors:** The PRS pricing engine and attribution system directly serve financial institutions, insurers, and corporate treasuries managing flood exposure
- **Co-design with end-users:** The PRS platform operator (project lead) is an end-user co-designer, ensuring fit-for-purpose outputs from the first workstream
- **Explainability and robustness:** The Bayesian attribution architecture provides explicit, auditable explanations for every parameter change and its portfolio consequences
- **Collaboration with ESA FutureEO:** The project explicitly builds on and extends the CEMS GFM service and the Copernicus Data Space Ecosystem infrastructure, with commitment to ESA FutureEO coordination activities
- **Stage 2 deadline:** 30 September 2026

### 5.3 ESA Phi-Lab UK — Environmental Sustainability Pillar

The project also aligns with ESA Phi-Lab UK Pillar 1: Fight climate change with space technology. Parametric flood insurance priced on satellite-derived, climate-evolving storm parameters is a direct commercial application of space technology to climate adaptation. Phi-Lab UK offers funding of €200,000–€225,000 per project for UK-based applicants from private organisations, research institutions, and academia, with NPL and the project lead constituting an eligible UK-based consortium.

***

## 6. Innovation and Novelty

This project is novel across three dimensions:

**Scientific novelty.** While Bayesian GEV frameworks for flood frequency analysis are established in hydrology, their application to the continuous, event-triggered calibration of a parametric pricing model parameter set — specifically using the Hybrid Normal-Pareto intensity scale of the MKM architecture — has not been demonstrated. The integration of SAR-derived flood observables as the likelihood function in such an update represents a genuinely new methodological contribution.

**Commercial novelty.** The use of Earth Observation data as a dynamic input to a structured financial product's pricing engine — rather than solely as a payout trigger — is a frontier application of satellite data in capital markets. The PRS basis quantification enabled by co-registered satellite and gauge observations represents a step-change in parametric flood pricing precision.

**Governance novelty.** The AI attribution engine — which quantifies the downstream portfolio impact of satellite-informed parameter changes before they are committed — establishes a new standard for model risk governance in EO-informed financial applications. The architecture explicitly preserves the Tier 1/2 governance hierarchy of the existing MKM model framework, demonstrating that satellite-driven dynamism and financial regulatory compliance are not in tension.

***

## 7. Known Limitations and Risk Mitigations

| Limitation | Mitigation |
|-----------|------------|
| Transfer function uncertainty: mapping physical observables to the normalised [0–100] scale involves irreducible modelling judgement | NPL metrological framework provides traceable uncertainty bounds; Bayesian update propagates this uncertainty into parameter posteriors rather than treating the score as exact |
| Sentinel-1 archive length (from 2014): ~12 years is insufficient to independently estimate decadal or centennial return periods | NRFA peak flow archive (from 1960s at many stations) constrains long-return-period tail behaviour; the Bayesian prior from the existing MKM historical scenario encodes pre-satellite climatological knowledge |
| Independence assumption in the storm intensity model: temporal clustering of storm events is not captured in the current MKM architecture | WS2 Bayesian update operates on individual event observations; cluster sequences are characterised using the storm sequence parameters documented in test results (MKM-SS-001) |
| UK-focus of NRFA gauge data: limits immediate applicability to UK PRS portfolios | Initial scope is explicitly UK; extension to European gauge networks (EuroWQMS, GRDC) is a future phase deliverable |
| Stationarity of the transfer function itself: the satellite-to-intensity mapping may itself evolve | Annual recalibration of transfer function parameters is included in the project governance cycle, consistent with existing MKM annual review |

***

## 8. Deliverables and Indicative Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **Phase 1** — Foundation | Months 1–6 | ESA data pipeline (CDSE S3 + openEO); UK flood event catalogue (2014–2025); NRFA gauge matching dataset; transfer function prototype |
| **Phase 2** — Calibration | Months 7–12 | NPL-certified transfer function v1.0; Bayesian prior specification; historical back-test of update mechanics against 2019–2024 UK flood events |
| **Phase 3** — Integration | Months 13–18 | Bayesian update engine integrated with MKM-SI-001; Dynamic Climate Scenario family; governance gate definitions |
| **Phase 4** — Attribution Engine | Months 19–24 | AI attribution engine; portfolio delta reporting; full model chain instrumentation; governance workflow interface |
| **Phase 5** — Validation & Handover | Months 25–30 | Independent validation report (NPL); regulatory documentation for Tier 2 model re-approval; publication of methodology |

***

## 9. Partnership Summary

| Party | Contribution | Role |
|-------|-------------|------|
| **MKM Research Labs / Project Lead** | Domain expertise in PRS pricing architecture; PRS platform development and integration; model chain instrumentation; project direction | Principal Investigator; end-user co-designer |
| **National Physical Laboratory (NPL)** | Data science capability; metrological calibration of transfer function; uncertainty quantification; compute and storage infrastructure; independent validation | Scientific Partner; metrological authority |
| **ESA / Copernicus** | Sentinel-1 SAR data; Copernicus DEM; CEMS GFM products; CDSE cloud infrastructure; scientific guidance | Data and infrastructure partner |
| **NRFA / UKCEH** | UK river flow and peak flow archive; real-time gauge data access | Data provider (open licence) |

***

## 10. Conclusion

The convergence of ESA's systematic satellite observation programme, the UK's world-class river gauge network, and advances in Bayesian inference and AI attribution creates a unique opportunity to build a new generation of climate-responsive parametric flood pricing instruments.

The Physical Risk Swap — already a sophisticated financial engineering achievement modelled on credit default swap architecture — has a clear and addressable limitation: its governing storm intensity parameters do not evolve in response to observed reality. This proposal provides the scientific framework, the data infrastructure, and the governance architecture to close that gap.

By making the ESA Copernicus archive financially actionable through metrologically rigorous AI, this project delivers direct ESA societal impact through improved flood risk transfer, advances the scientific state-of-the-art in Bayesian EO-to-parameter calibration, and establishes a replicable governance model for satellite-informed financial products that will extend far beyond flood risk.

The project is ready to proceed. The model architecture is established, the data infrastructure is in place, and the partnership between domain expertise (MKM Research Labs), measurement science (NPL), and satellite data (ESA) is uniquely configured to deliver this outcome.