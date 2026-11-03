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
"""The figures DD-001's model document (``flood_risk_v2.0.pdf``) prints, as printed.

Its Tables 4-6 and 8 are generated from the code in the house generator's format:
each value rounded (to 4, 3 and 4 places), then printed by size -- .2f from 1 up,
.4f below. v0.1 of the benchmark tested the filed v1.1; v2.0 replaced it.
"""

ORACLE_DD_PRINTED_T5 = ("0.0000", "0.0500", "0.0722", "0.1389", "0.2500", "0.3250", "0.4000", "0.5000",
                        "0.6000", "0.7500", "0.8500", "0.9500", "1.00")
ORACLE_DD_PRINTED_T6 = (("2.23", "3.54", "5.61"), ("1.49", "2.36", "3.74"), ("1.11", "1.77", "2.81"),
                        ("0.8910", "1.41", "2.25"), ("0.7420", "1.18", "1.87"), ("0.5570", "0.8840", "1.40"))
ORACLE_DD_PRINTED_T7 = (("1.00", "1.00", "1.00", "1.00"), ("0.8465", "0.9048", "0.9512", "0.9753"),
                        ("0.7165", "0.8187", "0.9048", "0.9512"), ("0.5134", "0.6703", "0.8187", "0.9048"),
                        ("0.1889", "0.3679", "0.6065", "0.7788"), ("0.0357", "0.1353", "0.3679", "0.6065"))
ORACLE_DD_ROUND = {"t5": 4, "t6": 3, "t7": 4, "t9": 3}
# Table 8 (depth 1 m, slope 0.003, 3 km): velocity as printed, travel time to 0.01 h.
ORACLE_DD_PRINTED_T9 = {"velocity": ("2.19", "1.37", "0.9130", "0.5480"), "travel": (0.38, 0.61, 0.91, 1.52)}
# Table 7: expected loss after a +/-10% curve shift, by damage ratio, to 4 places.
ORACLE_DD_PRINTED_T8 = ((0.1, 1.1, 0.9), (0.3, 1.1, 0.9), (0.5, 1.1, 0.9), (0.6, 1.0997, 0.9),
                        (0.7, 1.0947, 0.9009), (0.8, 1.0785, 0.9074), (0.9, 1.0559, 0.9228))
# s6.5: retention at 2 km for l = 2, 5 and 10 km; s3.3.4: at 600 m, 2 km and 5 km with the default.
ORACLE_DD_PRINTED_T10 = (0.37, 0.67, 0.82)
ORACLE_DD_PRINTED_S334 = ((600, 0.94), (2000, 0.82), (5000, 0.61))
# s3.4.3 and s8(7): 1 degree = 111 km overstates east-west distance by 61% at 51.5N.
ORACLE_DD_CLAIM_DEG_ERR = 0.61
# Q3: the N x N matrix for 10,000 properties takes 800 MB.
ORACLE_DD_CLAIM_MEMORY = (10_000, 800e6)
