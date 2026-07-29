# PhysicalRisk Platform

A flood risk modelling and pricing platform for mortgage and property portfolios, developed by MKM Research Labs. The platform models physical climate risk across catchment areas, generates synthetic portfolio data, prices Physical Risk Swaps (PRS), and produces regulatory-grade audit evidence.

---

## Getting Started

### 1. Clone and Install

```bash
git clone https://github.com/MKM-Research-Labs/PhysicalRisk.git
cd PhysicalRisk
```

Python 3.11 or later is required (3.13 recommended). Download from:

```
https://www.python.org/downloads/
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Generate Portfolio Data

The repository does not include generated data. All data directories are created automatically on first run. Generate the full portfolio:

```bash
python3 phys.py port --all
```

This takes approximately 30–60 minutes depending on hardware. To skip the multi-storm stress test and get running faster:

```bash
python3 phys.py port --all --nostress
```

The platform is fully functional without the stress test — see [Flood Probability Fallback](#flood-probability-fallback) below.

### 3. Verify Data Integrity

```bash
python3 phys.py test --audit
```

### 4. Generate the Visualisation

```bash
python3 phys.py visual
```

This produces a folium HTML map and opens it in the default browser. To generate without opening:

```bash
python3 phys.py visual --no-browser
```

### 5. Start the Server

```bash
python3 phys.py server
```

The server runs on `http://127.0.0.1:5013`. Options:

```bash
python3 phys.py server --host 0.0.0.0 --port 8080 --debug
```

---

## Port Pipeline Reference

### Pipeline Steps

The full `--all` pipeline runs the following steps in order:

| Step | Flag | Output |
|---|---|---|
| 1 | `--gauges` | `gauge.json` — 52 real gauge locations |
| 2 | `--properties` | `property.json` — synthetic property portfolio |
| 2.5 | *(automatic)* | Synthetic gauges — virtual gauges on river centreline nearest each property |
| 3 | `--mortgages` | `mortgage.json` — mortgage book |
| 4 | `--gaugehd` | `gaugehd/` — per-gauge historical daily data |
| 5 | `--stressm` | `storm_sequences.json`, `gaugets/`, `sequence_gauge/` — 20,000 multi-storm sequences |
| 6 | `--hazard` | `gaugehc.json` — GEV/Gumbel hazard curves per gauge |
| 7 | `--propertyts` | `propertyts/` — per-property flood time series |
| 8 | `--propertyhc` | `propertyhc.json` — property hazard curves + PRS pricing |
| 9 | `--counterparties` | `counterparty.json` |
| 10 | `--blotter` | Trade PDFs + 3 months of EOD snapshots |

### Segment Flags

Run individual segments instead of the full pipeline:

| Segment | Flag | Short |
|---|---|---|
| Flood gauges | `--gauges` | `--ga` |
| Properties | `--properties` | `--pr` |
| Synthetic gauges | *(runs automatically after properties)* | — |
| Mortgages | `--mortgages` | `--mo` |
| Gauge historical data | `--gaugehd` | `--hd` |
| Gauge time series | `--gaugets` | `--gt` |
| Multi-storm sequences | `--stressm` | — |
| Hazard curves | `--hazard` | `--hz` |
| Property flood time series | `--propertyts` | `--pt` |
| Property hazard curves | `--propertyhc` | `--phc` |
| Counterparties | `--counterparties` | `--ctpy` |
| Trading blotter | `--blotter` | `--bl` |
| Repair manifest | `--repair-manifest` | — |

Additional property time series variants:

| Flag | Description |
|---|---|
| `--propertytsd` | Synthetic distance time series (elevation diff = 0) |
| `--propertytse` | Synthetic elevation time series (distance = 0) |
| `--propertyshd` | Synthetic distance hazard curves (elevation diff = 0) |
| `--propertyshe` | Synthetic elevation hazard curves (distance = 0) |

### Stressm Flags

| Flag | Effect |
|---|---|
| `--stressm` | Generate 20,000 storm sequences and compute gauge responses |
| `--stressm --gauge-id <ID>` | Single-gauge mode for inspection |
| `--all --nostress` | Full pipeline skipping the stress test entirely |

### Numeric Controls

```bash
python3 phys.py port --all \
  --num-properties 200 \
  --num-gauges 52 \
  --num-sims 10000 \
  --simulation-hours 168 \
  --history-years 50 \
  --tail-weight 2.0
```

### Hazard Distribution

```bash
python3 phys.py port --hazard --distribution gev     # GEV (default)
python3 phys.py port --hazard --distribution gumbel   # Gumbel
```

### Other Port Flags

| Flag | Description |
|---|---|
| `--verbose` / `-v` | Print detailed progress |
| `--strict` | Refuse to run if upstream data is stale (BCBS 239 lineage guard) |
| `--pdf` | Generate portfolio report PDF after generation |
| `--backup` | Back up existing data files before overwriting |
| `--repair-manifest` | Re-hash all pipeline artifacts and rebuild a consistent lineage manifest |

### Data Protection

Port generation is password-protected to prevent accidental or unauthorised data overwrites. On first run, you will be prompted to set an admin password. Subsequent runs require this password before any data is written.

```bash
python3 phys.py port --all

# MKM Portfolio Generator — Admin Authentication
#   Admin password: ********
#   Authenticated.
```

The password hash is stored in `data/.port_admin`. To reset the password, delete this file and run any port command to set a new one.

The `--backup` flag copies all existing JSON files in the data directory to `data/.backups/<timestamp>/` before generation, providing a rollback point.

The `--repair-manifest` command is read-only and does not require authentication.

---

## Flood Probability Fallback

The platform uses per-gauge GBM flood classifiers for scenario analysis in the Stress Test tab. These classifiers are trained individually per gauge via the UI — they are not generated by the port pipeline.

When classifiers are not available (fresh install, or before any have been trained), the platform falls back to the **FloodPoly** model — a closed-form polynomial approximation that requires no trained model files.

FloodPoly is a logistic sigmoid with a quadratic polynomial kernel, fitted from a representative GBM classifier (AUC = 0.994, 3.4M samples). It operates in log-transformed feature space using two gauge-independent features:

- `h = ln(water_level / severe_threshold)` — normalised water level
- `t = ln((hour + 1) / 168)` — normalised storm time

The model equation is:

```
P(flood) = σ(a·h + b·t + c·h·t + d·h² + e·t² + f)
```

Fit quality vs the source GBM classifier: R² = 0.94, MAE = 0.046, RMSE = 0.099. The model is conservative — it slightly over-predicts P(flood) in the transition zone, which is acceptable for stress testing where false negatives are costlier than false positives.

The platform is fully functional with FloodPoly alone. Training per-gauge classifiers via the UI improves accuracy for individual gauges but is not required.

---

## Storm Percentile Selector

Storm scenario dropdowns across the platform include a percentile selector for disclosure reporting. Instead of scrolling through thousands of storms sorted by severity, select a percentile (50% to 99.9%) and click Go to jump directly to the corresponding storm.

The 99th percentile of 20,000 storms selects the 200th worst storm (worse than 99% of all scenarios). The selector appears on:

- Trading Desk Stress tab
- Portfolio Stress tab
- Gauge Stress tab (hazard curve panel)
- Storm Portfolio Impact panel

Percentile values run from 50% to 99% in single percentage points, then 99.1% to 99.9% in 0.1% steps. Default is 99%.

---

## Additional Commands

### Check Configuration

```bash
python3 phys.py config
```

Prints the resolved project root, catchment, input/output directories, and server settings.

### Trading Book

Generate a PRS trading book independently:

```bash
python3 phys.py book --style thames-central --num-gauges 12
python3 phys.py book --style market-making --num-gauges 20 --pdf --seed 42 --clean
```

| Option | Description |
|---|---|
| `--style` | `thames-central` or `market-making` |
| `--num-gauges` | Number of gauges to include |
| `--clean` | Delete existing book before regenerating |
| `--pdf` | Generate trade confirmation PDFs |
| `--seed` | Random seed for reproducibility |
| `--verbose` | Detailed output |

### Testing and Audit

```bash
python3 phys.py test              # Run everything — all suites + audit reports
python3 phys.py test --unit       # Unit/model tests only
python3 phys.py test --e2e        # E2E browser tests (Playwright)
python3 phys.py test --lineage    # Data lineage consistency checks (BCBS 239)
python3 phys.py test --audit      # Generate audit reports
python3 phys.py test --audit --pdf    # Compile LaTeX reports to PDF
python3 phys.py test --params --pdf   # Generate parameter inventory
python3 phys.py test --check-deps     # Verify Python dependencies
python3 phys.py test --unit --model hazard prs   # Filter to specific models
```

### Visualisation

```bash
python3 phys.py visual               # Generate map and open in browser
python3 phys.py visual --no-browser   # Generate without opening
```

---

## Production Deployment (Gunicorn)

```bash
pip install gunicorn
gunicorn wsgi:app --bind 0.0.0.0:5013 --workers 4 --timeout 120
```

| Option | Recommended | Description |
|---|---|---|
| `--bind` | `0.0.0.0:5013` | Address and port |
| `--workers` | `2–4 × CPU cores` | Worker processes |
| `--timeout` | `120` | Request timeout in seconds |

Do not use the Flask development server for production.

---

## Docker

```bash
docker build -t physicalrisk .
docker run -p 5001:5001 physicalrisk
```

Or using Docker Compose:

```bash
docker-compose up
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MKM_CATCHMENT` | `thames` | Active catchment identifier |
| `MKM_PROJECT_ROOT` | auto-detected | Project root directory |
| `MKM_INPUT_DIR` | `data/input/{catchment}` | Portfolio input data |
| `MKM_OUTPUT_DIR` | `data/output` | Generated reports |
| `MKM_RESULTS_DIR` | `data/results` | Analysis results |
| `MKM_SERVER_HOST` | `127.0.0.1` | Server bind address |
| `MKM_SERVER_PORT` | `5013` | Server port |
| `MKM_DEBUG` | `false` | Flask debug mode |

---

## Legal Notice

Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

This software is the proprietary and confidential work of MKM Research Labs. It is licensed solely for non-commercial research and educational use. Any commercial use — including but not limited to incorporation into products or services offered for sale, use in internal business operations intended for commercial advantage, or research and development conducted on behalf of a commercial entity — is expressly prohibited unless separately authorised in writing by MKM Research Labs.

Use, reproduction, distribution, or modification of this software is subject to the terms and conditions of the licence agreement provided with this software. No licence is granted by implication, estoppel, or otherwise. Unauthorised use or reproduction of this software, in whole or in part, may result in civil and criminal penalties and will be prosecuted to the maximum extent permissible under applicable law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL MKM RESEARCH LABS OR ITS AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For licensing enquiries, please contact MKM Research Labs directly.
