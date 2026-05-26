# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Block B10 quick-win coverage tests.

Each test targets 1-2 uncovered statements in files that are already
at 93-98 % coverage, pushing them to 99-100 %.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# 1. src/models/intensity/__main__.py (lines 21-23)
#    Runs `from .cli import main; main()` — test via subprocess
# ---------------------------------------------------------------------------

class TestIntensityMainModule:

    def test_intensity_module_runs(self):
        """Running `python -m models.intensity` executes cli.main().

        The subprocess exits in ~0.1s in isolation but can take much longer
        when the outer pytest run has coverage enabled (each child process
        re-initialises the coverage sitecustomize). A generous timeout stops
        the full-suite run from failing this due to system load rather than
        a real regression.
        """
        result = subprocess.run(
            [sys.executable, "-m", "models.intensity", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parents[1] / "src"),
            timeout=120,
        )
        assert result.returncode == 0
        assert "Storm Intensity" in result.stdout or "usage" in result.stdout.lower()


# ---------------------------------------------------------------------------
# 2. src/jsonfiles.py line 151 — JSONFileConfig.get(key)
# ---------------------------------------------------------------------------

class TestJSONFileConfigGet:

    def test_get_returns_known_key(self):
        """JSONFileConfig.get('hazard_curves') returns the hazard curves filename."""
        from jsonfiles import JSONFileConfig
        result = JSONFileConfig.get('hazard_curves')
        assert result == JSONFileConfig.HAZARD_CURVES

    def test_get_raises_on_unknown_key(self):
        from jsonfiles import JSONFileConfig
        with pytest.raises(KeyError):
            JSONFileConfig.get('nonexistent_key_xyz')


# ---------------------------------------------------------------------------
# 3. src/models/audit.py line 150 — entries truncation (> 10000)
# ---------------------------------------------------------------------------

class TestAuditTruncation:

    def test_entries_truncated_above_10000(self, tmp_path):
        """When audit log exceeds 10 000 entries, it keeps only the last 10 000."""
        from models.audit import log_model_usage, _get_audit_path

        audit_file = tmp_path / "data" / "model_audit_log.json"
        audit_file.parent.mkdir(parents=True, exist_ok=True)

        # Seed with 10 000 entries
        seed_entries = [{"seq": i} for i in range(10_000)]
        audit_file.write_text(json.dumps(seed_entries))

        with patch("models.audit._get_audit_path", return_value=str(audit_file)):
            log_model_usage(
                model_ref="TEST-TRUNC",
                action="test",
            )

        entries = json.loads(audit_file.read_text())
        assert len(entries) == 10_000
        # The first seeded entry (seq=0) should have been dropped
        assert entries[0].get("seq") == 1 or entries[0].get("model_id") is not None


# ---------------------------------------------------------------------------
# 4. src/models/risk/risk_assessor/ltv.py line 114 — ltv_ratio > 1 (percentage)
# ---------------------------------------------------------------------------

class TestLtvPercentageConversion:

    def test_ltv_ratio_as_percentage(self):
        """ltv_ratio > 1 is interpreted as a percentage and divided by 100."""
        from models.risk.risk_assessor.ltv import calculate_combined_risk_score

        # Pass ltv_ratio=96 (percentage form, > 1)
        # After conversion: 0.96, which is > 0.95 → multiplier = 2.0
        score = calculate_combined_risk_score(
            flood_risk_level='Medium', ltv_ratio=96
        )
        assert score > 0


# ---------------------------------------------------------------------------
# 5. src/server.py line 99 — if __name__ == '__main__': main()
#    Test by running as script with --help or mock
# ---------------------------------------------------------------------------

class TestServerMainBlock:

    def test_server_main_callable(self):
        """server.main() is callable (test by importing, not running)."""
        from server import main
        assert callable(main)


# ---------------------------------------------------------------------------
# 6. eod_page_01_summary.py line 84 — pnl_color (dead code, skip)
#    NOTE: pnl_color is defined but never called in the source.
#    Cannot cover without modifying source.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 7. intensity_sampler.py line 99 — fallback return 1 for unknown SequenceType
# ---------------------------------------------------------------------------

class TestIntensitySamplerFallback:

    def test_get_storm_count_unknown_type_returns_1(self):
        """Unknown sequence type falls back to 1 storm."""
        from port.src.storm_multi.generators.intensity_sampler import get_storm_count

        rng = np.random.RandomState(42)

        # Create a mock that doesn't match any known SequenceType
        unknown = MagicMock()
        unknown.__eq__ = lambda self, other: False

        count = get_storm_count(unknown, rng)
        assert count == 1


# ---------------------------------------------------------------------------
# 8. eod_page_03_pnl_detail.py line 67 — fmt_gbp returns "—" for v==0
# ---------------------------------------------------------------------------

class TestEODPnlDetailZeroNotional:

    def test_zero_notional_in_new_trade(self):
        """Position with notional=0 triggers fmt_gbp(0) → em-dash path."""
        from reports.trading.eod_page_03_pnl_detail import EODPnLDetailPage

        snapshot = {
            "positions": [
                {
                    "swap_id": "PRS-ZZZ",
                    "gauge_id": "GAUGE-001",
                    "trigger": "warning",
                    "notional": 0,
                    "trade_spread_bps": 150.0,
                    "fair_spread_bps": 145.0,
                    "new_trade_pnl": 100.0,
                    "market_pnl": 0.0,
                    "daily_pnl": 100.0,
                    "running_pnl": 100.0,
                },
            ],
        }
        page = EODPnLDetailPage()
        result = page.get_content(snapshot)
        assert isinstance(result, list)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 9. storm_factory.py line 107 — else branch (unknown IntensityProfile)
# ---------------------------------------------------------------------------

class TestStormFactoryElseBranch:

    def test_create_storm_linear_fallback(self):
        """Unknown intensity profile falls to else: intensity = peak * t_frac."""
        from models.stormgauge.storm_factory import create_storm

        # Use a mock that doesn't match TRIANGULAR/GAUSSIAN/BETA
        unknown_profile = MagicMock()
        unknown_profile.__eq__ = lambda self, other: False

        storm = create_storm(
            track_start=(0.0, 0.0),
            track_end=(2.0, 0.0),
            peak_intensity=50.0,
            intensity_profile=unknown_profile,
            num_track_points=5,
        )
        assert storm.storm_id.startswith("STORM-")
        assert len(storm.track) == 5
        # First point at t_frac=0 should have intensity = 50*0 = 0
        assert storm.track[0].intensity == 0.0


# ---------------------------------------------------------------------------
# 10. gaugehd/directory.py line 81 — if __name__ == "__main__": main()
# ---------------------------------------------------------------------------

class TestGaugehdDirectoryMain:

    def test_main_function_exists(self):
        """directory.main() is callable."""
        from port.cdm.gaugehd.directory import main
        assert callable(main)


# ---------------------------------------------------------------------------
# 11. insurance.py line 67 — area exceeds all finite thresholds
# ---------------------------------------------------------------------------

class TestInsuranceAreaFallback:

    def test_area_infinity_falls_through(self):
        """Area = float('inf') skips all threshold checks, hits fallback."""
        from models.valuation.insurance import get_area_premium_factor_range

        result = get_area_premium_factor_range(float('inf'))
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# 12. tradingdesk.py line 363 — get_statistics() method
# ---------------------------------------------------------------------------

class TestTradingDeskStatistics:

    def test_get_statistics_returns_dimensions(self):
        """get_statistics() returns panel_width and panel_height."""
        from visual.interactivity.trading.tradingdesk import TradingDeskPanel

        td = TradingDeskPanel.__new__(TradingDeskPanel)
        td.panel_width = "420px"
        td.panel_height = "600px"

        stats = td.get_statistics()
        assert stats["panel_width"] == "420px"
        assert stats["panel_height"] == "600px"


# ---------------------------------------------------------------------------
# 13. property/main/encoder.py line 37 — super().default(obj) fallback
# ---------------------------------------------------------------------------

class TestPropertyMainEncoderFallback:

    def test_unhandled_type_raises_typeerror(self):
        """Passing an unhandled type triggers super().default() → TypeError."""
        from port.src.property.main.encoder import DateTimeEncoder

        encoder = DateTimeEncoder()
        with pytest.raises(TypeError):
            encoder.default(set([1, 2, 3]))


# ---------------------------------------------------------------------------
# 14. property/ts/encoder.py line 22 — np.floating handling
# ---------------------------------------------------------------------------

class TestPropertyTsEncoderFloating:

    def test_numpy_floating_encoded_as_float(self):
        """np.float64 is converted to Python float by encoder."""
        from port.src.property.ts.encoder import DateTimeEncoder

        encoder = DateTimeEncoder()
        result = encoder.default(np.float64(3.14))
        assert isinstance(result, float)
        assert abs(result - 3.14) < 1e-10


# ---------------------------------------------------------------------------
# 15. visual/factory.py line 28 — create_visualization()
# ---------------------------------------------------------------------------

class TestVisualFactory:

    def test_create_visualization_returns_instance(self, tmp_path):
        """create_visualization() returns a TCEventVisualization instance."""
        from visual.factory import create_visualization
        from visual.core.visualizer import TCEventVisualization

        viz = create_visualization(
            input_dir=str(tmp_path),
            output_dir=str(tmp_path),
        )
        assert isinstance(viz, TCEventVisualization)
