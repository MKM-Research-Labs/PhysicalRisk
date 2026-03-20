"""Coverage expansion tests for mortgage.py — missing lines 202-205, 228-230."""

import json
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from tests.port.mortgage.conftest import make_generator, write_property_portfolio


class TestSingleMortgageFailure:
    """Lines 202-205: exception during _generate_single_mortgage is caught and counted."""

    def test_failed_mortgage_is_counted_and_skipped(self, tmp_path):
        """When _generate_single_mortgage raises, the generator continues and
        increments failed_mortgages."""
        prop_path = write_property_portfolio(tmp_path, count=3)
        gen = make_generator(tmp_path)

        original_gen = gen._generate_single_mortgage

        def exploding_gen(index, schema, property_info):
            if index == 1:
                raise RuntimeError("synthetic failure")
            return original_gen(index, schema, property_info)

        gen._generate_single_mortgage = exploding_gen

        result = gen.generate(property_portfolio_path=prop_path)

        assert result["processing_stats"]["failed_mortgages"] == 1
        assert result["processing_stats"]["successful_mortgages"] == 2
        assert len(result["data"]["mortgages"]) == 2

    def test_all_mortgages_fail_returns_empty_list(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=2)
        gen = make_generator(tmp_path)

        gen._generate_single_mortgage = MagicMock(side_effect=RuntimeError("fail"))

        result = gen.generate(property_portfolio_path=prop_path)

        assert result["processing_stats"]["failed_mortgages"] == 2
        assert result["data"]["mortgages"] == []


class TestSaveFailure:
    """Lines 228-230: exception when saving JSON to disk is re-raised."""

    def test_save_error_is_reraised(self, tmp_path):
        prop_path = write_property_portfolio(tmp_path, count=1)
        gen = make_generator(tmp_path)

        # Make the output dir read-only so json.dump fails
        read_only_dir = tmp_path / "locked_output"
        read_only_dir.mkdir()
        gen.output_dir = read_only_dir

        # Write one successful mortgage, then make the file unwritable
        # Simpler: patch open to raise on write
        with patch("builtins.open", side_effect=[
            open(prop_path, "r"),  # first open reads property file
            OSError("disk full"),  # second open for writing fails
        ]):
            with pytest.raises(OSError, match="disk full"):
                gen.generate(property_portfolio_path=prop_path)
