"""Tests for src/reports/port/generator.py — PortReportGenerator init and generate."""

import pytest
from pathlib import Path

from reports.port.generator import PortReportGenerator


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_input_dir_set(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert gen.input_dir == tmp_path

    def test_output_path_explicit(self, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(tmp_path, output_path=out)
        assert gen.output_path == out

    def test_styles_initialised(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert gen.title_style is not None
        assert gen.body_style is not None
        assert gen.section_style is not None

    def test_input_dir_accepts_string(self, tmp_path):
        gen = PortReportGenerator(str(tmp_path), output_path=tmp_path / 'out.pdf')
        assert isinstance(gen.input_dir, Path)

    def test_default_output_path_uses_audit_dir(self, tmp_path, monkeypatch):
        """When output_path is None, default to
        ``<output>/audit/archive/port_<catchment>.pdf`` using
        config.get_output_dir(). Port deliverables live under audit/archive/
        so they stay out of the `app.py test` audit root.
        """
        from config import config

        out_root = tmp_path / 'output'
        monkeypatch.setattr(config, 'get_output_dir', lambda: out_root)

        gen = PortReportGenerator(tmp_path / 'thames')
        # audit/archive dir was created
        assert (out_root / 'audit' / 'archive').is_dir()
        # output path is the audit / archive / port_<input_dir.name>.pdf
        assert gen.output_path == out_root / 'audit' / 'archive' / 'port_thames.pdf'


# ---------------------------------------------------------------------------
# generate() — end-to-end PDF creation
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_produces_pdf_file(self, populated_input, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        result = gen.generate()
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_pdf_starts_with_magic_bytes(self, populated_input, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        gen.generate()
        with open(out, 'rb') as f:
            assert f.read(5) == b'%PDF-'

    def test_returns_path(self, populated_input, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        result = gen.generate()
        assert isinstance(result, Path)

    def test_generate_with_empty_data(self, empty_input, tmp_path):
        """Even with completely empty input, PDF should still generate."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(empty_input, output_path=out)
        result = gen.generate()
        assert result.exists()
        assert result.stat().st_size > 0

    def test_generate_with_minimal_data(self, minimal_input, tmp_path):
        """Minimal data (empty arrays) should produce valid PDF."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(minimal_input, output_path=out)
        result = gen.generate()
        assert result.exists()

    def test_pdf_has_multiple_pages(self, populated_input, tmp_path):
        """With populated data, PDF should have multiple pages (from PageBreaks)."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        gen.generate()
        # Rough check: PDF should be large enough for multiple pages
        assert out.stat().st_size > 5000

    def test_output_path_creates_parent_dirs(self, populated_input, tmp_path):
        out = tmp_path / 'nested' / 'deep' / 'report.pdf'
        out.parent.mkdir(parents=True, exist_ok=True)
        gen = PortReportGenerator(populated_input, output_path=out)
        result = gen.generate()
        assert result.exists()

    def test_catchment_name_from_input_dir(self, populated_input, tmp_path):
        """The generator uses input_dir.name as the catchment name."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        assert gen.input_dir.name == 'thames'
