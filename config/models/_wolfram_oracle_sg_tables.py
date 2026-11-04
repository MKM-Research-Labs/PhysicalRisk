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
"""The figures MKM-SG-001's model document v2.0 prints, as printed (``storm_gauge_v2.0.pdf``).

Parsed from the document's source; the benchmark judges each against the code. Tables
8 and 9 are keyed by (peak, degrees north) and (constant, hours).
"""

ORACLE_SG_PRINTED_T4 = (("1.00", "1.00", "1.00"), ("0.9692", "0.7788", "0.7500"),
                        ("0.8825", "0.6065", "0.5000"), ("0.7548", "0.4724", "0.2500"),
                        ("0.6065", "0.3679", "0.0000"), ("0.3247", "0.2231", "0.0000"),
                        ("0.1353", "0.1353", "0.0000"))
ORACLE_SG_PRINTED_T5 = (
    ("0.9930", "1.73", "2.39", "3.01", "3.60"),
    ("1.24", "2.16", "2.99", "3.76", "4.50"),
    ("1.49", "2.59", "3.59", "4.52", "5.40"))
ORACLE_SG_T5_SENSITIVITIES = (0.8, 1.0, 1.2)
ORACLE_SG_PRINTED_T8 = (
    ((40, 0.0), ("40.0", "3.96", "2.5", "0.0", "0.0", "0.0", "0.00")),
    ((40, 0.1), ("34.3", "3.66", "2.5", "0.0", "0.0", "0.0", "0.00")),
    ((40, 0.2), ("21.6", "2.96", "2.5", "0.0", "0.0", "0.0", "0.00")),
    ((60, 0.0), ("60.0", "4.94", "2.5", "10.5", "0.0", "0.0", "6.20")),
    ((60, 0.1), ("51.4", "4.52", "2.5", "8.0", "0.0", "0.0", "2.68")),
    ((60, 0.2), ("32.3", "3.56", "2.5", "0.0", "0.0", "0.0", "0.00")),
    ((80, 0.0), ("80.0", "5.85", "2.5", "14.5", "6.5", "0.0", "16.17")),
    ((80, 0.1), ("68.5", "5.33", "2.5", "12.5", "1.0", "0.0", "10.24")),
    ((80, 0.2), ("43.1", "4.11", "2.5", "3.5", "0.0", "0.0", "0.29")),
    ((100, 0.0), ("100.0", "6.72", "2.5", "17.5", "10.5", "5.0", "27.36")),
    ((100, 0.1), ("85.7", "6.10", "2.5", "15.5", "8.0", "0.0", "19.27")),
    ((100, 0.2), ("53.9", "4.65", "2.5", "8.5", "0.0", "0.0", "3.63")),
)
ORACLE_SG_PRINTED_T9 = (
    (("lag", 1), ("6.72", "1.5", "17.5", "27.36")),
    (("lag", 2), ("6.72", "2.5", "17.5", "27.36")),
    (("lag", 4), ("6.72", "4.5", "17.5", "27.36")),
    (("rise", 0.5), ("6.95", "2.0", "18.5", "30.66")),
    (("rise", 1), ("6.72", "2.5", "17.5", "27.36")),
    (("rise", 2), ("6.31", "3.0", "16.0", "21.53")),
    (("rise", 4), ("5.53", "4.0", "13.0", "12.17")),
    (("decay", 6), ("6.72", "2.5", "13.5", "21.38")),
    (("decay", 12), ("6.72", "2.5", "17.5", "27.36")),
    (("decay", 24), ("6.72", "2.5", "26.0", "38.07")),
)
ORACLE_SG_PRINTED_T6 = ("0.135", "0.135", "0.0")
ORACLE_SG_PRINTED_T7 = ("0.707", "0.574", "0.500", "0.354")
ORACLE_SG_PRINTED_GAUSS = ("60.7", "13.5")      # s3.3.1: % of on-track intensity at sigma, 2 sigma
