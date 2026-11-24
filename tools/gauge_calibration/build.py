# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Build ``catch/<catchment>/gauge_calibration.json`` from Environment Agency records.

Shape-matches each gauge's simulated river rise to its observed record (not a fit):

* the EA daily-maximum record gives one annual maximum per water year (Oct-Sep,
  years under 300 days skipped) as the rise above the station's median daily
  level, so EA datums never meet ours;
* ``sensitivity`` scales the simulated rise (linear in
  ``sequence_response._route_quickflow_to_level``) by the geometric mean of
  observed/simulated rise at 2, 10 and 20 years, against a sensitivity-1 run;
* alert / warning / severe rises are the observed 2, 10 and 50-year rises from a
  Gumbel (L-moment) fit, so a level reached once in 50 years in reality is
  reached about 2% a year in the simulation.

Gauges without a record (tidal Thames, synthetic) take the catchment median,
marked provisional.

    python tools/gauge_calibration/build.py --ea-cache DIR --reference INPUT_DIR [--fetch]
"""

import argparse
import collections
import json
import math
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HYDROLOGY = "https://environment.data.gov.uk/hydrology/id/stations"
FLOOD_MONITORING = "https://environment.data.gov.uk/flood-monitoring/id/stations"
SEARCH_KM = 3
# A gauge only takes a station this close: its own lock or bridge, never the next
# one along (which would hand a tidal gauge the record of the lock above it).
MATCH_KM = 2.0
MIN_DAYS_PER_YEAR = 300
FIT_PERIODS = (2, 10, 20)
TRIGGER_PERIODS = {"alert": 2, "warning": 10, "severe": 50}
# A daily maximum above the station's own highest-on-record by more than this is
# a bad reading, provided both EA services share a datum.
SUSPECT_MARGIN_M = 0.10
SAME_DATUM_M = 1.0
MODEL_VERSIONS = {"MKM-ST-001": "2.0.0", "MKM-GHD-001": "2.0.0", "MKM-GH-001": "2.0.0"}

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mkm-gauge-calibration"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def _km(lat1, lon1, lat2, lon2):
    p = math.radians
    a = (math.sin(p(lat2 - lat1) / 2) ** 2
         + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(p(lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def _nearest_thames(items, lat, lon):
    """Nearest non-tidal River Thames station as (km, station), or None."""
    best = None
    for s in items:
        river = s.get("riverName") or ""
        river = " ".join(river).lower() if isinstance(river, list) else river.lower()
        if "thames" not in river or "tideway" in river:
            continue
        la, lo = s.get("lat"), s.get("long")
        if isinstance(la, list):
            la, lo = la[0], lo[0]
        d = _km(lat, lon, la, lo)
        if d > MATCH_KM:
            continue
        if best is None or d < best[0]:
            best = (d, s)
    return best


def _station(url):
    st = _get(url)["items"]
    return st[0] if isinstance(st, list) else st


def fetch(gauges, cache: Path):
    """Download each gauge's EA daily-maximum record and station scale into *cache*."""
    cache.mkdir(parents=True, exist_ok=True)
    for g in gauges:
        where = {"lat": g["lat"], "long": g["lon"], "dist": SEARCH_KM}
        q = urllib.parse.urlencode({"observedProperty": "waterLevel", **where})
        hy = _nearest_thames(_get(f"{HYDROLOGY}?{q}").get("items", []), g["lat"], g["lon"])
        if not hy:
            continue
        measures = [m["@id"] if isinstance(m, dict) else m
                    for m in _station(hy[1]["@id"]).get("measures", [])]
        measure = next((m for m in measures if "level-max-86400" in m), None)
        if not measure:
            continue
        readings = _get(f"{measure}/readings?mineq-date=1950-01-01&_limit=100000")["items"]
        q2 = urllib.parse.urlencode({"parameter": "level", **where})
        fm = _nearest_thames(_get(f"{FLOOD_MONITORING}?{q2}").get("items", []), g["lat"], g["lon"])
        scale = {}
        if fm:
            sc = _station(fm[1]["@id"]).get("stageScale")
            sc = _get(sc)["items"] if isinstance(sc, str) else (sc or {})
            scale = {"typical_low": sc.get("typicalRangeLow"),
                     "max_on_record": (sc.get("maxOnRecord") or {}).get("value")}
        record = {"station": hy[1].get("label"), "km": round(hy[0], 2), "measure": measure,
                  "scale": scale,
                  "readings": [[r["date"], r["value"], r.get("quality")]
                               for r in readings if r.get("value") is not None]}
        json.dump(record, open(cache / f"{g['name']}.json", "w"))
        print(f"  fetched {g['name']}: {record['station']} ({len(record['readings'])} days)",
              flush=True)

def _datum_segments(by_year):
    """Split water years wherever the yearly median level jumps by more than
    SAME_DATUM_M — a station datum change, not the river. Returns {water_year: segment}."""
    seg, prev, out = 0, None, {}
    for wy in sorted(by_year):
        med = statistics.median(v for v, _ in by_year[wy])
        if prev is not None and abs(med - prev) > SAME_DATUM_M:
            seg += 1
        out[wy], prev = seg, med
    return out


def annual_maxima(record):
    """{water_year: {rise_m, date}} above the median daily level of the year's datum
    segment, plus excluded years and the water years where the datum changed."""
    vals = [(d, v) for d, v, q in record["readings"] if q != "Suspect"]
    by_year = collections.defaultdict(list)
    for d, v in vals:
        by_year[int(d[:4]) + (int(d[5:7]) >= 10)].append((v, d))
    segment = _datum_segments(by_year)
    seg_median = {s: statistics.median(v for wy, days in by_year.items() if segment[wy] == s
                                       for v, _ in days)
                  for s in set(segment.values())}
    scale = record.get("scale") or {}
    out, excluded = {}, []
    for wy, days in sorted(by_year.items()):
        if len(days) < MIN_DAYS_PER_YEAR:
            continue
        median = seg_median[segment[wy]]
        if (scale.get("max_on_record") is not None and scale.get("typical_low") is not None
                and abs(median - scale["typical_low"]) < SAME_DATUM_M):
            cap = scale["max_on_record"] + SUSPECT_MARGIN_M
            if max(days)[0] > cap:
                excluded.append({"water_year": wy, "value_m": max(days)[0],
                                 "reason": "above the station's highest on record"})
                days = [x for x in days if x[0] <= cap]
        v, d = max(days)
        out[wy] = {"rise_m": round(v - median, 3), "date": d}
    changes = [wy for wy in sorted(segment) if wy - 1 in segment and segment[wy] != segment[wy - 1]]
    return out, excluded, changes


def empirical_level(values, T):
    """Level with return period T from Gringorten plotting positions, or None beyond the record."""
    xs = sorted(values, reverse=True)
    n = len(xs)
    ts = [(n + 0.12) / (i + 1 - 0.44) for i in range(n)]
    if T >= ts[0]:
        return None
    for i in range(n - 1):
        if ts[i] >= T >= ts[i + 1]:
            w = (math.log(T) - math.log(ts[i + 1])) / (math.log(ts[i]) - math.log(ts[i + 1]))
            return xs[i + 1] + w * (xs[i] - xs[i + 1])
    return xs[-1]


def gumbel_level(values, T):
    """Level with return period T from a Gumbel fit by L-moments."""
    xs = sorted(values)
    n = len(xs)
    b0 = sum(xs) / n
    b1 = sum(i * x for i, x in enumerate(xs)) / (n * (n - 1))
    alpha = (2 * b1 - b0) / math.log(2)
    xi = b0 - 0.5772156649 * alpha
    return xi - alpha * math.log(-math.log(1 - 1 / T))


def reference_catalogue(reference: Path, gauge_ids):
    """The reference run's event catalogue, built exactly as the hazard stage builds
    it (GH-001 v2): storm-gauge peaks per member storm, grouped into events and
    population-weighted — the storm set over-samples severe storms on purpose."""
    from models.frequency.events import build_catalogue
    from models.hazard.data_structures import GaugeResponse
    from models.hazard.io._load import load_storms_from_sequences
    seqs = json.load(open(reference / "storm_sequences.json"))
    members = {s["sequence_id"]: [m["storm_id"] for m in s.get("storms") or []]
               for s in seqs["sequences"]}
    responses = {}
    for gid in gauge_ids:
        sg = json.load(open(reference / "sequence_gauge" / f"{gid}.json"))
        rows = []
        for seq in sg["sequences"]:
            ids = members.get(seq["sequence_id"]) or []
            pulses = seq.get("pulse_peaks") or [{"storm_index": 0, "peak_m": seq["peak_m"]}]
            for p in pulses:
                if p["storm_index"] < len(ids):
                    rows.append(GaugeResponse(gid, ids[p["storm_index"]], 0.0, 0.0,
                                              float(p["peak_m"]), False, False, False))
        responses[gid] = rows
    return build_catalogue(responses, load_storms_from_sequences(seqs))


def simulated_rises(reference: Path, gauge_id, catalogue, storms_per_year):
    """Reference run's rise above normal level at each fit period, from the
    population-weighted catalogue annualised as the hazard curves are:
    P(year) = 1 − exp(−λ · P(level | event)). Made with MKM_GAUGE_CALIBRATION=off."""
    hd = json.load(open(reference / "gaugehd" / f"gauge_{gauge_id}_hd.json"))
    base = hd["statistics"]["median_level"]

    def annual(level):
        return 1 - math.exp(-storms_per_year * catalogue.conditional_probability(gauge_id, level))

    out = {}
    for T in (*FIT_PERIODS, 50):
        lo, hi = base - 5.0, base + 50.0
        for _ in range(60):                       # bisect: annual() falls as level rises
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if annual(mid) > 1 / T else (lo, mid)
        out[T] = (lo + hi) / 2 - base
    return out

def _solve_rating_curve(target, sim):
    """(sensitivity, exponent) with sensitivity × sim ** exponent through the 2- and
    20-year *target* rises."""
    lo, hi = FIT_PERIODS[0], FIT_PERIODS[-1]
    exponent = math.log(target[hi] / target[lo]) / math.log(sim[hi] / sim[lo])
    return target[lo] / sim[lo] ** exponent, exponent


def calibrate_gauge(record, sim, first_pass=None):
    """One gauge's calibration entry from its EA record and reference-run rises.

    Rating curve rise = offset + sensitivity × reference_rise ** rise_exponent,
    solved through the observed 2- and 20-year rises (Gumbel); the 10- and 50-year
    points are an out-of-sample check, recorded in ``fit``.

    ``offset`` is the seasonal head start the storms begin from (they arrive mostly
    in winter, above the annual median), which the rating curve does not shape. It
    is measured from *first_pass* — the weighted rises of a run made with the
    first-pass calibration — as its mean excess over the first-pass curve; without
    one it is zero.
    """
    am, excluded, datum_changes = annual_maxima(record)
    rises = [x["rise_m"] for x in am.values()]
    obs = {T: gumbel_level(rises, T) for T in (*FIT_PERIODS, 50)}
    s1, b1 = _solve_rating_curve(obs, sim)
    offset = 0.0
    if first_pass:
        offset = statistics.mean(first_pass[T] - s1 * sim[T] ** b1 for T in sim)
    sensitivity, exponent = _solve_rating_curve({T: v - offset for T, v in obs.items()}, sim)
    fitted = {T: offset + sensitivity * sim[T] ** exponent for T in sim}
    top = max(am, key=lambda wy: am[wy]["rise_m"])
    return {
        "ea_station": record["station"],
        "ea_station_km": record["km"],
        "ea_measure": record["measure"],
        "record_years": len(am),
        "sensitivity": round(sensitivity, 4),
        "rise_exponent": round(exponent, 4),
        "seasonal_offset_m": round(offset, 3),
        # History swings shrink by the first-pass slope at typical (2-year) levels;
        # held fixed across passes so the seasonal offset stays what was measured.
        "variability_scale": round(obs[FIT_PERIODS[0]] / sim[FIT_PERIODS[0]], 4),
        "rise_m": {**{lv: round(obs[T], 3) for lv, T in TRIGGER_PERIODS.items()},
                   "historical_high": am[top]["rise_m"]},
        "historical_high_date": am[top]["date"][:10],
        "fit": {"observed_rise_m": {str(T): round(v, 3) for T, v in obs.items()},
                "reference_rise_m": {str(T): round(v, 3) for T, v in sim.items()},
                "fitted_rise_m": {str(T): round(v, 3) for T, v in fitted.items()}},
        "excluded_years": excluded,
        "datum_changes": datum_changes,
        "annual_max_rise_m": {str(wy): x["rise_m"] for wy, x in am.items()},
    }


def build(catchment, cache: Path, reference: Path, storms_per_year, first_pass: Path = None):
    gauges = [g["FloodGauge"]["Header"] for g in json.load(open(reference / "gauge.json"))["flood_gauges"]]
    calibrated = [(h["GaugeName"], h["GaugeID"]) for h in gauges
                  if (cache / f"{h['GaugeName']}.json").exists()]
    catalogue = reference_catalogue(reference, [gid for _, gid in calibrated])
    first_cat = reference_catalogue(first_pass, [gid for _, gid in calibrated]) if first_pass else None
    entries = {}
    for name, gid in calibrated:
        path = cache / f"{name}.json"
        sim = simulated_rises(reference, gid, catalogue, storms_per_year)
        fp = simulated_rises(first_pass, gid, first_cat, storms_per_year) if first_pass else None
        entries[name] = {"gauge_id": gid, **calibrate_gauge(json.load(open(path)), sim, fp)}
        e = entries[name]
        f = e["fit"]
        print(f"  {name:28} s {e['sensitivity']:.3f}  b {e['rise_exponent']:.2f}  "
              + "  ".join(f"{T}y {f['fitted_rise_m'][T]:.2f}/{f['observed_rise_m'][T]:.2f}"
                          for T in ("2", "10", "20", "50")), flush=True)
    levels = (*TRIGGER_PERIODS, "historical_high")
    med = lambda key: round(statistics.median(e[key] for e in entries.values()), 4)  # noqa: E731
    default = {
        "provisional": True,
        "applies_to": "gauges without their own EA record (tidal Thames, synthetic gauges)",
        "sensitivity": med("sensitivity"),
        "rise_exponent": med("rise_exponent"),
        "variability_scale": med("variability_scale"),
        "rise_m": {lv: round(statistics.median(e["rise_m"][lv] for e in entries.values()), 3)
                   for lv in levels},
    }
    return {
        "catchment": catchment,
        "built": date.today().isoformat(),
        "source": "Environment Agency Hydrology API, daily maximum water level (level-max-86400)",
        "method": ("Shape match, not a fit: sensitivity = geometric mean of observed/simulated "
                   "rise at the 2, 10 and 20-year return periods; trigger rises = observed "
                   "Gumbel (L-moment) 2, 10 and 50-year rises above the median daily level."),
        "storms_per_year": storms_per_year,
        "return_periods": TRIGGER_PERIODS,
        "model_versions": MODEL_VERSIONS,
        "default": default,
        "gauges": entries,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the gauge calibration from EA records.")
    ap.add_argument("--catchment", default="thames")
    ap.add_argument("--ea-cache", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True,
                    help="input dir of a sensitivity-1 run (gauge.json, gaugets/, gaugehd/)")
    ap.add_argument("--storms-per-year", type=float)
    ap.add_argument("--first-pass", type=Path,
                    help="input dir of a run made with the first-pass calibration; "
                         "measures each gauge's seasonal offset and re-solves")
    ap.add_argument("--fetch", action="store_true", help="download the EA records first")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from config.frequency import catchment_lambda
    lam = args.storms_per_year or catchment_lambda(args.catchment)
    if args.fetch:
        real = [g["FloodGauge"] for g in json.load(open(args.reference / "gauge.json"))["flood_gauges"]
                if g["FloodGauge"]["SensorDetails"]["GaugeInformation"].get("DataSourceType")
                == "SensorGauge"]
        fetch([{"name": fg["Header"]["GaugeName"], "lat": fg["Location"]["GaugeLatitude"],
                "lon": fg["Location"]["GaugeLongitude"]} for fg in real], args.ea_cache)
    doc = build(args.catchment, args.ea_cache, args.reference, lam, args.first_pass)
    out = args.out or REPO_ROOT / "catch" / args.catchment / "gauge_calibration.json"
    json.dump(doc, open(out, "w"), indent=1)
    print(f"wrote {out} ({len(doc['gauges'])} gauges calibrated)")


if __name__ == "__main__":
    main()
