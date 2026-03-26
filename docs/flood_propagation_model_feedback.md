<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# This is a write up of a piece of functionality that describes how a flood at a couple of gauges enables the water to move across the terrain towards the property. We have been having issues with getting flood events to happen.  Can you use the latest version of the book 210 to check whether the rationale is correct and if not suggest improvements.

Your overall pipeline (gauges → interpolation → distance decay → elevation check → hydrograph → damage) is directionally consistent with the “gauge-to-property” logic in the latest Book 210 text, but two key pieces of the rationale are out of line with the book and are almost certainly contributing to “no events” at properties: the way you (a) average gauges and (b) handle propagation/retention.[^1_1][^1_2]

Below I’ll focus on what the book implies you *should* be doing around those two points, and concrete changes.

***

## 1. Conceptual alignment with Book 210

Book 210’s view of gauge→property hazard can be summarised as:[^1_2]

- Start from physically or statistically robust **gauge-level flood frequency / extreme value curves** (GEV / Gumbel) at each gauge.[^1_2]
- Use hydraulically meaningful **routing / floodplain models** (Muskingum‑Cunge, 1D/2D Saint‑Venant, or at least DEM-based flow paths) to propagate that hazard across terrain.[^1_2]
- Treat **property positioning** (elevation, flow paths, connectivity, micro‑topography) as the core determinant of whether that hazard reaches the asset.[^1_2]

Your model ticks the first and last boxes (GEV at gauges, explicit property elevation/thresholds) but uses a very simplified and partly inconsistent treatment of the “in‑between” propagation (IDW + simple exponential retention), whereas the book pushes you toward flow‑aligned propagation and very light damping over a few hundred metres.[^1_1][^1_2]

***

## 2. Issues in your current rationale

### 2.1 IDW across multiple gauges

- IDW of WSE from three gauges assumes the *true* water surface at the property is a weighted average of all three, which is not how a river or tidal reach behaves.[^1_1][^1_2]
- Book 210 explicitly flags that hydrology/hydraulics should respect **flow connectivity and direction**, not isotropic spatial averaging; it recommends Muskingum‑Cunge routing along reaches or 1D/2D Saint‑Venant for floodplains, and DEM‑based flow paths for pluvial routing.[^1_2]
- You’ve already observed IDW “dilution” (one high gauge + two low gauges → unrealistically low interpolated WSE, leaving many properties dry).[^1_1]

**Implication:** The “178/200 properties unflooded” behaviour is consistent with the book’s critique of naive spatial averaging; your rationale that IDW is an acceptable surrogate for hydraulic propagation is *not* supported by the book and should be revised.[^1_1][^1_2]

### 2.2 Distance-based retention

- You apply a distance-decay factor `exp(−d/L)` with L = 10 km to water height above the gauge, even for properties a few hundred metres away.[^1_1]
- For fluvial/tidal flooding in near‑field (≤ 1–2 km along the same reach), Book 210 treats attenuation primarily via hydraulic routing (wave celerity, storage, roughness), not as simple exponential loss in stage.[^1_2]
- For your worked example (636 m), the factor is 0.94, which you rightly interpret as “negligible loss,” so in practice this isn’t your main problem.[^1_1]
- But conceptually it’s double‑counting with the Manning‑based travel time (you both attenuate and separately compute a very fast travel time), whereas the book treats wave speed and attenuation together inside the routing/hydraulic module.[^1_2][^1_1]

**Implication:** The retention term is not consistent with the more physically grounded routing described in the book; at best it’s redundant, at worst it interacts badly with IDW to reduce flood transmission.

### 2.3 Mixing vertical and horizontal logic

- Your threshold logic is sound (prop elevation – gauge elevation + floor step) and aligns with the property‑positioning emphasis in the book.[^1_1][^1_2]
- The part that’s weak is the purely horizontal “distance” treatment that ignores actual **flow paths, barriers, and DEM‑derived connectivity**, which Book 210 emphasises via 2D surface routing and microtopography.[^1_2]

***

## 3. Concrete improvements to bring it in line

### 3.1 Replace multi-gauge IDW with flow-aligned gauge selection

Instead of averaging three gauges:

- For **fluvial/tidal** flooding:
    - Identify the **hydraulic reach** for each property using river network topology (or, minimally, nearest river line and along‑channel distance).[^1_2]
    - Use **one primary gauge per reach** (plus maybe an upstream/downstream pair for consistency checks), and treat its stage as the controlling boundary condition for that reach.[^1_2]
    - If you must interpolate, do it **along the river centreline** (1D routing) or on a precomputed 2D water‑surface from a hydraulic model, not isotropic IDW.[^1_2]
- For your existing implementation:
    - Short term: change **Stage 2** so that, for river floods, you simply take the **nearest hydraulically connected gauge** (synthetic or real) and drop the other two from the interpolation for that property.[^1_1][^1_2]
    - Keep the synthetic gauge as you do now, but treat it as the single effective gauge for the local reach (no averaging).[^1_1]

This aligns with Book 210’s “gauge-based triggering system” and “property positioning analysis” where distance and connectivity from a specific river source are what matter, not an average across multiple sources.[^1_2]

### 3.2 Replace generic retention with simple hydraulic / DEM routing

Book 210 proposes three tiers of increasing sophistication for propagation:[^1_2]


| Tier | Method | When to use |
| :-- | :-- | :-- |
| 0 | Direct gauge stage → floodplain depth via precomputed maps | If you have 1D/2D model outputs or vendor hazard grids |
| 1 | 1D hydrologic / hydraulic routing (Muskingum‑Cunge / 1D Saint‑Venant) | Along river channels between gauges and local cross‑sections |
| 2 | 2D shallow‑water (coupled 1D–2D) | For complex floodplains / urban areas |

Recommended changes for your case:

- **Short term (no new hydraulics):**
    - Drop the `exp(−d/L)` attenuation for fluvial/tidal where property is within, say, 1–2 km along the same reach; treat stage as **conserved** over that distance, and rely on elevation differences only.[^1_1][^1_2]
    - Use the DEM to ensure the property is actually **downhill and connected** to the river (simple flow‑direction / flow‑accumulation check). If not connected, force no fluvial flood and reserve that hazard for pluvial/groundwater modules.[^1_2]
- Medium term (consistent with Book 210):
    - Precompute a **lookup table** (or raster) of water depth at each terrain cell for a small set of gauge stages (e.g., severe threshold, +0.5 m, +1 m), using a 1D–2D or at least pond‑fill algorithm over your DEM.[^1_2]
    - At run time, map each simulated gauge peak to the nearest precomputed surface, then read off depth at the property location. This is exactly the kind of hybrid the book advocates as a pragmatic compromise between full Saint‑Venant and simple screening.[^1_2]


### 3.3 Keep the elevation / threshold logic, but clarify event definition

Your current threshold logic is fine and consistent with the book:[^1_1][^1_2]

- Flood if \$ water\_at\_property > (prop\_elev - gauge\_elev) + floor\_step \$.[^1_1]

Improvements:

- Explicitly treat **different flood types**:
    - Fluvial/tidal: driven by river stage at connected gauges.
    - Pluvial: driven by local intensity‑duration rainfall and DEM‑based ponding.
    - Groundwater/drainage: via separate modules if needed.[^1_2]

This matches Book 210’s multi‑hazard framing (fluvial, pluvial, groundwater, infrastructure) and avoids having one imperfect river‑only mechanism stand in for all flood mechanisms.[^1_2]

***

## 4. Likely immediate “bug-fix” changes

Given your current code and the book’s guidance, the minimal change set to make floods actually happen more plausibly would be:[^1_1][^1_2]

1. **Turn off multi-gauge IDW for river floods**
    - Use only the nearest hydraulically connected gauge (or the synthetic local gauge) per property.
2. **Disable or cap distance retention for near-field**
    - For `d < 2 km` on the same reach, set retention = 1 for fluvial/tidal; keep it only for genuinely downstream routing over many km if you don’t yet have Muskingum‑Cunge.[^1_1][^1_2]
3. **Add a simple DEM connectivity check**
    - Confirm that a monotone downhill path exists from the river cell near the gauge to the property; if yes, allow fluvial flood; if not, require pluvial/other modules.[^1_2]

Those three steps keep almost all of your existing machinery, but align the physical logic much more closely with the hydrology/hydraulics rationale in Book 210 and should materially increase the number of properties that flood when gauges clearly indicate a severe event.[^1_1][^1_2]

If you like, I can next help translate this into specific pseudocode or refactor suggestions for the `spatial.py` and `flood.py` functions.

<div align="center">⁂</div>

[^1_1]: flood_propagation_model.md

[^1_2]: Weather-Patterns-to-Physical-Risk-Swaps-Edition2.txt

