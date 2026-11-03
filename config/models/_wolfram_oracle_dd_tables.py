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
"""The figures DD-001's filed document (``flood_risk.pdf`` v1.1) prints, as printed.

Tables 5-7 came from the sensitivity generator, which rounded each value (to 4, 3
and 4 places) and then formatted it by size: .2f from 1 up, .4f below.
"""

ORACLE_DD_PRINTED_T5 = ("0.0000", "0.0500", "0.0722", "0.1389", "0.2500", "0.3250", "0.4000", "0.5000",
                        "0.6000", "0.7500", "0.8500", "0.9500", "1.00")
ORACLE_DD_PRINTED_T6 = (("2.23", "3.54", "5.61"), ("1.49", "2.36", "3.74"), ("1.11", "1.77", "2.81"),
                        ("0.8910", "1.41", "2.25"), ("0.7420", "1.18", "1.87"), ("0.5570", "0.8840", "1.40"))
ORACLE_DD_PRINTED_T7 = (("1.00", "1.00", "1.00", "1.00"), ("0.6065", "0.7788", "0.8465", "0.9048"),
                        ("0.3679", "0.6065", "0.7165", "0.8187"), ("0.1353", "0.3679", "0.5134", "0.6703"),
                        ("0.0067", "0.0821", "0.1889", "0.3679"), ("0.0000", "0.0067", "0.0357", "0.1353"))
ORACLE_DD_ROUND = {"t5": 4, "t6": 3, "t7": 4}
# Table 9 (depth 1 m, slope 0.003): mean velocity (m/s) and travel time (h) by n.
ORACLE_DD_PRINTED_T9 = {"velocity": (0.64, 0.40, 0.27, 0.16), "travel": (1.3, 2.1, 3.1, 5.2)}
# Table 10: attenuation at 2 km for l = 1, 2 and 5 km; s3.3.4: e^-1 and e^-3.
ORACLE_DD_PRINTED_T10 = (0.14, 0.37, 0.67)
ORACLE_DD_PRINTED_S334 = (0.37, 0.05)
# Table 8: a +/-10% shift gives expected loss 1.08x / 0.92x, VaR99 +7.5% / -7.1%, ES99 +8.2% / -7.8%.
ORACLE_DD_PRINTED_T8 = {"el": (1.08, 0.92), "var99": (0.075, -0.071), "es99": (0.082, -0.078)}
# s8(8): 1 degree = 111 km "introduces approximately 2% error at 51.5N" east-west.
ORACLE_DD_CLAIM_DEG_ERR = 0.02
# s9.3: the N x N matrix for 10,000 properties takes about 800 MB.
ORACLE_DD_CLAIM_MEMORY = (10_000, 800e6)
