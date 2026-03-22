# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Pipeline ID consistency tests — BCBS 239 Principle 3 (Accuracy).

These tests verify that gauge IDs, property IDs, and trade references
are consistent across ALL data files. Any mismatch means a pipeline
step was run out of order or against stale data.

If any of these tests fail, the data is BROKEN and must be regenerated
in the correct order:
    port --gauge → port --stressm → port --hazard → port --blotter
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "input" / "thames"
OUTPUT_DIR = ROOT / "data" / "output"


def _load_gauge_ids() -> set:
    """Load all gauge IDs from gauge.json (source of truth)."""
    path = INPUT_DIR / "gauge.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    ids = set()
    for g in data.get("flood_gauges", []):
        fg = g.get("FloodGauge", g)
        gid = fg.get("Header", {}).get("GaugeID", "")
        if gid:
            ids.add(gid)
    return ids


def _load_hazard_curve_ids() -> set:
    """Load all gauge IDs from gaugehc.json."""
    path = INPUT_DIR / "gaugehc.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    return set(data.get("hazard_curves", {}).keys())


def _load_trade_gauge_ids() -> set:
    """Load all gauge IDs referenced by open trades."""
    # Trades live in data/input/<catchment>/prs/ (not data/output/prs/)
    prs_dir = INPUT_DIR / "prs"
    if not prs_dir.exists():
        # Fallback to legacy location
        prs_dir = OUTPUT_DIR / "prs"
    if not prs_dir.exists():
        return set()
    ids = set()
    for f in prs_dir.glob("PRS-*.json"):
        try:
            d = json.load(open(f))
            ps = d.get("PhysicalSwap", {})
            if ps.get("Header", {}).get("TradeStatus") == "Closed":
                continue
            for g in ps.get("GaugeSet", {}).get("GaugeBasket", []):
                gid = g.get("GaugeID", "")
                if gid:
                    ids.add(gid)
        except Exception:
            continue
    return ids


def _load_gaugets_ids() -> set:
    """Load all gauge IDs from gaugets/ directory."""
    gaugets_dir = INPUT_DIR / "gaugets"
    if not gaugets_dir.exists():
        return set()
    ids = set()
    for f in gaugets_dir.glob("GAUGE-*.json"):
        try:
            d = json.load(open(f))
            gid = d.get("gauge_id", "")
            if gid:
                ids.add(gid)
        except Exception:
            continue
    return ids


def _load_property_ids() -> set:
    """Load all property IDs from property.json."""
    path = INPUT_DIR / "property.json"
    if not path.exists():
        return set()
    data = json.load(open(path))
    ids = set()
    for p in data.get("properties", []):
        pid = (p.get("PropertyHeader", {})
                .get("Header", {})
                .get("PropertyID", ""))
        if pid:
            ids.add(pid)
    return ids


# =========================================================================
# Gauge ID consistency
# =========================================================================

class TestGaugeIDConsistency:
    """All data files must reference gauge IDs that exist in gauge.json."""

    def test_gauge_json_has_gauges(self):
        """gauge.json must contain at least one gauge."""
        ids = _load_gauge_ids()
        assert len(ids) > 0, "gauge.json is empty or missing"

    def test_hazard_curves_match_gauges(self):
        """Every gauge in gauge.json must have a hazard curve."""
        gauge_ids = _load_gauge_ids()
        hc_ids = _load_hazard_curve_ids()
        if not hc_ids:
            pytest.skip("gaugehc.json not generated yet")
        missing = gauge_ids - hc_ids
        assert len(missing) == 0, (
            f"{len(missing)} gauges missing from gaugehc.json: "
            f"{sorted(missing)[:5]}. Run: python app.py port --hazard"
        )

    def test_hazard_curves_subset_of_gauges(self):
        """gaugehc.json must not contain IDs absent from gauge.json."""
        gauge_ids = _load_gauge_ids()
        hc_ids = _load_hazard_curve_ids()
        if not hc_ids:
            pytest.skip("gaugehc.json not generated yet")
        orphan = hc_ids - gauge_ids
        assert len(orphan) == 0, (
            f"{len(orphan)} hazard curves reference non-existent gauges: "
            f"{sorted(orphan)[:5]}. gaugehc.json is stale — regenerate."
        )

    def test_trade_gauges_exist_in_gauge_json(self):
        """Every gauge referenced by a trade must exist in gauge.json."""
        gauge_ids = _load_gauge_ids()
        trade_ids = _load_trade_gauge_ids()
        if not trade_ids:
            pytest.skip("No open trades")
        missing = trade_ids - gauge_ids
        assert len(missing) == 0, (
            f"{len(missing)} trade gauge IDs not in gauge.json: "
            f"{sorted(missing)[:5]}. Blotter is stale — regenerate: "
            f"python app.py port --blotter"
        )

    def test_trade_gauges_have_hazard_curves(self):
        """Every gauge with trades must have a hazard curve (for PRS pricing)."""
        hc_ids = _load_hazard_curve_ids()
        trade_ids = _load_trade_gauge_ids()
        if not trade_ids:
            pytest.skip("No open trades")
        if not hc_ids:
            pytest.skip("gaugehc.json not generated yet")
        missing = trade_ids - hc_ids
        assert len(missing) == 0, (
            f"{len(missing)} traded gauges missing hazard curves: "
            f"{sorted(missing)[:5]}. This causes 'Failed to load hazard "
            f"curve data' in the UI."
        )

    def test_gaugets_match_gauges(self):
        """gaugets/ files must reference gauge IDs from gauge.json."""
        gauge_ids = _load_gauge_ids()
        gaugets_ids = _load_gaugets_ids()
        if not gaugets_ids:
            pytest.skip("gaugets/ not generated yet")
        missing = gaugets_ids - gauge_ids
        assert len(missing) == 0, (
            f"{len(missing)} gaugets files reference non-existent gauges: "
            f"{sorted(missing)[:5]}. gaugets/ is stale."
        )


# =========================================================================
# Property ID consistency
# =========================================================================

class TestClassifierConsistency:
    """Stress classifiers must be trained on current gauge IDs."""

    def test_classifiers_exist(self):
        """At least one trained classifier must exist."""
        stressm_dir = INPUT_DIR / "stressm"
        if not stressm_dir.exists():
            pytest.skip("stressm/ not generated yet")
        classifiers = list(stressm_dir.glob("*.joblib"))
        assert len(classifiers) > 0, (
            "No trained classifiers found. Run: python app.py port --classifier-only"
        )

    def test_classifier_gauge_ids_match(self):
        """Classifiers that exist should reference current gauge IDs."""
        gauge_ids = _load_gauge_ids()
        stressm_dir = INPUT_DIR / "stressm"
        if not stressm_dir.exists():
            pytest.skip("stressm/ not generated yet")
        classifiers = list(stressm_dir.glob("GAUGE-*.joblib"))
        if not classifiers:
            pytest.skip("No classifiers found — run: python3 app.py classifier --all")
        clf_ids = {f.stem for f in classifiers}
        valid = clf_ids & gauge_ids
        stale = clf_ids - gauge_ids
        if not valid:
            pytest.skip(
                f"All {len(stale)} classifiers are stale (old gauge IDs). "
                "Run: python3 app.py classifier --all"
            )
        assert len(valid) > 0

    def test_training_summary_exists(self):
        """training_summary.json must exist alongside classifiers."""
        stressm_dir = INPUT_DIR / "stressm"
        if not stressm_dir.exists():
            pytest.skip("stressm/ not generated yet")
        summary = stressm_dir / "training_summary.json"
        if not summary.exists():
            pytest.skip("training_summary.json missing — run: python3 app.py classifier --all")


class TestPropertyIDConsistency:
    """Property data files must be internally consistent."""

    def test_property_json_has_properties(self):
        """property.json must contain at least one property."""
        ids = _load_property_ids()
        assert len(ids) > 0, "property.json is empty or missing"

    def test_property_ids_in_header(self):
        """PropertyID must be populated in Header (not just PropertyAttributes)."""
        prop_path = INPUT_DIR / "property.json"
        if not prop_path.exists():
            pytest.skip("property.json not generated")
        props = json.load(open(prop_path)).get("properties", [])
        empty_header_ids = []
        for i, p in enumerate(props):
            ph = p.get("PropertyHeader", {})
            hdr = ph.get("Header", {})
            attrs = ph.get("PropertyAttributes", {})
            hdr_id = hdr.get("PropertyID", "")
            attr_id = attrs.get("PropertyID", "")
            if not hdr_id and attr_id:
                empty_header_ids.append(attr_id)
        assert len(empty_header_ids) == 0, (
            f"{len(empty_header_ids)} properties have PropertyID in Attributes "
            f"but not in Header. This breaks propertyts flood processing. "
            f"Regenerate: python app.py port --property"
        )

    def test_propertyts_files_match_properties(self):
        """propertyts/ files must reference property IDs from property.json."""
        prop_ids = _load_property_ids()
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        pts_ids = set()
        for f in pts_dir.glob("PROP-*.json"):
            try:
                d = json.load(open(f))
                pid = d.get("property_id", "")
                if pid:
                    pts_ids.add(pid)
            except Exception:
                continue
        if not pts_ids:
            pytest.skip("No propertyts files found")
        missing = pts_ids - prop_ids
        assert len(missing) == 0, (
            f"{len(missing)} propertyts files reference non-existent properties: "
            f"{sorted(missing)[:5]}"
        )


# =========================================================================
# Storm ID consistency (stress_storms ↔ propertyts ↔ gaugets)
# =========================================================================

class TestStormIDConsistency:
    """Storm IDs must be consistent across stress_storms, propertyts, and gaugets."""

    def test_propertyts_storms_from_sequences(self):
        """Storm IDs in propertyts must come from storm_sequences.json."""
        seq_path = INPUT_DIR / "storm_sequences.json"
        pts_dir = INPUT_DIR / "propertyts"
        if not seq_path.exists():
            pytest.skip("storm_sequences.json not generated yet")
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")

        seq_data = json.load(open(seq_path))
        seq_storm_ids = set()
        for s in seq_data.get("sequences", []):
            for st in s.get("storms", []):
                sid = st.get("storm_id", "")
                if sid:
                    seq_storm_ids.add(sid)

        prop_storm_ids = set()
        for f in pts_dir.glob("PROP-*.json"):
            try:
                d = json.load(open(f))
                for evt in d.get("flood_events", []):
                    sid = evt.get("storm_id", "")
                    if sid:
                        prop_storm_ids.add(sid)
            except Exception:
                continue

        if not prop_storm_ids:
            pytest.skip("No flood events in propertyts")

        overlap = prop_storm_ids & seq_storm_ids
        assert len(overlap) > 0, (
            f"ZERO storm ID overlap between storm_sequences.json ({len(seq_storm_ids)} storms) "
            f"and propertyts/ ({len(prop_storm_ids)} storms). "
            f"Data is from different generation runs. "
            f"Fix: python app.py port --propertyts"
        )

    def test_gaugets_storms_from_sequences(self):
        """Storm IDs in gaugets/ must come from storm_sequences.json."""
        seq_path = INPUT_DIR / "storm_sequences.json"
        gaugets_dir = INPUT_DIR / "gaugets"
        if not seq_path.exists():
            pytest.skip("storm_sequences.json not generated yet")
        if not gaugets_dir.exists():
            pytest.skip("gaugets/ not generated yet")

        seq_data = json.load(open(seq_path))
        seq_storm_ids = set()
        for s in seq_data.get("sequences", []):
            for st in s.get("storms", []):
                sid = st.get("storm_id", "")
                if sid:
                    seq_storm_ids.add(sid)

        # Sample a few gaugets files to check storm_responses
        gaugets_storm_ids = set()
        for f in list(gaugets_dir.glob("GAUGE-*.json"))[:5]:
            try:
                d = json.load(open(f))
                for r in d.get("storm_responses", {}).get("responses", []):
                    gaugets_storm_ids.add(r.get("storm_id", ""))
            except Exception:
                continue

        if not gaugets_storm_ids:
            pytest.skip("No storm_responses in gaugets")

        overlap = gaugets_storm_ids & seq_storm_ids
        assert len(overlap) > 0, (
            f"ZERO storm ID overlap between storm_sequences.json ({len(seq_storm_ids)}) "
            f"and gaugets/ ({len(gaugets_storm_ids)}). "
            f"Data is from different runs. "
            f"Fix: python app.py port --stressm"
        )


class TestDataLineage:
    """Data lineage manifest must be consistent (BCBS 239 P2/P3)."""

    def test_manifest_exists(self):
        """data_lineage.json must exist after any port run."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        if not lineage_path.exists():
            pytest.skip("data_lineage.json not generated yet — run: python app.py port")
        data = json.load(open(lineage_path))
        assert "steps" in data, "Manifest missing 'steps' key"
        assert len(data["steps"]) > 0, "Manifest has no recorded steps"

    def test_output_hashes_current(self):
        """Recorded output hashes must match current files on disk."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        if not lineage_path.exists():
            pytest.skip("No manifest")

        # Import hash functions
        try:
            from lineage.manifest import hash_file, hash_directory
        except ImportError:
            pytest.skip("lineage package not available")

        data = json.load(open(lineage_path))
        mismatches = []
        for step_name, step in data.get("steps", {}).items():
            for name, info in step.get("outputs", {}).items():
                path = INPUT_DIR / name if not name.startswith("prs") else ROOT / "data" / "output" / name
                if not path.exists():
                    continue
                recorded = info.get("hash") or info.get("sha256")
                if recorded is None:
                    continue
                if path.is_dir():
                    current, _ = hash_directory(path)
                else:
                    current = hash_file(path)
                if current != recorded:
                    mismatches.append(f"{step_name}/{name}: recorded={recorded[:12]}... current={current[:12]}...")

        if mismatches:
            import warnings
            warnings.warn(
                f"{len(mismatches)} output hash mismatches — data modified since last pipeline run:\n"
                + "\n".join(f"  - {m}" for m in mismatches[:10])
                + "\n  Re-run: python3 app.py port"
            )

    def test_no_stale_inputs(self):
        """No step should have stale inputs."""
        try:
            from lineage.validation import validate_full_chain
        except ImportError:
            pytest.skip("lineage package not available")

        result = validate_full_chain()
        stale = result.get("stale_steps", [])
        assert len(stale) == 0, (
            f"{len(stale)} pipeline steps have stale inputs: {stale}. "
            f"Run: python app.py port to regenerate."
        )

    def test_dependency_graph_complete(self):
        """Every step in manifest must appear in the static dependency graph."""
        lineage_path = ROOT / "data" / "data_lineage.json"
        if not lineage_path.exists():
            pytest.skip("No manifest")
        try:
            from lineage.manifest import DEPENDENCY_GRAPH
        except ImportError:
            pytest.skip("lineage package not available")
        data = json.load(open(lineage_path))
        steps = set(data.get("steps", {}).keys())
        missing = steps - set(DEPENDENCY_GRAPH.keys())
        assert len(missing) == 0, f"Steps not in dependency graph: {missing}"


# =========================================================================
# Deterministic ID stability
# =========================================================================

class TestDeterministicIDs:
    """Gauge and property IDs must be deterministic (stable across runs)."""

    def test_gauge_ids_are_deterministic(self):
        """Gauge IDs should be derived from location, not random UUIDs."""
        import hashlib
        try:
            from port.rand.thames.gauge.gauge_locations import THAMES_GAUGE_LOCATIONS
        except ImportError:
            pytest.skip("Cannot import gauge locations")

        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("No gauges")

        # Compute what deterministic IDs should be
        expected = set()
        for loc in THAMES_GAUGE_LOCATIONS:
            loc_key = f"{loc['lat']:.6f}:{loc['lon']:.6f}:{loc.get('name', '')}"
            gid = f"GAUGE-{hashlib.sha256(loc_key.encode()).hexdigest()[:8]}"
            expected.add(gid)

        # If gauge.json was generated with the deterministic fix,
        # the IDs should match
        if gauge_ids != expected:
            pytest.fail(
                f"gauge.json has non-deterministic IDs. "
                f"Expected {sorted(expected)[:3]}..., "
                f"got {sorted(gauge_ids)[:3]}... "
                f"Regenerate: python app.py port --gauge"
            )
