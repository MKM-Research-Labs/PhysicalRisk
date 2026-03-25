# PhysicalRisk Platform

A flood risk modelling and pricing platform for mortgage and property portfolios, developed by MKM Research Labs. The platform models physical climate risk across catchment areas, generates synthetic portfolio data, prices Physical Risk Swaps (PRS), and produces regulatory-grade audit evidence.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/MKM-Research-Labs/PhysicalRisk.git
cd PhysicalRisk
```

### 2. Install Python

The platform requires Python 3.11 or later. Python 3.13 is recommended.

Download the latest release from the official Python website and follow the installer instructions for your operating system:

```
https://www.python.org/downloads/
```

Verify your installation:

```bash
python3 --version
```

### 3. Create a Virtual Environment

Create a virtual environment inside the cloned directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

You should see `(.venv)` prefixed in your shell prompt.

### 4. Install Dependencies

With the virtual environment active, install all required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs the full dependency set including NumPy, pandas, SciPy, scikit-learn, GeoPandas, folium, QuantLib, Flask, ReportLab, and pytest.

### 5. Generate Portfolio Data

The repository does not include generated data. After cloning, run the port pipeline to create your local dataset:

```bash
# Quick start — full pipeline without classifier training (~30 min)
python3 app.py port --all --nostress

# Full pipeline including classifiers (~2–4 hours, best run overnight)
python3 app.py port --all --train-classifier
```

Then run the audit to verify data integrity:

```bash
python3 app.py test --audit
```

### 6. Verify Configuration

Check that the platform can locate all required directories:

```bash
python3 app.py config
```

This prints the resolved project root, catchment, input/output directories, and server settings.

---

## Running the Platform

The recommended sequence is: **port → audit → visual → server**, with classifier training left to run overnight once the platform is up.

> **First time running?** You must run `python3 app.py port` before starting the server — the repository does not include generated data. Use `--all --nostress` to get the platform up quickly. The multi-storm stress test and GBM classifier training (step 6) generates 20,000 storm sequences and trains one classifier per gauge — approximately 2–4 hours total. Get the platform running first, then leave `--all --train-classifier` to run overnight.

### Step 1 — Generate the Portfolio

**Recommended overnight run** — full pipeline including storm sequences and all GBM flood classifiers:

```bash
python3 app.py port --all --train-classifier
```

Approximate timing:
- Steps 1–5 (gauges, properties, synthetic gauges, mortgages, historical data): ~5–10 min
- Step 6 stressm (20,000 sequences × 219 gauges + classifiers): ~2–4 hours
- Steps 7–11 (hazard curves, property risk, counterparties, blotter): ~10–20 min

**Quick daytime run** — skip the stress test entirely to get the platform up in minutes:

```bash
python3 app.py port --all --nostress
```

This runs all 11 pipeline steps except the multi-storm stress test (step 6). The platform is fully functional without classifiers — the Stress Test tab uses heuristic flood probability estimates until trained models are available.

**Generate storm sequences without classifier training** — useful for regenerating hazard curves:

```bash
python3 app.py port --stressm --no-classifier
python3 app.py port --hazard
```

Once storm sequences exist (`storm_sequences.json`), hazard curves can be rebuilt independently at any time.

### Pipeline Steps

The full `--all` pipeline runs the following steps in order:

| Step | Flag | Output |
|---|---|---|
| 1 | `--gauges` | `gauge.json` — 52 real gauge locations |
| 2 | `--properties` | `property.json` — synthetic property portfolio |
| 2.5 | *(automatic)* | Synthetic gauges — virtual gauges on river centreline nearest each property |
| 3 | `--mortgages` | `mortgage.json` — mortgage book |
| 4 | `--gaugehd` | `gaugehd/` — per-gauge historical daily data |
| 5 | `--stressm` | `storm_sequences.json`, `gaugets/`, `sequence_gauge/` — 20,000 multi-storm sequences + classifiers |
| 6 | `--hazard` | `gaugehc.json` — GEV/Gumbel hazard curves per gauge |
| 7 | `--propertyts` | `propertyts/` — per-property flood time series |
| 8 | `--propertyhc` | `propertyhc.json` — property hazard curves + PRS pricing |
| 9 | `--counterparties` | `counterparty.json` |
| 10 | `--blotter` | Trade PDFs + 3 months of EOD snapshots |

> **Dependency note:** Step 6 (hazard curves) reads from `storm_sequences.json` produced by step 5. If you skip step 5 with `--nostress`, an existing `storm_sequences.json` from a previous run is used. If no file exists yet, run `--stressm` separately first.
>
> **Synthetic gauges:** Step 2.5 runs automatically after property generation. For each property, a synthetic gauge is created at the nearest point on the river centreline, with properties interpolated from the two real gauges either side. Nearby properties (within 50m) share a synthetic gauge. These synthetic gauges flow through stressm, hazard curves, and PRS pricing as first-class entities.

### Segment Flags

You can run individual segments instead of the full pipeline:

| Segment | Flag | Short |
|---|---|---|
| Flood gauges | `--gauges` | `--ga` |
| Properties | `--properties` | `--pr` |
| Synthetic gauges | *(runs automatically after properties)* | — |
| Mortgages | `--mortgages` | `--mo` |
| Gauge historical data | `--gaugehd` | `--hd` |
| Multi-storm sequences + classifiers | `--stressm` | — |
| Hazard curves | `--hazard` | `--hz` |
| Property flood time series | `--propertyts` | `--pt` |
| Property hazard curves | `--propertyhc` | `--phc` |
| Counterparties | `--counterparties` | `--ctpy` |
| Trading blotter | `--blotter` | `--bl` |
| Repair manifest | `--repair-manifest` | — |

Use `--repair-manifest` after partial pipeline runs or when the lineage manifest (`data/data_lineage.json`) has become inconsistent. It re-hashes all on-disk artifacts without regenerating any data, making the manifest match the current file state.

```bash
python3 app.py port --repair-manifest
```

### Classifier Flags

| Flag | Alias | Effect |
|---|---|---|
| `--stressm` | — | Generate 10,000 storm sequences, compute gauge responses; no classifier |
| `--stressm --train-classifier` | `--stressm --tc` | Generate sequences + train one GBM per gauge (~2–4 hours for 52 gauges) |
| `--stressm --no-classifier` | `--stressm --nc` | Alias for plain `--stressm`; sequences only, skip GBM training |
| `--stressm --gauge-id <ID>` | `--stressm --gid <ID>` | Single-gauge mode for inspection or targeted retraining |
| `--all --train-classifier` | — | Full pipeline including classifier training (recommended overnight run) |
| `--all --nostress` | — | Full pipeline skipping step 6 entirely |

### Numeric Controls

```bash
python3 app.py port --all \
  --num-properties 200 \
  --num-gauges 52 \
  --num-storms 10000 \
  --simulation-hours 168 \
  --history-years 50
```

### Hazard Distribution

The hazard curve fitting distribution can be selected independently:

```bash
# GEV distribution (default)
python3 app.py port --hazard --distribution gev

# Gumbel distribution
python3 app.py port --hazard --distribution gumbel
```

Other flags:

```bash
--verbose / -v  # Print detailed progress
```

**Example: regenerate gauge time series and rebuild hazard curves with verbose output:**

```bash
python3 app.py port --gaugets --hazard -v
```

### Step 2 — Generate the Visualisation

Once portfolio data exists, generate the interactive flood risk map:

```bash
python3 app.py visual
```

This produces a folium HTML map and opens it in your default browser. To generate without launching the browser:

```bash
python3 app.py visual --no-browser
```

The map file is written to `data/results/`.

### Step 3 — Start the Server

There are two ways to run the server depending on your environment.

#### Development (Flask built-in)

For local development and testing, use the built-in Flask server:

```bash
python3 app.py server
```

The server runs on `http://127.0.0.1:5013` by default. Options:

```bash
python3 app.py server --host 0.0.0.0 --port 8080 --debug
```

| Option | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `5013` | Port number |
| `--debug` | off | Enable Flask debug mode |

Do not use the Flask development server for production — it is single-threaded and not designed to handle concurrent requests reliably.

#### Production (Gunicorn + wsgi.py)

For a production or shared environment, use Gunicorn pointing at `wsgi.py`. First install Gunicorn into your virtual environment:

```bash
pip install gunicorn
```

Then start the server:

```bash
gunicorn wsgi:app --bind 0.0.0.0:5013 --workers 4 --timeout 120
```

| Option | Recommended value | Description |
|---|---|---|
| `--bind` | `0.0.0.0:5013` | Address and port to listen on |
| `--workers` | `2–4 × CPU cores` | Number of worker processes |
| `--timeout` | `120` | Request timeout in seconds — increase if report generation is slow |
| `--access-logfile` | `-` | Log requests to stdout |
| `--error-logfile` | `-` | Log errors to stdout |

A typical production invocation:

```bash
gunicorn wsgi:app \
  --bind 0.0.0.0:5013 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

To run Gunicorn as a background daemon and redirect logs to a file:

```bash
gunicorn wsgi:app \
  --bind 0.0.0.0:5013 \
  --workers 4 \
  --timeout 120 \
  --daemon \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

Create the `logs/` directory first if using file logging:

```bash
mkdir -p logs
```

To stop a daemonised Gunicorn, find and kill the master process:

```bash
pkill -f "gunicorn wsgi:app"
```

### Step 4 — Run Long Tasks Overnight

Once the server is running and you have confirmed the platform is working, the full portfolio pipeline with classifier training is best left to run overnight unattended:

```bash
# Terminal 2 — Full pipeline with classifier training (~2–4 hours for 52 gauges)
python3 app.py port --all --train-classifier

# Terminal 3 — Full test audit (run concurrently or after)
python3 app.py test --audit
```

**Daytime workflow (platform usable immediately, classifiers deferred):**

```bash
# Morning: full pipeline without stress test, platform up in minutes
python3 app.py port --all --nostress

# Evening: leave this running overnight — trains all 52 GBM classifiers
python3 app.py port --all --train-classifier
```

The platform works normally while classifiers are training — the Stress Test tab uses heuristic flood probability estimates until each gauge's model is available. Once `--train-classifier` completes, restart the server to pick up the new classifiers:

```bash
python3 app.py server
```

---

## Additional Commands

### Trading Book

Generate a PRS trading book independently of the full portfolio pipeline:

```bash
# Thames Central style (default)
python3 app.py book --style thames-central --num-gauges 12

# Market making style
python3 app.py book --style market-making --num-gauges 20 --pdf --seed 42 --clean
```

| Option | Description |
|---|---|
| `--style` | `thames-central` or `market-making` |
| `--num-gauges` | Number of gauges to include |
| `--clean` | Delete existing book before regenerating |
| `--pdf` | Generate trade confirmation PDFs |
| `--seed` | Random seed for reproducibility |
| `--verbose` | Detailed output |

### Test Audit

Run the full test suite and generate a regulatory-grade audit evidence package:

```bash
python3 app.py test --audit
```

To also compile a PDF test evidence report (requires a LaTeX installation):

```bash
python3 app.py test --audit --pdf
```

You can filter tests to a specific model using its alias:

```bash
python3 app.py test --audit --model hazard prs
```

Audit outputs are written to `data/output/audit/` and include a JUnit XML report, coverage XML and HTML, a LaTeX test report, a code analysis report, and a duplication report.

### Check Dependencies

Verify all Python dependencies are installed and importable:

```bash
python3 app.py check
```

To generate a parameter inventory document:

```bash
python3 app.py check params
```

---

## Environment Variables

All configuration values can be overridden via environment variables:

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

## Platform Overview

### Catchments and Portfolio Generation

The platform is built around the concept of a catchment — a geographic river system used as the basis for flood risk modelling. The Thames catchment is the primary implementation, with architecture in place to support additional catchments. Within a catchment, the platform synthesises a complete portfolio of flood gauges, properties, and mortgages. The Thames catchment covers 52 real gauge locations: 12 upstream non-tidal gauges from Reading to Teddington Lock, and 40 tidal gauges from Richmond to Purfleet. For each property, a synthetic gauge is created at the nearest point on the river centreline, with hydrological properties interpolated from the two flanking real gauges. This gives each property a dedicated nearby gauge with physically meaningful storm responses, rather than relying on distant real gauges. Properties within 50m of the same river point share a synthetic gauge. A typical 200-property portfolio produces ~170 synthetic gauges, giving a total of ~220 gauges in the network. Mortgages are then generated against the property portfolio, linking physical flood risk to financial exposure.

### Storm Modelling

Storm scenarios are generated using the `storm_multi` sequence generator, which produces compound multi-storm events rather than independent scenarios. The generator supports four sequence types: isolated single storms, doublets (two storms in close succession), clusters (three to four storms), and persistent systems (four to five storms). All sequences are constrained to a 168-hour (seven-day) event window, with precipitation required to end by hour 156 — matching the insurance industry's standard loss aggregation clause. Sequence durations, intensities, and inter-storm gaps are stochastically sampled using calibrated distributions across six intensity categories from minimal through to catastrophic. Each sequence is written to `storm_sequences.json` in the portfolio input directory.

The `stressm` pipeline runs the full multi-storm forward model: for each sequence, a spatial correlation model translates storm intensities into per-gauge precipitation, which drives the hydrological forward model to produce water level responses at all gauges (real and synthetic). Per-gauge responses are written to individual files under `sequence_gauge/` to keep file sizes under version control limits. The resulting gauge response matrix is used both to build hazard curves and to train the GBM flood classifiers.

### Hazard Curves and Flood Classification

For each gauge, the platform fits a Generalised Extreme Value (GEV) or Gumbel distribution to the simulated water level record drawn from the multi-storm sequences, producing a hazard curve that maps return period to flood depth. A gradient-boosted machine learning classifier is trained per gauge on the stress test response data to estimate the probability of flooding given current water level, hour of storm, and first and second order rate of change in water level. This classifier operates in near real-time during scenario analysis and is retrained whenever `--stressm --train-classifier` is run.

### Physical Risk Swap Pricing

The core financial product priced by the platform is the Physical Risk Swap — a bilateral contract in which one counterparty pays a fixed spread and receives floating payments contingent on flood events at specified gauge locations. PRS pricing uses QuantLib's credit default swap framework, with flood probability replacing credit default probability on the hazard leg. Property-level hazard curves are aggregated to gauge level and fed into the pricing engine. The platform generates a complete trading book with individual trade confirmations, mark-to-market valuations, and end-of-day portfolio snapshots covering a three-month historical window.

### Interactive Visualisation

The visualisation layer produces a self-contained HTML interactive map of the catchment using folium. The map renders all gauges and properties as clickable markers with context menus. From any gauge marker a user can access the gauge report, view the hazard curve, inspect the storm analysis panel, or open the trading blotter filtered to that gauge. From any property marker a user can generate a property or mortgage report, view the property hazard curve, or inspect property-level flood scenarios. The map loads directly in a browser with no server dependency.

### REST API

The Flask API exposes the full platform over HTTP using versioned blueprints under `/api/v1`. Endpoints cover property and gauge portfolios, time series data, hazard curves, PRS pricing, counterparty management, the trading book, EOD snapshots, and governance documents. A detailed health check endpoint reports the status of all data files and model dependencies. The API is CORS-enabled and suitable for integration with external dashboards or risk management systems.

### Audit and Governance

The platform produces a comprehensive audit evidence package on demand. This includes a JUnit XML test report, line and branch coverage reports, a compiled LaTeX test evidence document, static code analysis, and a code duplication report. Model usage is logged automatically via a structured audit trail. Governance documents including model risk committee reports, validation evidence, and regulatory submissions are stored and served through the governance API endpoints.

---

## Docker

A Docker image is provided for containerised deployment:

```bash
docker build -t physicalrisk .
docker run -p 5001:5001 physicalrisk
```

Or using Docker Compose:

```bash
docker-compose up
```

The containerised server runs on port 5001 with `FLASK_ENV=production`.

---

## Legal Notice

Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

This software is the proprietary and confidential work of MKM Research Labs. It is licensed solely for non-commercial research and educational use. Any commercial use — including but not limited to incorporation into products or services offered for sale, use in internal business operations intended for commercial advantage, or research and development conducted on behalf of a commercial entity — is expressly prohibited unless separately authorised in writing by MKM Research Labs.

Use, reproduction, distribution, or modification of this software is subject to the terms and conditions of the licence agreement provided with this software. No licence is granted by implication, estoppel, or otherwise. Unauthorised use or reproduction of this software, in whole or in part, may result in civil and criminal penalties and will be prosecuted to the maximum extent permissible under applicable law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL MKM RESEARCH LABS OR ITS AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For licensing enquiries, please contact MKM Research Labs directly.
