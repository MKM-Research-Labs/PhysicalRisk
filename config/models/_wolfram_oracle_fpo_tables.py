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
"""The figures MKM-FPO-001's model document prints, as printed (v2.0, 03-Nov-2026).

Its tables are generated from the code; these are what the PDF says, read off its
source, so the benchmark tests the document and not the generator.
"""

# s4.3, Table 2: the coefficients of the terms in order. s3.3, Table 1: the envelope's
# knots, (w/s, earliest hour).
ORACLE_FPO_DOC_COEFFS = ('32.871867', '-12.801048', '-7.540193', '44.826451', '-2.848226', '54.512653', '-0.756589', '-29.568283', '6.254275', '-1.293810')
ORACLE_FPO_DOC_ENVELOPE = (
    ('0.326', '0.0'),
    ('0.35', '2.3'),
    ('0.4', '4.7'),
    ('0.45', '6.1'),
    ('0.5', '7.5'),
    ('0.55', '8.9'),
    ('0.6', '10.8'),
    ('0.65', '12.9'),
    ('0.7', '15.1'),
    ('0.75', '18.4'),
    ('0.8', '22.0'),
    ('0.85', '24.9'),
    ('0.9', '29.3'),
    ('0.95', '35.7'),
    ('1', '37.4'))

# s7.1, Table 4: P(flood) by w/s and hour (s = 6.58 m), and the cells marked as held.
ORACLE_FPO_T_SEVERE = 6.58
ORACLE_FPO_T_LEVELS = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0)
ORACLE_FPO_T_HOURS = (0, 6, 12, 24, 48, 84, 120, 167)
ORACLE_FPO_PRINTED_GRID = (
    (0.001, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.046, 0.029, 0.001, 0.0, 0.0, 0.0, 0.0, 0.0),
    (0.334, 0.388, 0.352, 0.043, 0.0, 0.0, 0.0, 0.0),
    (0.608, 0.608, 0.664, 0.49, 0.034, 0.0, 0.0, 0.0),
    (0.896, 0.896, 0.891, 0.801, 0.293, 0.008, 0.0, 0.0),
    (0.99, 0.99, 0.99, 0.969, 0.733, 0.079, 0.003, 0.0),
    (0.999, 0.999, 0.999, 0.999, 0.97, 0.461, 0.036, 0.001),
    (1.0, 1.0, 1.0, 1.0, 0.999, 0.937, 0.348, 0.013),
    (1.0, 1.0, 1.0, 1.0, 1.0, 0.988, 0.714, 0.054),
    (1.0, 1.0, 1.0, 1.0, 1.0, 0.997, 0.906, 0.165),
    (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0))
ORACLE_FPO_PRINTED_HELD = ((0.4, 0), (0.5, 0), (0.5, 6), (0.6, 0), (0.6, 6), (0.7, 0), (0.7, 6), (0.7, 12), (0.8, 0), (0.8, 6), (0.8, 12), (0.9, 0), (0.9, 6), (0.9, 12), (0.9, 24), (0.95, 0), (0.95, 6), (0.95, 12), (0.95, 24), (0.99, 0), (0.99, 6), (0.99, 12), (0.99, 24))

# s5, Table 3: per gauge on the held-out storms, (near MAE, near bias, near share over
# 0.1 in percent, below MAE). s4.1: the fitted and held-out state counts.
ORACLE_FPO_PRINTED_FIT = (
    (0.059, 0.0247, 20.0, 0.0125),
    (0.0408, -0.007, 10.0, 0.0087),
    (0.0542, 0.0128, 16.0, 0.0198),
    (0.0658, -0.0343, 21.0, 0.0203),
    (0.0465, 0.0171, 15.0, 0.0075),
    (0.0518, 0.0087, 17.0, 0.01),
    (0.0478, -0.0015, 15.0, 0.0064),
    (0.0557, -0.0081, 16.0, 0.0179),
    (0.0578, 0.0246, 21.0, 0.0092),
    (0.0628, -0.0288, 20.0, 0.0166),
    (0.0566, 0.0188, 18.0, 0.0174))
ORACLE_FPO_PRINTED_STATES = (1807233, 1807896)

# s3.1: t at hour 0.
ORACLE_FPO_PRINTED_T0 = -5.12
