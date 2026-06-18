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

"""Unit tests for the CDM Asset Review tool's pure helpers and summary builders.

These exercise the small dict-walking helpers (``_addr``/``_coords``/
``_set_nested``/``_get_nested``), every per-asset summary builder, the audit
log read/append helpers, and the model-output loaders — all without a Flask
client and without touching the real data tree.
"""

import json


# --- tiny formatting helpers ------------------------------------------------
def test_addr_joins_present_bits_only(app_mod):
    loc = {"BuildingNumber": "12", "StreetName": "Mill Rd",
           "TownCity": None, "Postcode": "CB1 2AB"}
    assert app_mod._addr(loc) == "12 Mill Rd CB1 2AB"


def test_addr_empty(app_mod):
    assert app_mod._addr({}) == ""


def test_type_class_known_and_unknown(app_mod):
    assert app_mod._type_class("residential") == "badge-residential"
    assert app_mod._type_class("commercial") == "badge-commercial"
    assert app_mod._type_class("industrial") == "badge-industrial"
    assert app_mod._type_class("warehouse") == "badge-na"
    assert app_mod._type_class(None) == "badge-na"


def test_coords_valid(app_mod):
    assert app_mod._coords("51.5", "-0.1") == {"lat": 51.5, "lon": -0.1}


def test_coords_invalid(app_mod):
    assert app_mod._coords(None, "x") == {"lat": None, "lon": None}
    assert app_mod._coords("nan-ish", None) == {"lat": None, "lon": None}


# --- nested get/set ---------------------------------------------------------
def test_set_nested_creates_intermediate_dicts(app_mod):
    rec = {}
    app_mod._set_nested(rec, "A.B.C", 7)
    assert rec == {"A": {"B": {"C": 7}}}


def test_set_nested_single_segment(app_mod):
    rec = {}
    app_mod._set_nested(rec, "Top", 1)
    assert rec["Top"] == 1


def test_get_nested_hit_and_miss(app_mod):
    rec = {"A": {"B": {"C": 7}}}
    assert app_mod._get_nested(rec, "A.B.C") == 7
    assert app_mod._get_nested(rec, "A.B.X") is None
    assert app_mod._get_nested(rec, "A.B.C.D") is None  # walk past a scalar


# --- summary builders -------------------------------------------------------
def test_sum_gauge(app_mod):
    rec = {"FloodGauge": {"Header": {"GaugeID": "G1", "GaugeName": "Weir",
                                     "CatchmentID": "thames"},
                          "Location": {"GaugeLatitude": 51.0,
                                       "GaugeLongitude": -0.2}}}
    s = app_mod._sum_gauge(rec)
    assert s["id"] == "G1" and s["sub"] == "Weir" and s["tag"] == "thames"
    assert s["lat"] == 51.0 and s["lon"] == -0.2


def test_sum_gauge_defaults(app_mod):
    s = app_mod._sum_gauge({})
    assert s["sub"] == "—" and s["tag"] == "gauge"


def test_sum_property(app_mod):
    rec = {"PropertyHeader": {
        "Header": {"PropertyID": "P9", "propertyType": "residential"},
        "Location": {"StreetName": "High St", "TownCity": "London"},
        "Valuation": {"PropertyValue": 400000}}}
    s = app_mod._sum_property(rec)
    assert s["id"] == "P9"
    assert s["tag"] == "residential" and s["tagClass"] == "badge-residential"
    assert s["value"] == 400000 and "High St" in s["sub"]


def test_sum_property_uprn_fallback(app_mod):
    rec = {"PropertyHeader": {"Header": {"UPRN": "U1"}, "Location": {},
                              "Valuation": {}}}
    assert app_mod._sum_property(rec)["id"] == "U1"


def test_sum_commercial(app_mod):
    rec = {"CommercialAsset": {"Header": {"PropertyID": "C1"},
                              "Location": {"TownCity": "Leeds"},
                              "CommercialAttributes": {"CommercialType": "Office"},
                              "Valuation": {"PropertyValue": 9_000_000}}}
    s = app_mod._sum_commercial(rec)
    assert s["id"] == "C1" and s["tag"] == "Office"
    assert s["tagClass"] == "badge-commercial" and s["value"] == 9_000_000


def test_sum_commercial_defaults(app_mod):
    s = app_mod._sum_commercial({})
    assert s["tag"] == "commercial"


def test_sum_loan_rloan_root(app_mod):
    rec = {"RLoan": {"Header": {"RLoanID": "L1", "PropertyID": "P1"},
                     "CurrentStatus": {"AccountStatus": "Active",
                                       "OutstandingBalance": 123},
                     "FinancialTerms": {"OriginalLoan": 200}}}
    s = app_mod._sum_loan(rec)
    assert s["id"] == "L1" and s["sub"] == "Property P1"
    assert s["tag"] == "Active" and s["value"] == 123


def test_sum_loan_balance_falls_back_to_original(app_mod):
    rec = {"RLoan": {"Header": {"RLoanID": "L2"},
                     "CurrentStatus": {},
                     "FinancialTerms": {"OriginalLoan": 555}}}
    s = app_mod._sum_loan(rec)
    assert s["value"] == 555 and s["sub"] == "—" and s["tag"] == "loan"


def test_sum_commercial_loan_uses_meta(app_mod):
    rec = {"Mortgage": {"Header": {"RLoanID": "CL1"}, "CurrentStatus": {},
                        "FinancialTerms": {}},
           "_commercial_meta": {"commercial_type": "Retail",
                                "borrower_type": "SPV"}}
    s = app_mod._sum_commercial_loan(rec)
    assert s["id"] == "CL1" and s["sub"] == "Retail · SPV"


def test_sum_commercial_loan_without_meta_keeps_loan_sub(app_mod):
    rec = {"Mortgage": {"Header": {"RLoanID": "CL2", "PropertyID": "P5"},
                        "CurrentStatus": {}, "FinancialTerms": {}}}
    s = app_mod._sum_commercial_loan(rec)
    assert s["sub"] == "Property P5"


def test_sum_counterparty(app_mod):
    rec = {"CounterpartySet": {"Party": {
        "PartyID": "CP1", "PartyName": "Acme Bank",
        "ContactInformation": {"City": "London", "Country": "UK"}}}}
    s = app_mod._sum_counterparty(rec)
    assert s["id"] == "CP1" and s["sub"] == "Acme Bank" and s["tag"] == "London UK"


def test_sum_counterparty_defaults(app_mod):
    s = app_mod._sum_counterparty({})
    assert s["sub"] == "—" and s["tag"] == "counterparty"


# --- records helpers --------------------------------------------------------
def test_records_of_list_passthrough(app_mod):
    assert app_mod._records_of([1, 2, 3], "property") == [1, 2, 3]


def test_records_of_container(app_mod):
    doc = {"properties": [{"x": 1}]}
    assert app_mod._records_of(doc, "property") == [{"x": 1}]


def test_records_of_missing_container(app_mod):
    assert app_mod._records_of({}, "property") == []


def test_record_id(app_mod):
    rec = {"PropertyHeader": {"Header": {"PropertyID": "PID"},
                              "Location": {}, "Valuation": {}}}
    assert app_mod._record_id("property", rec) == "PID"


# --- audit log helpers ------------------------------------------------------
def test_load_audit_missing_returns_empty(app_mod, sandbox):
    assert app_mod._load_audit() == []


def test_load_audit_corrupt_returns_empty(app_mod, sandbox):
    app_mod.AUDIT_FILE.write_text("{ not json", encoding="utf-8")
    assert app_mod._load_audit() == []


def test_append_audit_empty_is_noop(app_mod, sandbox):
    app_mod._append_audit([])
    assert not app_mod.AUDIT_FILE.exists()


def test_append_audit_accumulates(app_mod, sandbox):
    app_mod._append_audit([{"field": "a"}])
    app_mod._append_audit([{"field": "b"}])
    assert [e["field"] for e in app_mod._load_audit()] == ["a", "b"]


# --- model output loaders ---------------------------------------------------
def test_model_assets_missing_file(app_mod, tmp_path):
    app_mod._CACHE.clear()
    model, amap = app_mod._model_assets("fire", tmp_path / "nope.json")
    assert model is None and amap == {}


def test_model_assets_parses_and_caches(app_mod, tmp_path):
    app_mod._CACHE.clear()
    p = tmp_path / "fire.json"
    p.write_text(json.dumps({"metadata": {"model": "MKM-FIRE-001"},
                             "assets": [{"asset_id": "C1", "n_fires": 3}]}),
                 encoding="utf-8")
    model, amap = app_mod._model_assets("fire", p)
    assert model == "MKM-FIRE-001" and amap["C1"]["n_fires"] == 3
    # second call (different path) returns the cached first result
    again = app_mod._model_assets("fire", tmp_path / "other.json")
    assert again[1]["C1"]["n_fires"] == 3


def test_storm_type_index_missing(app_mod, monkeypatch, tmp_path):
    app_mod._CACHE.clear()
    monkeypatch.setattr(app_mod, "INPUT_DIR", tmp_path)
    assert app_mod._storm_type_index() == {}


def test_storm_type_index_parses(app_mod, monkeypatch, tmp_path):
    app_mod._CACHE.clear()
    monkeypatch.setattr(app_mod, "INPUT_DIR", tmp_path)
    (tmp_path / "storm_sequences.json").write_text(json.dumps({"sequences": [
        {"sequence_id": "S1", "sequence_type": "cluster",
         "intensity_category": "severe"}]}), encoding="utf-8")
    idx = app_mod._storm_type_index()
    assert idx["S1"] == {"type": "cluster", "intensity": "severe"}


# --- hazard-curve record loader --------------------------------------------
def test_hc_record_unsupported_asset(app_mod):
    assert app_mod._hc_record("gauge", "G1") is None


def test_hc_record_reads_and_caches(app_mod, monkeypatch, tmp_path):
    app_mod._CACHE.clear()
    monkeypatch.setattr(app_mod, "INPUT_DIR", tmp_path)
    (tmp_path / "propertyhc.json").write_text(json.dumps({
        "property_hazard_curves": {"P1": {"flood_zone": "3"}}}), encoding="utf-8")
    assert app_mod._hc_record("property", "P1") == {"flood_zone": "3"}
    assert app_mod._hc_record("property", "ZZZ") is None  # cache hit, missing id


def test_hc_record_missing_file_empty(app_mod, monkeypatch, tmp_path):
    app_mod._CACHE.clear()
    monkeypatch.setattr(app_mod, "INPUT_DIR", tmp_path)  # no propertyhc.json
    assert app_mod._hc_record("property", "P1") is None


# --- seed-source golden fallback -------------------------------------------
def test_seed_source_golden_fallback(app_mod, monkeypatch, tmp_path):
    monkeypatch.setattr(app_mod, "INPUT_DIR", tmp_path / "empty")  # no primary
    golden = tmp_path / "golden.json"
    golden.write_text("{}", encoding="utf-8")
    monkeypatch.setitem(app_mod.ASSETS["property"], "golden", golden)
    assert app_mod._seed_source("property") == golden
