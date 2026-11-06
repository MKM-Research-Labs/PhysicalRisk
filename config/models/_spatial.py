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
"""Spatial Interpolation Model parameters (MKM-SP-001 v2.0, ``models/floodrisk/spatial``).

Eq. 1's sphere (m); s3.2's IDW power and the distance within which a gauge's own value
is returned (m); and s3.4's conversion of a degree to kilometres in the correlation
matrix, which MKM-DD-001 v2.0 documents as Eq. 9 and which takes no account of
latitude (it overstates east-west separation by 61% at 51.5 N).
"""

spatial_earth_radius_m = 6371000.0
spatial_idw_power = 2.0
spatial_idw_min_distance_m = 1.0
spatial_km_per_degree = 111.0
