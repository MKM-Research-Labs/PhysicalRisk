# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Asset-type configuration for the property / commercial timeseries + hazard-curve
generators.

The flood propagation, IDW interpolation, depth-damage, and PRS pricing logic
is identical between residential and commercial assets. What differs is the
input JSON shape and the output filenames:

                        residential                commercial
  portfolio_filename    property.json              commercial.json
  portfolio_key         properties                 commercial_assets
  root_section_key      PropertyHeader             CommercialAsset
  attributes_key        PropertyAttributes         CommercialAttributes
  id_prefix             PROP-                      CPROP-
  ts_dirs.normal        propertyts                 commercialts
  ts_dirs.shd           propertytsd                commercialtsd
  ts_dirs.she           propertytse                commercialtse
  ts_dirs.bri           propertytsb                commercialtsb
  ts_dirs.win           propertytsw                commercialtsw
  ts_dirs.faw           propertytsfaw              commercialtsfaw
  ts_dirs.fow           propertytsfow              commercialtsfow
  ts_dirs.bow           propertytsbow              commercialtsbow
  ts_dirs.baw           propertytsbaw              commercialtsbaw
  hc_files.normal       propertyhc.json            commercialhc.json
  hc_files.shd          propertyshd.json           commercialshd.json
  hc_files.she          propertyshe.json           commercialshe.json
  hc_files.bri          propertybri.json           commercialbri.json
  hc_files.win          propertywin.json           commercialwin.json
  hc_files.faw          propertyfaw.json           commercialfaw.json
  hc_files.fow          propertyfow.json           commercialfow.json
  hc_files.bow          propertybow.json           commercialbow.json
  hc_files.baw          propertybaw.json           commercialbaw.json
  type_field            PropertyResi               CommercialType
  type_default          Detached                   Office

The TS + HC generator classes read an ``ASSET_CONFIG`` class attribute. The
residential generators set it to ``RESIDENTIAL_CONFIG``; the commercial
subclasses override only that attribute.

Wind-coupled peril scenarios. ``win``/``faw``/``fow`` combine the RAW asset
flood spine with wind (flood-only / flood AND wind / flood OR wind). ``bow``
(BRI OR wind) and ``baw`` (BRI AND wind) are the same union/intersection but
anchored on the BRI-resilient flood (the ``bri`` ts) — i.e. the flood level the
book actually trades at. The peril ts generator derives ``bow``/``baw`` from the
``bri`` ts rather than the ``normal`` ts; everything downstream is identical.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Union


@dataclass(frozen=True)
class AssetTypeConfig:
    """Per-asset-type knobs for the ts/hc generators."""

    # Input portfolio
    portfolio_filename: str       # e.g. "property.json" / "commercial.json"
    portfolio_key: str            # JSON key holding the records list

    # Record shape
    root_section_key: str         # "PropertyHeader" / "CommercialAsset"
    attributes_key: str           # "PropertyAttributes" / "CommercialAttributes"
    type_field: str               # field name inside attributes that holds the asset-type label
    type_default: str             # fallback label when the field is absent

    # Output naming
    id_prefix: str                # "PROP-" / "CPROP-" — used for output filenames + glob
    ts_dirs: Mapping[str, str]    # mode → ts output directory name
    hc_files: Mapping[str, str]   # mode → hc output JSON filename
    label: str                    # human-readable label for log lines

    @property
    def id_glob(self) -> str:
        """Glob pattern matching the per-asset JSON files in the ts output dirs."""
        return f"{self.id_prefix}*.json"

    def ts_dir(self, output_dir: Union[str, Path], mode: str) -> Path:
        return Path(output_dir) / self.ts_dirs[mode]

    def hc_file(self, output_dir: Union[str, Path], mode: str) -> Path:
        return Path(output_dir) / self.hc_files[mode]

    # ── database seam access (hazard curves) ─────────────────────────────────
    # The generators' local mode vocabulary uses ``"normal"`` for the default
    # flood scenario; the seam (config.data_layout.SCENARIO_MODES) calls it
    # ``"flood"``. The remaining modes (shd/she/bri/win/faw/fow/bow/baw) match.
    @property
    def _is_commercial(self) -> bool:
        return self.portfolio_key == "commercial_assets"

    @staticmethod
    def _seam_mode(mode: str) -> str:
        return "flood" if mode == "normal" else mode

    def get_hazard_curves(self, catchment: str, mode: str = "normal"):
        """Load this asset type's hazard curves for *mode* via the database seam.

        Returns the raw hazard-curve document (or ``None`` when absent), keyed on
        *catchment* and dispatched to the property or commercial artifact."""
        import database
        fn = (database.get_commercial_hazard_curves if self._is_commercial
              else database.get_property_hazard_curves)
        return fn(catchment, mode=self._seam_mode(mode))

    def save_hazard_curves(self, catchment: str, payload, mode: str = "normal") -> None:
        """Save this asset type's hazard curves for *mode* via the database seam."""
        import database
        fn = (database.save_commercial_hazard_curves if self._is_commercial
              else database.save_property_hazard_curves)
        fn(catchment, payload, mode=self._seam_mode(mode))

    def get_portfolio(self, catchment: str) -> list:
        """List this asset type's portfolio records (property / commercial) via
        the database seam."""
        import database
        fn = database.list_commercial if self._is_commercial else database.list_properties
        return fn(catchment)

    def save_portfolio_flood_summary(self, catchment: str, payload, mode: str = "normal") -> None:
        """Save this asset type's portfolio flood summary for *mode* via the seam."""
        import database
        fn = (database.save_commercial_portfolio_flood_summary if self._is_commercial
              else database.save_portfolio_flood_summary)
        fn(catchment, payload, mode=self._seam_mode(mode))

    # ── database seam access (per-asset timeseries) ──────────────────────────
    def iter_timeseries_ids(self, catchment: str, mode: str = "normal"):
        """Yield this asset type's per-asset timeseries ids for *mode* via the seam.

        Filtered to the asset id prefix (``PROP-`` / ``CPROP-``) so singleton docs
        that share the ts directory — e.g. ``portfolio_flood_summary`` — are
        excluded, matching the old ``glob(id_glob)`` semantics."""
        import database
        fn = (database.iter_commercial_timeseries_ids if self._is_commercial
              else database.iter_property_timeseries_ids)
        return [k for k in fn(catchment, mode=self._seam_mode(mode))
                if k.startswith(self.id_prefix)]

    def timeseries_exists(self, catchment: str, mode: str = "normal") -> bool:
        """True if this asset type's per-asset timeseries collection for *mode* has
        been generated (distinguishes 'stage not run' from an empty portfolio)."""
        import database
        fn = (database.commercial_timeseries_exists if self._is_commercial
              else database.property_timeseries_exists)
        return fn(catchment, mode=self._seam_mode(mode))

    def get_timeseries(self, catchment: str, asset_id: str, mode: str = "normal"):
        """Load one per-asset timeseries record for *mode* via the seam."""
        import database
        fn = (database.get_commercial_timeseries if self._is_commercial
              else database.get_property_timeseries)
        return fn(catchment, asset_id, mode=self._seam_mode(mode))

    def save_timeseries(self, catchment: str, asset_id: str, payload, mode: str = "normal") -> None:
        """Save one per-asset timeseries record for *mode* via the seam."""
        import database
        fn = (database.save_commercial_timeseries if self._is_commercial
              else database.save_property_timeseries)
        fn(catchment, asset_id, payload, mode=self._seam_mode(mode))

    def clear_timeseries(self, catchment: str, mode: str = "normal") -> None:
        """Remove this asset type's whole per-asset timeseries collection for *mode*
        (replaces a glob-and-unlink of the ts dir before a full rewrite)."""
        import database
        fn = (database.clear_commercial_timeseries if self._is_commercial
              else database.clear_property_timeseries)
        fn(catchment, mode=self._seam_mode(mode))


RESIDENTIAL_CONFIG = AssetTypeConfig(
    portfolio_filename="property.json",
    portfolio_key="properties",
    root_section_key="PropertyHeader",
    attributes_key="PropertyAttributes",
    type_field="PropertyResi",
    type_default="Detached",
    id_prefix="PROP-",
    ts_dirs={
        "normal": "propertyts",
        "shd": "propertytsd",
        "she": "propertytse",
        "bri": "propertytsb",
        "win": "propertytsw",
        "faw": "propertytsfaw",
        "fow": "propertytsfow",
        "bow": "propertytsbow",
        "baw": "propertytsbaw",
    },
    hc_files={
        "normal": "propertyhc.json",
        "shd": "propertyshd.json",
        "she": "propertyshe.json",
        "bri": "propertybri.json",
        "win": "propertywin.json",
        "faw": "propertyfaw.json",
        "fow": "propertyfow.json",
        "bow": "propertybow.json",
        "baw": "propertybaw.json",
    },
    label="Property",
)


COMMERCIAL_CONFIG = AssetTypeConfig(
    portfolio_filename="commercial.json",
    portfolio_key="commercial_assets",
    root_section_key="CommercialAsset",
    attributes_key="CommercialAttributes",
    type_field="CommercialType",
    type_default="Office",
    id_prefix="CPROP-",
    ts_dirs={
        "normal": "commercialts",
        "shd": "commercialtsd",
        "she": "commercialtse",
        "bri": "commercialtsb",
        "win": "commercialtsw",
        "faw": "commercialtsfaw",
        "fow": "commercialtsfow",
        "bow": "commercialtsbow",
        "baw": "commercialtsbaw",
    },
    hc_files={
        "normal": "commercialhc.json",
        "shd": "commercialshd.json",
        "she": "commercialshe.json",
        "bri": "commercialbri.json",
        "win": "commercialwin.json",
        "faw": "commercialfaw.json",
        "fow": "commercialfow.json",
        "bow": "commercialbow.json",
        "baw": "commercialbaw.json",
    },
    label="Commercial",
)


__all__ = ["AssetTypeConfig", "RESIDENTIAL_CONFIG", "COMMERCIAL_CONFIG"]
