# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Catchment-data layout parameters — the single source of truth for the names and
relative paths of every generated artifact.

Per project rule 1 (no hardcoded parameters outside the ``config`` package), all
filenames, directory names, scenario-mode suffixes and id field names live here. The
``database`` package builds its artifact registry from these constants and never hard
codes a literal of its own. Paths are relative to ``data/input/<catchment>/``.
"""

#: Default scenario variant ("normal" flood scenario).
DEFAULT_MODE = "flood"

#: Candidate id fields used to match a record within a portfolio document.
ID_FIELDS = ("id", "property_id", "gauge_id", "asset_id", "commercial_id",
             "loan_id", "counterparty_id", "swap_id", "event_id")

# ── Portfolio entity documents ───────────────────────────────────────────────
PORTFOLIO_FILES = {
    "gauge": "gauge.json",
    "property": "property.json",
    "loan": "loan.json",
    "commercial": "commercial.json",
    "commercial_loan": "commercial_loan.json",
    "counterparty": "counterparty.json",
}

# ── Hazard-curve documents (by scenario mode) ────────────────────────────────
GAUGE_HAZARD_FILE = "gaugehc.json"
PROPERTY_HAZARD_FILES = {
    "flood": "propertyhc.json", "shd": "propertyshd.json", "she": "propertyshe.json",
    "bri": "propertybri.json", "win": "propertywin.json", "faw": "propertyfaw.json",
    "fow": "propertyfow.json", "bow": "propertybow.json", "baw": "propertybaw.json",
}
COMMERCIAL_HAZARD_FILES = {
    "flood": "commercialhc.json", "shd": "commercialshd.json", "she": "commercialshe.json",
    "bri": "commercialbri.json", "win": "commercialwin.json", "faw": "commercialfaw.json",
    "fow": "commercialfow.json", "bow": "commercialbow.json", "baw": "commercialbaw.json",
}

# ── Timeseries directories (by scenario mode) ────────────────────────────────
PROPERTY_TS_DIRS = {
    "flood": "propertyts", "shd": "propertytsd", "she": "propertytse",
    "bri": "propertytsb", "win": "propertytsw", "faw": "propertytsfaw",
    "fow": "propertytsfow", "bow": "propertytsbow", "baw": "propertytsbaw",
}
COMMERCIAL_TS_DIRS = {
    "flood": "commercialts", "shd": "commercialtsd", "she": "commercialtse",
    "bri": "commercialtsb", "win": "commercialtsw", "faw": "commercialtsfaw",
    "fow": "commercialtsfow", "bow": "commercialtsbow", "baw": "commercialtsbaw",
}
GAUGE_TS_DIR = "gaugets"
GAUGE_HISTORY_DIR = "gaugehd"
GAUGE_HISTORY_FILENAME = "gauge_{key}_hd.json"
PORTFOLIO_FLOOD_SUMMARY_FILE = "portfolio_flood_summary.json"

# ── Storms / sequences ───────────────────────────────────────────────────────
STORM_SEQUENCES_FILE = "storm_sequences.json"
STRESS_STORMS_DIR = "stress_storms"
STRESS_STORM_INDEX_FILE = "stress_storms/_index.json"
SEQUENCE_GAUGE_DIR = "sequence_gauge"

# ── Perils ───────────────────────────────────────────────────────────────────
FIRE_RESULTS_FILE = "fire/fire.json"
SEISMIC_RESULTS_FILE = "seismic/seismic.json"
TYPHOON_DAMAGE_DIR = "typhoon/damage"

# ── Trading desk ─────────────────────────────────────────────────────────────
MARKET_STATE_FILE = "blotter/market_state.json"
TRADE_MARKS_FILE = "blotter/trade_marks.json"
EOD_DIR = "blotter/eod"
EOD_KEY_PREFIX = "EOD-"
PRS_DIR = "prs"

# ── Classifiers (binary) ─────────────────────────────────────────────────────
CLASSIFIERS_DIR = "classifiers"
CLASSIFIER_FILENAME = "{key}.joblib"

# ── Generic keyed-file naming ────────────────────────────────────────────────
KEYED_FILENAME = "{key}.json"
