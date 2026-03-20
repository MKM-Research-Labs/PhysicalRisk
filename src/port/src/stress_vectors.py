# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Stress vector generator — builds per-gauge training vectors for the
flood classifier.

Each gauge gets 5 chunked JSON files in stress_vectors/ containing
log-transformed features derived from 168h compound gauge responses to
all storm sequences.  Near-miss augmentation is included so the classifier
can learn smooth probability transitions near the severe threshold.

Chunking keeps every file under GitHub's 100 MB limit (~27 MB each).

Port step 5b — runs after stressm (which generates sequences + gauge
responses) and before hazard curves.

Output: data/input/<catchment>/stress_vectors/GAUGE-xxx_1.json … _5.json
"""

import json
import math
import time
from pathlib import Path
from typing import Optional

import numpy as np

# Log-transform constants (must match classifier.py)
_LOG_END = 168.0
_LOG_EPS = 1e-8
_NUM_HOURS = 168

# Near-miss augmentation
_NEARMISS_COUNT = 200
_NEARMISS_LOW = 0.80
_NEARMISS_HIGH = 0.99

# Chunking — keeps files under GitHub's 100 MB limit
NUM_CHUNKS = 5


def load_gauge_vectors(sv_dir: Path, gauge_id: str) -> dict:
    """Load and reassemble chunked vector files for one gauge.

    Reads GAUGE-xxx_1.json … GAUGE-xxx_5.json, concatenates their
    ``vector`` arrays, and returns a single dict identical to the
    old monolithic format.
    """
    sv_dir = Path(sv_dir)
    chunks = sorted(sv_dir.glob(f"{gauge_id}_*.json"))

    # Backwards compat: also accept un-chunked GAUGE-xxx.json
    if not chunks:
        legacy = sv_dir / f"{gauge_id}.json"
        if legacy.exists():
            with open(legacy) as f:
                return json.load(f)
        raise FileNotFoundError(
            f"No vector files for {gauge_id} in {sv_dir}")

    all_vectors = []
    meta = None
    for cp in chunks:
        with open(cp) as f:
            chunk = json.load(f)
        all_vectors.extend(chunk["vector"])
        if meta is None:
            meta = {k: v for k, v in chunk.items()
                    if k not in ("vector", "chunk", "total_chunks",
                                 "num_vectors_total", "flood_positive_total")}

    meta["vector"] = all_vectors
    meta["num_vectors"] = len(all_vectors)
    return meta


def list_available_gauges(sv_dir: Path) -> list:
    """Return sorted list of gauge IDs with saved vectors (chunked or legacy)."""
    sv_dir = Path(sv_dir)
    ids = set()
    for p in sv_dir.glob("GAUGE-*_1.json"):
        ids.add(p.stem.rsplit("_", 1)[0])
    for p in sv_dir.glob("GAUGE-*.json"):
        if "_" not in p.stem:
            ids.add(p.stem)
    return sorted(ids)


def _generate_nearmiss_vectors(severe_l: float, base_level: float, rng) -> list:
    """Synthesise near-miss hydrographs peaking at 80-99% of severe."""
    vectors = []
    for _ in range(_NEARMISS_COUNT):
        peak_frac = rng.uniform(_NEARMISS_LOW, _NEARMISS_HIGH)
        peak_level = severe_l * peak_frac
        rise_hours = rng.randint(10, 50)
        decay_rate = rng.uniform(0.02, 0.08)

        levels = np.full(_NUM_HOURS, base_level, dtype=float)
        for h in range(_NUM_HOURS):
            if h < rise_hours:
                phase = (h / rise_hours) * (math.pi / 2)
                levels[h] = base_level + (peak_level - base_level) * math.sin(phase)
            else:
                dt = h - rise_hours
                levels[h] = base_level + (peak_level - base_level) * math.exp(-decay_rate * dt)

        log_hs = [math.log(max(lv / severe_l, _LOG_EPS)) for lv in levels]
        for h in range(_NUM_HOURS):
            log_t = math.log((h + 1) / _LOG_END)
            delta = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
            prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
            delta2 = delta - prev_delta
            vectors.append([
                round(log_hs[h], 6), round(log_t, 6),
                round(delta, 6), round(delta2, 6), 0,
            ])
    return vectors


def _build_gauge_vectors(
    sequences: list,
    gauge: dict,
    spatial_model,
    target_spatial_index: int,
    rng,
) -> dict:
    """Build training vectors for one gauge.

    Returns dict with vectors, levels metadata, and label info.
    """
    from port.src.storm_multi.models.sequence_response import (
        SequenceGaugeParams, compute_sequence_gauge_response, _make_precip_series,
    )

    gid = gauge["gauge_id"]
    severe_l = gauge["severe_warning"]
    alert_l = gauge["flood_alert"]
    warning_l = gauge["flood_warning"]

    gp = SequenceGaugeParams(
        gauge_id=gid,
        base_level=gauge["base_level"],
        flood_alert=alert_l,
        flood_warning=warning_l,
        severe_warning=severe_l,
    )

    vectors = []
    flood_positive = 0

    for seq in sequences:
        catchment_precip = _make_precip_series(seq)
        gauge_precip_all = spatial_model.apply_to_sequence(
            seq, catchment_precip, rng=rng
        )
        levels = compute_sequence_gauge_response(
            seq, gp, precip_series=gauge_precip_all[target_spatial_index]
        )

        if severe_l > 0:
            log_hs = [math.log(max(lv / severe_l, _LOG_EPS)) for lv in levels]
        else:
            log_hs = [math.log(max(lv, _LOG_EPS)) for lv in levels]

        for h in range(_NUM_HOURS):
            log_t = math.log((h + 1) / _LOG_END)
            delta = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
            prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
            delta2 = delta - prev_delta
            future_max = max(levels[h:]) if h < _NUM_HOURS else levels[h]
            flood_flag = 1 if (severe_l > 0 and future_max >= severe_l) else 0
            if flood_flag:
                flood_positive += 1
            vectors.append([
                round(log_hs[h], 6), round(log_t, 6),
                round(delta, 6), round(delta2, 6), flood_flag,
            ])

    total_v = len(vectors)
    label_level = severe_l
    label_name = "severe_warning"

    # Near-miss augmentation
    if severe_l > 0 and flood_positive > 0:
        nm_rng = np.random.RandomState(rng.randint(0, 2**31))
        nearmiss = _generate_nearmiss_vectors(severe_l, gauge["base_level"], nm_rng)
        vectors.extend(nearmiss)

    # If no severe events, relabel against flood_alert
    if flood_positive == 0:
        label_level = alert_l
        label_name = "flood_alert"
        vectors = []
        flood_positive = 0
        for seq in sequences:
            catchment_precip = _make_precip_series(seq)
            gauge_precip_all = spatial_model.apply_to_sequence(
                seq, catchment_precip, rng=rng
            )
            levels = compute_sequence_gauge_response(
                seq, gp, precip_series=gauge_precip_all[target_spatial_index]
            )
            ref = label_level
            log_hs = [math.log(max(lv / ref, _LOG_EPS)) for lv in levels]
            for h in range(_NUM_HOURS):
                log_t = math.log((h + 1) / _LOG_END)
                delta = log_hs[h] - log_hs[h - 1] if h > 0 else 0.0
                prev_delta = log_hs[h - 1] - log_hs[h - 2] if h > 1 else 0.0
                delta2 = delta - prev_delta
                future_max = max(levels[h:]) if h < _NUM_HOURS else levels[h]
                flood_flag = 1 if future_max >= ref else 0
                if flood_flag:
                    flood_positive += 1
                vectors.append([
                    round(log_hs[h], 6), round(log_t, 6),
                    round(delta, 6), round(delta2, 6), flood_flag,
                ])
        # Near-miss against alert
        if flood_positive > 0:
            nm_rng = np.random.RandomState(rng.randint(0, 2**31))
            nearmiss = _generate_nearmiss_vectors(alert_l, gauge["base_level"], nm_rng)
            vectors.extend(nearmiss)

    return {
        "gauge_id": gid,
        "alert_level": round(alert_l, 4),
        "warning_level": round(warning_l, 4),
        "severe_level": round(label_level, 4),
        "label_threshold": label_name,
        "num_sequences": len(sequences),
        "num_vectors": len(vectors),
        "flood_positive": flood_positive,
        "flood_rate": round(flood_positive / len(vectors), 6) if vectors else 0,
        "vector": vectors,
    }


def generate_stress_vectors(
    input_dir: Path,
    output_dir: Path,
    count: int = 20_000,
    catchment_id: str = "thames",
    seed: int = 42,
    gauge_id: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """
    Build stress vectors for all (or one) gauge and save to stress_vectors/.

    Loads sequences from storm_sequences.json (already generated by stressm),
    rebuilds gauge responses, and saves per-gauge vector JSON files.

    Args:
        input_dir:    data/input/<catchment>/
        output_dir:   stress_vectors/ directory
        count:        Expected sequence count (for loading)
        catchment_id: Catchment identifier
        seed:         Random seed
        gauge_id:     If set, only build vectors for this gauge
        verbose:      Extra logging

    Returns:
        Summary dict.
    """
    import json
    from port.src.storm_multi.utils.serialization import load_sequences, SEQUENCES_FILENAME
    from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel
    from port.src.stressm.gauge_parser import (
        _extract_gauges, _parse_gauge, _load_gaugehd_baselines,
    )

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()

    # Load sequences (already generated by stressm step 5)
    seq_path = input_dir / SEQUENCES_FILENAME
    if not seq_path.exists():
        raise FileNotFoundError(
            f"storm_sequences.json not found at {seq_path}. "
            "Run step 5 (stressm) first."
        )
    sequences = load_sequences(seq_path)
    print(f"  Loaded {len(sequences):,} sequences from {SEQUENCES_FILENAME}", flush=True)

    # Load gauge portfolio
    gauge_path = input_dir / "gauge.json"
    with open(gauge_path) as f:
        gauge_json = json.load(f)

    gaugehd_dir = input_dir / "gaugehd"
    baselines = _load_gaugehd_baselines(gaugehd_dir)

    raw_gauges = _extract_gauges(gauge_json)
    all_gauges = [parsed for rec in raw_gauges
                  if (parsed := _parse_gauge(rec, baselines)) is not None]

    # Build spatial model
    all_locations = [(g["lat"], g["lon"]) for g in all_gauges]
    spatial_model = SpatialCorrelationModel(all_locations)
    all_gauge_ids = [g["gauge_id"] for g in all_gauges]

    # Filter to requested gauge(s)
    if gauge_id:
        target_gauges = [g for g in all_gauges if g["gauge_id"] == gauge_id]
        if not target_gauges:
            raise ValueError(f"Gauge '{gauge_id}' not found in gauge.json")
    else:
        target_gauges = all_gauges

    n = len(target_gauges)
    print(f"  Building stress vectors for {n} gauge{'s' if n != 1 else ''}...",
          flush=True)

    rng = np.random.RandomState(seed)
    results = []

    for i, gauge in enumerate(target_gauges):
        gid = gauge["gauge_id"]
        spatial_i = all_gauge_ids.index(gid)
        t1 = time.time()

        result = _build_gauge_vectors(
            sequences=sequences,
            gauge=gauge,
            spatial_model=spatial_model,
            target_spatial_index=spatial_i,
            rng=np.random.RandomState(seed + 1 + i),
        )

        # Save as chunked JSON (5 files per gauge)
        vectors = result.pop("vector")
        chunk_size = math.ceil(len(vectors) / NUM_CHUNKS)
        total_kb = 0
        for ci in range(NUM_CHUNKS):
            chunk_vectors = vectors[ci * chunk_size : (ci + 1) * chunk_size]
            chunk_doc = {
                **result,
                "chunk": ci + 1,
                "total_chunks": NUM_CHUNKS,
                "num_vectors_total": result["num_vectors"],
                "flood_positive_total": result["flood_positive"],
                "vector": chunk_vectors,
            }
            chunk_path = output_dir / f"{gid}_{ci + 1}.json"
            with open(chunk_path, "w") as f:
                json.dump(chunk_doc, f, separators=(",", ":"))
            total_kb += chunk_path.stat().st_size / 1024

        elapsed_g = time.time() - t1
        print(f"    [{i+1}/{n}] {gid}  "
              f"vectors={result['num_vectors']:,}  "
              f"flood_rate={result['flood_rate']:.1%}  "
              f"label={result['label_threshold']}  "
              f"({elapsed_g:.1f}s, {NUM_CHUNKS} chunks, {total_kb:.0f} KB)",
              flush=True)

        results.append({
            "gauge_id": gid,
            "num_vectors": result["num_vectors"],
            "flood_positive": result["flood_positive"],
            "flood_rate": result["flood_rate"],
            "label_threshold": result["label_threshold"],
        })

    elapsed = time.time() - t0

    summary = {
        "num_gauges": len(results),
        "total_vectors": sum(r["num_vectors"] for r in results),
        "elapsed_seconds": round(elapsed, 1),
        "gauges": results,
    }

    # Write index
    index_path = output_dir / "_index.json"
    with open(index_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary
