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

"""Wolfram oracle benchmark parameters for MKM-SS-001 (Storm Sequence Generator).

The cases a benchmark run evaluates, the claims in SS-001's model document
(``storm_multi_v3.1.pdf``, v3.1, 09-Nov-2026) it tests, and where it files its evidence.
Benchmark v0.1 tested v2.0 (11-Mar-2026); it is kept in the git history and filed in
History as evidence of the check.
"""

ORACLE_SS_PACKAGE = "src/port/src/storm_multi"
ORACLE_SS_SOURCES = ("src/port/src/storm_multi/generators/sequence_generator.py",
                     "src/port/src/storm_multi/generators/batch_generator.py",
                     "src/port/src/storm_multi/generators/duration_sampler.py",
                     "src/port/src/storm_multi/generators/gap_sampler.py",
                     "src/port/src/storm_multi/generators/intensity_sampler.py",
                     "src/port/src/storm_multi/utils/validation.py")

ORACLE_SS_OUT_DIR = "docs/models/storm_sequence_benchmark"
ORACLE_SS_DOC = "MKM-SS-001_wolfram_benchmark"
ORACLE_SS_CSV = "storm_sequence.csv"
ORACLE_SS_WL = "storm_sequence.wl"
ORACLE_SS_TABLE_PREFIX = "evidence_tables_"

ORACLE_SS_CODE_TOL = 1e-12       # replayed sequences: code against the reference
ORACLE_SS_WOLFRAM_TOL = 1e-25    # exact probabilities: Wolfram against the reference
ORACLE_SS_Z_LIMIT = 4.0          # Monte Carlo against exact: standard errors allowed

# The document's equations and tables (v3.1), as the reference implements them.
ORACLE_SS_WINDOW_H = 168
ORACLE_SS_DRAIN_H = 12
ORACLE_SS_SEQ_PROB = {"minimal": "0.05", "baseline": "0.15", "moderate": "0.30", "severe": "0.50",
                      "extreme": "0.70", "catastrophic": "0.85"}
ORACLE_SS_TYPE_WEIGHTS = {"minimal": ("0.60", "0.30", "0.10"), "baseline": ("0.60", "0.30", "0.10"),
                          "moderate": ("0.50", "0.35", "0.15"), "severe": ("0.30", "0.50", "0.20"),
                          "extreme": ("0.20", "0.45", "0.35"), "catastrophic": ("0.15", "0.45", "0.40")}
ORACLE_SS_COUNTS = {"isolated": (1,), "doublet": (2,), "cluster": (3,), "persistent": (4,)}
ORACLE_SS_GAP_OF = {"doublet": "medium", "cluster": "medium", "persistent": "short"}
ORACLE_SS_DURATION = {"minimal": (1, 2, 4), "baseline": (2, 4, 8), "moderate": (4, 10, 20),
                      "severe": (8, 16, 32), "extreme": (12, 24, 48), "catastrophic": (16, 40, 80)}
ORACLE_SS_GAP = {"short": (6, 18, 36), "medium": (24, 48, 72)}
ORACLE_SS_BASE = {"minimal": (0.3, 0.10), "baseline": (0.6, 0.15), "moderate": (1.0, 0.20),
                  "severe": (1.8, 0.30), "extreme": (3.0, 0.50), "catastrophic": (5.0, 0.80)}
ORACLE_SS_VARIATION = "0.2"
ORACLE_SS_CORR_PROB = "0.70"
ORACLE_SS_FLOOR = 0.1
ORACLE_SS_BETA = (2.0, 2.0)
ORACLE_SS_WEIGHTS = {"moderate": "0.40", "severe": "0.35", "extreme": "0.20", "catastrophic": "0.05"}
ORACLE_SS_PBASE = {"thames": 35.0, "mekong": 90.0, "halong": 100.0}   # Table 7, catch/<id>/storm.py
ORACLE_SS_PBASE_FALLBACK = ("rhine", 35.0)  # a catchment with no storm module takes the Thames value

# The cases.
ORACLE_SS_SEED = 42
ORACLE_SS_COUNT = 10000
ORACLE_SS_SEEDS = 100            # s7.2: 100 independent seeds of 10,000
ORACLE_SS_FORCED_SEED = 20261107  # every category with every forced type
ORACLE_SS_FORCED_COUNT = 400
ORACLE_SS_CATEGORIES = ("minimal", "baseline", "moderate", "severe", "extreme", "catastrophic")

# The document's stated figures.
ORACLE_SS_TABLE9 = {"isolated": 5225, "doublet": 1469, "cluster": 2116, "persistent": 1190}
ORACLE_SS_TABLE9_PCT = 1         # s7.2: pooled over 100 seeds, every type within 1% of Table 9
ORACLE_SS_CAP_WORST = ("catastrophic", "persistent", 4, 77.7)  # s6.2: the configuration capped most often, %
ORACLE_SS_CAP_ALL_PCT = 8.6      # s6.2: share of all duration draws capped, default batch
ORACLE_SS_PINNED_PCT = 3.1       # s6.3: multi-storm sequences with every storm capped
ORACLE_SS_SHORTENED_PCT = 35.4   # s6.3: multi-storm sequences whose gaps are shortened
ORACLE_SS_SCALE_STATED = {"moderate-severe persistent": 4.7, "catastrophic persistent": 99.7}  # s6.3, %
ORACLE_SS_Q6_CAP_PCT = 50        # Q6: a cap rate above this calls for recalibration
ORACLE_SS_Q6_SHORT_PCT = 70      # Q6: a shortening rate (by type) above this says the tables are inconsistent
ORACLE_SS_SHORT_BY_TYPE = {"doublet": 0.8, "cluster": 52.3, "persistent": 47.9}  # s6.3 / Q6: baseline, %
ORACLE_SS_SUBSEQUENT_STATED = "0.85"  # Table 8: P(subsequent storm >= first)
ORACLE_SS_SECONDS = 60           # Q2: 10,000 sequences in under a minute
ORACLE_SS_GAUGES_STATED = 11     # s7.3: the summary of the classifiers retrained for v3.1 covers 11 Thames gauges
ORACLE_SS_AUC_STATED = 0.9842    # its mean AUC-ROC, to four places (retrained on v3.1's catalogue)
ORACLE_SS_EXAMPLE_GAUGE = "GAUGE-1aaf8b08"
ORACLE_SS_CLASSIFIER_SUMMARY = "training_summary.json"  # in config.get_classifiers_dir()
ORACLE_SS_STATED_PATHS = ("src/port/src/stressm/pipeline/orchestrator/_core.py", "src/port/src/stressm/batch_train.py",
                          "src/routes/trading/stress/training.py", "app/commands/port/stages/storm.py",
                          "app/commands/port/parser.py", "phys.py")
ORACLE_SS_STATED_FLAGS = ("--stressm", "--num-sims", "--gauge-id", "--seed")  # in app/commands/port/parser.py
ORACLE_SS_STATED_FILES = ("storm_sequences.json", "sequences_summary.json")
ORACLE_SS_STATED_MODULES = {
    "core/data_structures.py": ("SequenceStorm", "StormSequence", "SequenceType", "GapType",
                                "make_storm_id", "make_sequence_id"),
    "generators/sequence_generator.py": ("SequenceGenerator",),
    "generators/batch_generator.py": ("generate_event_set",),
    "generators/duration_sampler.py": ("sample_duration", "get_duration_range"),
    "generators/gap_sampler.py": ("sample_gap", "get_gap_range", "get_min_gap"),
    "generators/intensity_sampler.py": ("should_generate_sequence", "sample_sequence_type",
                                        "get_storm_count", "sample_storm_intensity"),
    "utils/validation.py": ("validate_sequence", "validate_event_set", "fits_in_window", "precip_end_hour",
                            "min_gap_hours"),
    "utils/serialization.py": ("save_sequences", "save_summary", "load_sequences"),
}
ORACLE_SS_CAP_TOL = 1e-9         # a duration within this of the cap is capped
# The code redraws the first storm's variation from the same law when a uniform draw is
# at least this (FIRST_STORM_DOMINANT_PROB: so with probability 0.70; v3.0 s3.7 states it).
# It cannot change delta_0's law; the replay mirrors it so the random streams stay in step.
ORACLE_SS_REDRAW_PROB = 0.30
