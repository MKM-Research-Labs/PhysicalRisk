# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Commercial Portfolio Generator.

Generates synthetic commercial asset data based on the CommercialAssetCDM
schema. Heavy-lifting (locations, common-asset random generators) is
delegated to the residential property infrastructure; commercial-specific
fields are produced by the active catchment's commercial_random
(``port.rand.<catchment_id>.commercial.commercial_random``).

Usage
-----
    from port.src.commercial import generate_commercials
    result = generate_commercials(count=10)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import config
from port.cdm import CommercialAssetCDM
from port.src.property.main.encoder import DateTimeEncoder
from port.src.property.main.locations import LocationsMixin
from port.utils.schema import build_section

logger = logging.getLogger(__name__)


class CommercialPortfolioGenerator(LocationsMixin):
    """Generates commercial asset portfolio data for the active catchment."""

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True,
    ):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.commercial_cdm = CommercialAssetCDM()
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        # commercial_random handles all field generation (commercial-specific
        # menus + delegation to residential property_random for shared fields).
        # Dispatched via config so the active catchment's commercial random
        # module (port.rand.<catchment_id>.commercial.commercial_random) is
        # picked up, not a literal port.rand.thames.* path.
        self.random = random_module or config.load_random_module(
            'commercial.commercial_random')
        # Catchment params still come from the configured catchment.
        self.params = catchment_params or config.load_params_module()

        self.processing_stats = {
            'total_assets': 0,
            'successful_assets': 0,
            'failed_assets': 0,
            'start_time': None,
            'end_time': None,
        }

    def log(self, message: str, level: str = "INFO"):
        getattr(logger, level.lower(), logger.info)(message)

    def generate(self, count: int = 10) -> Dict:
        """Generate `count` commercial assets."""
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['total_assets'] = count

        self.log("=" * 60, "INFO")
        self.log("COMMERCIAL PORTFOLIO GENERATOR", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Catchment: {config.CATCHMENT}", "INFO")
        self.log(f"Target asset count: {count}", "INFO")
        self.log(f"Output directory: {self.output_dir}", "INFO")

        # Reuse the residential location generator (Thames addresses are
        # Thames addresses — commercial assets live on the same network).
        self._gauge_id_map = {}
        gauge_file = self.output_dir / 'gauge.json'
        if gauge_file.exists():
            try:
                with open(gauge_file) as f:
                    gauge_portfolio = json.load(f)
                for idx, g in enumerate(gauge_portfolio.get('flood_gauges',
                                                            gauge_portfolio.get('gauges', []))):
                    gid = g.get('FloodGauge', {}).get('Header', {}).get('GaugeID', '')
                    if gid:
                        self._gauge_id_map[idx] = gid
            except Exception as e:
                self.log(f"Could not load gauge IDs: {e}", "DEBUG")

        self.log("Generating commercial asset locations...", "INFO")
        locations = self._generate_locations(count)
        self.log(f"Generated {len(locations)} locations", "INFO")

        schema = self.commercial_cdm.schema
        self.log("Schema loaded from CommercialAssetCDM", "DEBUG")

        records = []
        record_ids = []

        for i, location in enumerate(locations):
            try:
                metadata = self.random.generate_commercial_metadata(i, location)
                ctype = metadata['commercial_type']
                pid = metadata['property_id']

                # Walk the schema and produce values via the commercial
                # random module (it knows when to delegate to residential).
                asset_data = build_section(schema, i, metadata, self.random)

                # Stamp identifiers + cross-section consistency.
                self._set_specific_values(asset_data, metadata, location)

                records.append(asset_data)
                record_ids.append(pid)
                self.processing_stats['successful_assets'] += 1

                self.log(f"  [{i+1}/{count}] {pid} ({ctype}) at {location.get('name','?')}", "INFO")

            except Exception as e:
                self.log(f"Failed to generate commercial asset {i+1}: {e}", "ERROR")
                self.processing_stats['failed_assets'] += 1
                continue

        output_path = self.output_dir / "commercial.json"
        output_data = {
            "commercial_assets": records,
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "Commercial v0.1 (first slice)",
                "catchment": config.CATCHMENT,
                "total_assets_generated": len(records),
                "type_mix": self._type_mix_summary(records),
            }
        }
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, cls=DateTimeEncoder)
        self.log(f"Commercial data saved to: {output_path}", "INFO")

        self.processing_stats['end_time'] = datetime.now()
        elapsed = (self.processing_stats['end_time'] -
                   self.processing_stats['start_time']).total_seconds()
        self.log("=" * 60, "INFO")
        self.log(f"Generated {self.processing_stats['successful_assets']}/"
                 f"{count} commercial assets in {elapsed:.1f}s", "INFO")

        return {
            "data": {"commercial_assets": records, "asset_ids": record_ids,
                     "locations": locations},
            "file_path": output_path,
            "processing_stats": self.processing_stats,
        }

    # ------------------------------------------------------------------

    def _set_specific_values(self, asset_data: Dict, metadata: Dict, location: Dict):
        """Stamp identifiers + lat/lon + a few cross-section consistencies."""
        ca = asset_data.setdefault('CommercialAsset', {})

        header = ca.setdefault('Header', {})
        header['PropertyID'] = metadata['property_id']
        header['CatchmentID'] = config.CATCHMENT
        header['UPRN'] = header.get('UPRN') or f"UPRN-{metadata['property_id']}"
        header['propertyType'] = 'commercial'
        header['propertyStatus'] = header.get('propertyStatus', 'active')

        loc = ca.setdefault('Location', {})
        # LocationsMixin uses 'lat'/'lon' (legacy) keys; map them to the CDM
        # schema's full names.
        loc['LatitudeDegrees'] = location.get('lat', loc.get('LatitudeDegrees'))
        loc['LongitudeDegrees'] = location.get('lon', loc.get('LongitudeDegrees'))
        if location.get('postcode'):
            loc['Postcode'] = location['postcode']
        if location.get('name'):
            loc['TownCity'] = location['name']

        attrs = ca.setdefault('CommercialAttributes', {})
        attrs['CommercialType'] = metadata['commercial_type']
        attrs['PropertyAreaSqm'] = metadata['property_area']
        attrs['ConstructionYear'] = metadata['construction_year']

        valuation = ca.setdefault('Valuation', {})
        valuation['PropertyValue'] = metadata['property_value']
        valuation['ValuationDate'] = datetime.now().date().isoformat()

        # RiskAssessment.GroundLevelMeters — derive from elevation
        risk = ca.setdefault('RiskAssessment', {})
        if 'GroundLevelMeters' not in risk:
            risk['GroundLevelMeters'] = location.get('elevation')

    def _type_mix_summary(self, records: List[Dict]) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in records:
            t = r.get('CommercialAsset', {}).get('CommercialAttributes', {}).get('CommercialType', 'Unknown')
            out[t] = out.get(t, 0) + 1
        return out


def generate_commercials(
    count: int = 10,
    output_dir: Optional[Path] = None,
) -> Dict:
    """Convenience wrapper for the CLI. Catchment is taken from
    ``config.catchment_id`` (pinned by the CLI entry point)."""
    return CommercialPortfolioGenerator(output_dir=output_dir).generate(count=count)
