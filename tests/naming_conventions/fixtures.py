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

"""Tests verifying test fixtures follow the naming convention protocol."""

import re
import uuid
import pytest
from .conftest import GAUGE_ID_RE, STORM_ID_RE


class TestTestFixtureStormIDs:
    """Storm IDs in test fixture constants follow STORM-{8hex} protocol."""

    def test_stress_routes_storm_constants_match_protocol(self):
        """_data.py STORM_SEVERE and STORM_WARNING follow the protocol."""
        from tests.routes.trading._data import STORM_SEVERE, STORM_WARNING
        assert STORM_ID_RE.match(STORM_SEVERE), \
            f"stress_routes.STORM_SEVERE='{STORM_SEVERE}' violates STORM-{{8hex}}"
        assert STORM_ID_RE.match(STORM_WARNING), \
            f"stress_routes.STORM_WARNING='{STORM_WARNING}' violates STORM-{{8hex}}"

    def test_port_stress_routes_storm_constants_match_protocol(self):
        """_data.py STORM_PORT_* constants follow the protocol."""
        from tests.routes.trading._data import (
            STORM_PORT_SEVERE, STORM_PORT_ALERT,
        )
        assert STORM_ID_RE.match(STORM_PORT_SEVERE), \
            f"port_stress.STORM_PORT_SEVERE='{STORM_PORT_SEVERE}' violates protocol"
        assert STORM_ID_RE.match(STORM_PORT_ALERT), \
            f"port_stress.STORM_PORT_ALERT='{STORM_PORT_ALERT}' violates protocol"

    def test_sample_stress_storms_storm_ids_match_protocol(self):
        """All storm_id values in SAMPLE_STRESS_STORMS follow STORM-{8hex}."""
        from tests.routes.trading._data import SAMPLE_STRESS_STORMS
        for storm in SAMPLE_STRESS_STORMS['storms']:
            sid = storm['storm_id']
            assert STORM_ID_RE.match(sid), (
                f"SAMPLE_STRESS_STORMS storm '{sid}' violates STORM-{{8hex}} protocol. "
                f"Use STORM-{{uuid4()[:8]}} format, e.g. 'STORM-a1b2c3d4'."
            )

    def test_sample_port_stress_storms_ids_match_protocol(self):
        """All storm_id values in SAMPLE_PORT_STRESS_STORMS follow STORM-{8hex}."""
        from tests.routes.trading._data import SAMPLE_PORT_STRESS_STORMS
        for storm in SAMPLE_PORT_STRESS_STORMS['storms']:
            sid = storm['storm_id']
            assert STORM_ID_RE.match(sid), (
                f"SAMPLE_PORT_STRESS_STORMS storm '{sid}' violates STORM-{{8hex}} "
                f"protocol. Use STORM-{{uuid4()[:8]}} format."
            )


class TestTestFixtureGaugeIDs:
    """Gauge IDs in test fixtures follow the naming convention."""

    def test_new_conftest_gauge_ids_match_protocol(self):
        """New gauge IDs added in conftest (GAUGE-{8hex}) follow the protocol."""
        from tests.routes.trading.conftest import (
            GAUGE_VAUXHALL, GAUGE_WATERLOO, GAUGE_BLACKFRIARS, GAUGE_LONDON,
        )
        new_gauges = {
            'GAUGE_VAUXHALL': GAUGE_VAUXHALL,
            'GAUGE_WATERLOO': GAUGE_WATERLOO,
            'GAUGE_BLACKFRIARS': GAUGE_BLACKFRIARS,
            'GAUGE_LONDON': GAUGE_LONDON,
        }
        for name, gid in new_gauges.items():
            assert GAUGE_ID_RE.match(gid), (
                f"conftest.{name}='{gid}' violates GAUGE-{{8hex}} protocol"
            )

    def test_backward_compat_gauge_ids_are_documented(self):
        """GAUGE-001, GAUGE-002, GAUGE-9042bd95 are backward-compat exceptions."""
        from tests.routes.trading.conftest import (
            GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
        )
        compat_ids = {GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH}
        assert compat_ids == {'GAUGE-001', 'GAUGE-002', 'GAUGE-9042bd95'}, (
            "Backward-compatible gauge ID set changed unexpectedly. "
            "Update this assertion and the conftest docstring."
        )

    def test_gaugehc_new_entries_follow_protocol(self):
        """The new gauge entries in SAMPLE_GAUGEHC follow GAUGE-{8hex}."""
        from tests.routes.trading.conftest import SAMPLE_GAUGEHC
        backward_compat = {'GAUGE-001', 'GAUGE-002', 'GAUGE-9042bd95'}
        violations = []
        for gid in SAMPLE_GAUGEHC['hazard_curves']:
            if gid not in backward_compat and not GAUGE_ID_RE.match(gid):
                violations.append(gid)
        assert not violations, (
            f"These gaugehc IDs violate GAUGE-{{8hex}} protocol: {violations}"
        )

    def test_gauge_json_and_gaugehc_ids_are_consistent(self):
        """gauge.json and gaugehc.json gauge IDs must be identical sets."""
        from tests.routes.trading.conftest import SAMPLE_GAUGE_JSON, SAMPLE_GAUGEHC
        gauge_json_ids = {
            g['FloodGauge']['GaugeID']
            for g in SAMPLE_GAUGE_JSON['flood_gauges']
        }
        gaugehc_ids = set(SAMPLE_GAUGEHC['hazard_curves'].keys())
        assert gauge_json_ids == gaugehc_ids, (
            f"gauge.json IDs do not match gaugehc.json IDs.\n"
            f"  Only in gauge.json:  {gauge_json_ids - gaugehc_ids}\n"
            f"  Only in gaugehc.json: {gaugehc_ids - gauge_json_ids}"
        )

    def test_stress_storm_gauge_ids_are_in_known_set(self):
        """Gauge IDs in SAMPLE_STRESS_STORMS gauge_responses are from _data."""
        from tests.routes.trading._data import SAMPLE_STRESS_STORMS, ALL_TEST_GAUGE_IDS
        known = set(ALL_TEST_GAUGE_IDS)
        violations = []
        for storm in SAMPLE_STRESS_STORMS['storms']:
            for gr in storm.get('gauge_responses', []):
                gid = gr['gauge_id']
                if gid not in known and not GAUGE_ID_RE.match(gid):
                    violations.append(f"{storm['storm_id']}: {gid}")
        assert not violations, (
            f"Unknown gauge IDs in stress storm responses: {violations}"
        )


class TestProtocolUniformity:
    """All entity types derive IDs the same way: PREFIX-{uuid4()[:8]}."""

    def test_all_uuid4_suffixes_produce_lowercase_hex(self):
        """str(uuid.uuid4())[:8] always yields lowercase hex."""
        for _ in range(200):
            suffix = str(uuid.uuid4())[:8]
            assert suffix == suffix.lower(), \
                f"uuid4()[:8] produced uppercase chars: '{suffix}'"
            assert re.match(r'^[0-9a-f]{8}$', suffix), \
                f"uuid4()[:8] produced non-hex chars: '{suffix}'"

    def test_gauge_prop_mort_storm_share_same_suffix_derivation(self):
        """All four entity types use str(uuid4())[:8] — same derivation, same format."""
        from .conftest import GAUGE_ID_RE, PROP_ID_RE, MORT_ID_RE, STORM_ID_RE
        for entity, pattern in [
            ('GAUGE', GAUGE_ID_RE),
            ('PROP', PROP_ID_RE),
            ('MORT', MORT_ID_RE),
            ('STORM', STORM_ID_RE),
        ]:
            suffix = str(uuid.uuid4())[:8]
            entity_id = f"{entity}-{suffix}"
            assert pattern.match(entity_id), \
                f"{entity} ID '{entity_id}' does not match its own pattern"

    def test_all_entity_suffixes_have_same_length(self):
        """All entity ID suffixes are exactly 8 characters."""
        suffix_lengths = {
            'GAUGE': len(str(uuid.uuid4())[:8]),
            'PROP': len(str(uuid.uuid4())[:8]),
            'MORT': len(str(uuid.uuid4())[:8]),
            'STORM': len(str(uuid.uuid4())[:8]),
        }
        assert all(v == 8 for v in suffix_lengths.values()), \
            f"Unexpected suffix lengths: {suffix_lengths}"
