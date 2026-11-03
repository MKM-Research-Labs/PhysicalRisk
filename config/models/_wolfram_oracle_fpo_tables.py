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
"""The figures MKM-FPO-001's model document prints, as printed (v1.0, s8 and s5).

No generator ever produced these tables: ``sensitivity_tables.tex`` was a static file.
"""

# Table 1 (s8): P(flood) by level (m) and hour, severe threshold 6.58 m.
ORACLE_FPO_T1_SEVERE = 6.58
ORACLE_FPO_T1_LEVELS = (4.0, 4.5, 5.0, 5.5, 6.0, 6.3, 6.58, 7.0, 7.5)
ORACLE_FPO_T1_HOURS = (0, 12, 24, 48, 96, 167)
ORACLE_FPO_PRINTED_T1 = (
    (0.00, 0.00, 0.00, 0.00, 0.00, 0.00), (0.00, 0.00, 0.00, 0.00, 0.01, 0.02),
    (0.00, 0.00, 0.01, 0.02, 0.07, 0.15), (0.01, 0.02, 0.05, 0.13, 0.33, 0.53),
    (0.07, 0.14, 0.25, 0.45, 0.71, 0.85), (0.20, 0.34, 0.49, 0.69, 0.87, 0.94),
    (0.42, 0.58, 0.71, 0.84, 0.94, 0.97), (0.72, 0.82, 0.89, 0.95, 0.98, 0.99),
    (0.93, 0.96, 0.97, 0.99, 1.00, 1.00))
# Table 2 (s8): (level, hour, GBM, poly) at selected points, rate of rise zero.
ORACLE_FPO_PRINTED_T2 = ((5.00, 24, 0.01, 0.01), (5.50, 48, 0.14, 0.13), (6.00, 24, 0.27, 0.25),
                         (6.30, 48, 0.72, 0.69), (6.58, 96, 0.93, 0.94), (7.00, 48, 0.96, 0.95))
# s4.2 fit metrics against the GBM surface of the fitted gauge; s9.1 the cubic's R^2.
ORACLE_FPO_PRINTED_FIT = {"r2": 0.9395, "mae": 0.0456, "rmse": 0.0986}
ORACLE_FPO_PRINTED_CUBIC_R2 = 0.97
# s3.2: t at hour 0; s8: P at the severe level from hour 0 to hour 167.
ORACLE_FPO_PRINTED_T0 = -5.1
ORACLE_FPO_PRINTED_AT_SEVERE = (0.42, 0.97)
