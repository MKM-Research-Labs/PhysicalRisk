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
(``storm_multi.pdf``, v2.0, 11-Mar-2026) it tests, and where it files its evidence.
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

# The document's equations and tables (v2.0), as the reference implements them.
ORACLE_SS_WINDOW_H = 168
ORACLE_SS_DRAIN_H = 12
ORACLE_SS_SEQ_PROB = {"minimal": "0.05", "baseline": "0.15", "moderate": "0.30", "severe": "0.50",
                      "extreme": "0.70", "catastrophic": "0.85"}
ORACLE_SS_TYPE_WEIGHTS = {"minimal": ("0.60", "0.30", "0.10"), "baseline": ("0.60", "0.30", "0.10"),
                          "moderate": ("0.50", "0.35", "0.15"), "severe": ("0.30", "0.50", "0.20"),
                          "extreme": ("0.20", "0.45", "0.35"), "catastrophic": ("0.15", "0.45", "0.40")}
ORACLE_SS_COUNTS = {"isolated": (1,), "doublet": (2,), "cluster": (3, 4), "persistent": (4, 5)}
ORACLE_SS_GAP_OF = {"doublet": "MEDIUM", "cluster": "MEDIUM", "persistent": "SHORT"}
ORACLE_SS_DURATION = {"minimal": (2, 6, 12), "baseline": (6, 12, 24), "moderate": (12, 30, 60),
                      "severe": (24, 48, 96), "extreme": (36, 72, 144), "catastrophic": (48, 120, 240)}
ORACLE_SS_GAP = {"SHORT": (6, 18, 36), "MEDIUM": (24, 48, 72)}
ORACLE_SS_BASE = {"minimal": (0.3, 0.10), "baseline": (0.6, 0.15), "moderate": (1.0, 0.20),
                  "severe": (1.8, 0.30), "extreme": (3.0, 0.50), "catastrophic": (5.0, 0.80)}
ORACLE_SS_VARIATION = "0.2"
ORACLE_SS_CORR_PROB = "0.70"
ORACLE_SS_FLOOR = 0.1
ORACLE_SS_BETA = (2.0, 2.0)
ORACLE_SS_WEIGHTS = {"moderate": "0.40", "severe": "0.35", "extreme": "0.20", "catastrophic": "0.05"}
ORACLE_SS_PBASE = {"thames": 35.0, "rhine": 40.0, "danube": 45.0, "mississippi": 55.0}

# The cases.
ORACLE_SS_SEED = 42
ORACLE_SS_COUNT = 10000
ORACLE_SS_SEEDS = 100            # s7.2: 100 independent seeds of 10,000
ORACLE_SS_FORCED_SEED = 20261107  # every category with every forced type
ORACLE_SS_FORCED_COUNT = 400
ORACLE_SS_CATEGORIES = ("minimal", "baseline", "moderate", "severe", "extreme", "catastrophic")

# The document's stated figures.
ORACLE_SS_TABLE9 = {"isolated": 5800, "doublet": 2000, "cluster": 1600, "persistent": 600}
ORACLE_SS_TABLE9_PCT = 2         # s7.2: empirical within 2% of Table 9
ORACLE_SS_CAP_CAT5_PCT = 99      # s6.2: catastrophic durations capped in a 5-storm sequence
ORACLE_SS_CAP_ALL_PCT = 35       # s6.2: share of all duration draws capped, default batch
ORACLE_SS_SCALE_STATED = {"moderate-severe persistent": 20, "catastrophic persistent": 60}  # s6.3, %
ORACLE_SS_SUBSEQUENT_STATED = "0.70"  # Table 8: P(subsequent storm >= first)
ORACLE_SS_SECONDS = 60           # Q2: 10,000 sequences in under a minute
ORACLE_SS_GAUGES_STATED = 52     # s7.3: the classifier result covers all 52 Thames gauges
ORACLE_SS_AUC_STATED = 0.993
ORACLE_SS_EXAMPLE_GAUGE = "GAUGE-8f1d368d"
ORACLE_SS_CLASSIFIER_SUMMARY = "training_summary.json"  # in config.get_classifiers_dir()
ORACLE_SS_STATED_PATHS = ("src/port/src/stressm.py", "src/routes/trading/port_stress.py")
ORACLE_SS_STATED_FILES = ("doublet_sequences.json", "sequences_summary.json", "gauge_summary.json")
ORACLE_SS_STATED_MODULES = {
    "core/data_structures.py": ("SequenceStorm", "StormSequence", "SequenceType", "GapType",
                                "make_storm_id", "make_sequence_id"),
    "generators/sequence_generator.py": ("SequenceGenerator",),
    "generators/batch_generator.py": ("generate_event_set",),
    "generators/duration_sampler.py": ("sample_duration", "DURATION_PARAMS"),
    "generators/gap_sampler.py": ("sample_gap", "GAP_PARAMS"),
    "generators/intensity_sampler.py": ("should_generate_sequence", "sample_sequence_type",
                                        "get_storm_count", "sample_storm_intensity"),
    "utils/validation.py": ("validate_sequence", "validate_event_set", "fits_in_window"),
    "utils/serialization.py": (),
}
ORACLE_SS_ZERO_GAP_H = 1e-6      # a sequence whose gaps total less than this has none
# The code redraws the first storm's variation from the same law with this probability
# (FIRST_STORM_DOMINANT_PROB; the document has no such step). It cannot change delta_0's
# law; the replay mirrors it only so the two random streams stay in step.
ORACLE_SS_REDRAW_PROB = 0.30
