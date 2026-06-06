# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage validation — completeness, full chain (part 5).
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


class TestValidateFullChain:
    """validate_full_chain: end-to-end consistency check."""

    def test_empty_manifest(self):
        from lineage.validation import validate_full_chain
        from lineage.manifest import DEPENDENCY_GRAPH, OPTIONAL_STEPS
        with patch("lineage.validation.load_manifest", return_value=_make_manifest({})):
            result = validate_full_chain()
        assert not result["is_consistent"]
        # Every required (non-optional) step should appear as missing;
        # opt-in steps absent from the manifest are not flagged.
        assert len(result["missing_steps"]) == len(
            set(DEPENDENCY_GRAPH) - OPTIONAL_STEPS)

    def test_consistent_chain(self):
        from lineage.validation import validate_full_chain
        # Build a minimal consistent manifest: root steps only
        manifest = _make_manifest({
            "gauges": {"inputs": {}, "outputs": {"gauge.json": {"hash": "a"}}},
            "counterparties": {"inputs": {}, "outputs": {"counterparty.json": {"hash": "b"}}},
            "synthetic_gauges": {
                "inputs": {"gauge.json": {"hash": "a"}},
                "outputs": {"gauge.json": {"hash": "a2"}},
            },
            "properties": {
                "inputs": {"gauge.json": {"hash": "a2"}},
                "outputs": {"property.json": {"hash": "c"}},
            },
            "mortgages": {
                "inputs": {"property.json": {"hash": "c"}},
                "outputs": {"loan.json": {"hash": "d"}},
            },
            "gaugehd": {
                "inputs": {"gauge.json": {"hash": "a2"}},
                "outputs": {"gaugehd/": {"hash": "e"}},
            },
            "stressm": {
                "inputs": {"gauge.json": {"hash": "a2"}, "gaugehd/": {"hash": "e"}},
                "outputs": {
                    "gaugets/": {"hash": "f"},
                    "stress_storms/": {"hash": "g"},
                    "storm_sequences.json": {"hash": "h"},
                    "sequence_gauge/": {"hash": "i"},
                },
            },
            "hazard": {
                "inputs": {"gauge.json": {"hash": "a2"}, "gaugets/": {"hash": "f"}},
                "outputs": {"gaugehc.json": {"hash": "j"}, "gaugets/": {"hash": "f"}},
            },
            "propertyts": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertyts/": {"hash": "k"}},
            },
            "propertytsd": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytsd/": {"hash": "k1"}},
            },
            "propertytse": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytse/": {"hash": "k2"}},
            },
            "propertyhc": {
                "inputs": {
                    "propertyts/": {"hash": "k"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertyhc.json": {"hash": "l"}},
            },
            "propertyshd": {
                "inputs": {
                    "propertytsd/": {"hash": "k1"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertyshd.json": {"hash": "l1"}},
            },
            "propertyshe": {
                "inputs": {
                    "propertytse/": {"hash": "k2"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertyshe.json": {"hash": "l2"}},
            },
            "propertytsb": {
                "inputs": {
                    "property.json": {"hash": "c"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"propertytsb/": {"hash": "k3"}},
            },
            "propertybri": {
                "inputs": {
                    "propertytsb/": {"hash": "k3"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"propertybri.json": {"hash": "l3"}},
            },
            "blotter": {
                "inputs": {"gaugehc.json": {"hash": "j"}, "counterparty.json": {"hash": "b"}},
                "outputs": {"prs/": {"hash": "m"}},
            },
            "typhoon": {
                "inputs": {},
                "outputs": {
                    "typhoon/ensemble.json": {"hash": "n"},
                    "typhoon/events/": {"hash": "o"},
                    "typhoon/windts/": {"hash": "p"},
                    "typhoon/damage/": {"hash": "q"},
                },
            },
            "commercial": {
                "inputs": {},
                "outputs": {
                    "commercial.json": {"hash": "r"},
                    "commercial_loan.json": {"hash": "s"},
                },
            },
            "commercialts": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialts/": {"hash": "t"}},
            },
            "commercialtsd": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialtsd/": {"hash": "t1"}},
            },
            "commercialtse": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialtse/": {"hash": "t2"}},
            },
            "commercialhc": {
                "inputs": {
                    "commercialts/": {"hash": "t"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialhc.json": {"hash": "u"}},
            },
            "commercialshd": {
                "inputs": {
                    "commercialtsd/": {"hash": "t1"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialshd.json": {"hash": "u1"}},
            },
            "commercialshe": {
                "inputs": {
                    "commercialtse/": {"hash": "t2"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialshe.json": {"hash": "u2"}},
            },
            "commercialtsb": {
                "inputs": {
                    "commercial.json": {"hash": "r"},
                    "gauge.json": {"hash": "a2"},
                    "gaugets/": {"hash": "f"},
                },
                "outputs": {"commercialtsb/": {"hash": "t3"}},
            },
            "commercialbri": {
                "inputs": {
                    "commercialtsb/": {"hash": "t3"},
                    "gaugehc.json": {"hash": "j"},
                    "gauge.json": {"hash": "a2"},
                },
                "outputs": {"commercialbri.json": {"hash": "u3"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = validate_full_chain()
        assert result["is_consistent"]
        assert result["stale_steps"] == []
        assert result["missing_steps"] == []

    def test_stale_step_detected(self):
        from lineage.validation import validate_full_chain
        manifest = _make_manifest({
            "gauges": {"inputs": {}, "outputs": {"gauge.json": {"hash": "new"}}},
            "properties": {
                "inputs": {"gauge.json": {"hash": "old"}},
                "outputs": {"property.json": {"hash": "x"}},
            },
        })
        with patch("lineage.validation.load_manifest", return_value=manifest):
            result = validate_full_chain()
        assert not result["is_consistent"]
        assert "properties" in result["stale_steps"]
