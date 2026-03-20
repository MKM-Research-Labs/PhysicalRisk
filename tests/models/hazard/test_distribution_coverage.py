"""
Tests for models.intensity.distribution — coverage expansion.

Targets uncovered lines: 95, 123, 125, 170-171.
- Line 95: _normal_pdf method
- Line 123: _inverse_normal returns -inf when p <= 0
- Line 125: _inverse_normal returns +inf when p >= 1
- Lines 170-171: high-p branch of _inverse_normal (p > p_high = 0.97575)
"""

import math

import pytest

from models.intensity.distribution import IntensityDistribution


class TestNormalPdf:

    def test_normal_pdf_at_zero(self):
        """Line 95: _normal_pdf(0) should return 1/sqrt(2*pi)."""
        d = IntensityDistribution()
        result = d._normal_pdf(0.0)
        expected = 1.0 / math.sqrt(2 * math.pi)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_normal_pdf_positive(self):
        """Line 95: _normal_pdf at positive value."""
        d = IntensityDistribution()
        result = d._normal_pdf(1.0)
        expected = math.exp(-0.5) / math.sqrt(2 * math.pi)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_normal_pdf_symmetric(self):
        """Line 95: _normal_pdf is symmetric."""
        d = IntensityDistribution()
        assert d._normal_pdf(2.0) == pytest.approx(d._normal_pdf(-2.0))

    def test_normal_pdf_decreases_from_center(self):
        """Line 95: PDF decreases as |x| increases."""
        d = IntensityDistribution()
        assert d._normal_pdf(0) > d._normal_pdf(1) > d._normal_pdf(2)


class TestInverseNormalEdges:

    def test_p_zero_returns_neg_inf(self):
        """Line 123: _inverse_normal(0) returns -inf."""
        d = IntensityDistribution()
        result = d._inverse_normal(0.0)
        assert result == float('-inf')

    def test_p_negative_returns_neg_inf(self):
        """Line 123: _inverse_normal(-0.5) returns -inf."""
        d = IntensityDistribution()
        result = d._inverse_normal(-0.5)
        assert result == float('-inf')

    def test_p_one_returns_pos_inf(self):
        """Line 125: _inverse_normal(1.0) returns +inf."""
        d = IntensityDistribution()
        result = d._inverse_normal(1.0)
        assert result == float('inf')

    def test_p_greater_than_one_returns_pos_inf(self):
        """Line 125: _inverse_normal(1.5) returns +inf."""
        d = IntensityDistribution()
        result = d._inverse_normal(1.5)
        assert result == float('inf')


class TestInverseNormalHighP:

    def test_high_p_branch(self):
        """Lines 170-171: p > p_high (0.97575) uses the upper tail formula."""
        d = IntensityDistribution()
        # p = 0.99 > 0.97575 → triggers lines 170-171
        result = d._inverse_normal(0.99)
        # z for p=0.99 should be approximately 2.326
        assert result == pytest.approx(2.326, abs=0.02)

    def test_high_p_branch_0_98(self):
        """Lines 170-171: p=0.98 also triggers high-p branch."""
        d = IntensityDistribution()
        result = d._inverse_normal(0.98)
        # z for p=0.98 ≈ 2.054
        assert result == pytest.approx(2.054, abs=0.02)

    def test_high_p_is_positive(self):
        """Lines 170-171: high-p branch returns positive value."""
        d = IntensityDistribution()
        for p in [0.976, 0.98, 0.99, 0.995, 0.999]:
            result = d._inverse_normal(p)
            assert result > 0, f"_inverse_normal({p}) = {result} should be positive"

    def test_inverse_roundtrip_high_p(self):
        """Lines 170-171: verify roundtrip CDF(inverse_CDF(p)) ≈ p for high p."""
        d = IntensityDistribution()
        for p in [0.98, 0.99, 0.995]:
            z = d._inverse_normal(p)
            recovered = d._normal_cdf(z)
            assert recovered == pytest.approx(p, abs=0.001)
