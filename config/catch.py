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

"""
Catchment management mixin for MKM Research Labs PRS Platform.

CatchmentMixin holds all catchment selection, loading, and enumeration
logic that was previously inline in PortfolioConfig.
"""

import os
from contextlib import contextmanager
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from catch.base_catchment import BaseCatchment


class CatchmentMixin:
    """Catchment selection and loading logic for PortfolioConfig."""

    def _init_catchment(self) -> None:
        """Initialise catchment state. Call once from PortfolioConfig.__init__."""
        self._catchment_id: str = os.environ.get('MKM_CATCHMENT', 'thames')
        self._catchment_instance: Optional['BaseCatchment'] = None

    # ------------------------------------------------------------------
    # catchment_id property
    # ------------------------------------------------------------------

    @property
    def catchment_id(self) -> str:
        """Get the current catchment identifier."""
        return self._catchment_id

    # NOTE: ``catchment_id`` is intentionally read-only. The active catchment is a
    # process-wide global that drives config paths + params; permanently mutating it
    # (the old ``config.catchment_id = value`` setter) made sequential/nested
    # multi-catchment runs race on a shared global and leak one run's catchment into
    # the next. Switch catchments through the scoped :meth:`use_catchment` context
    # manager instead — it restores the previous catchment on exit. Run-scoped *data*
    # identity is carried separately by ``database.catchment_context`` (a ContextVar).

    def _set_catchment(self, value: str) -> None:
        """Switch the active catchment and repoint paths. Internal — callers use the
        scoped :meth:`use_catchment` so every change is restored.

        Accepts either catch/<value>.py or catch/<value>/ as valid.
        """
        value = value.lower().strip()

        file_path = self.catchments_dir / f"{value}.py"
        dir_path = self.catchments_dir / value

        if not file_path.exists() and not dir_path.exists():
            available = self.list_catchments()
            raise ValueError(
                f"Catchment '{value}' not found. "
                f"Available catchments: {', '.join(available)}"
            )

        if value != self._catchment_id:
            self._catchment_instance = None
            self._catchment_id = value
            # Refresh path attributes so input_dir, results_dir, etc.
            # point at data/input/<new_catchment>/. Without this, every
            # downstream consumer keeps using the catchment that was
            # active at PortfolioConfig() instantiation time.
            if hasattr(self, '_init_paths'):
                self._init_paths(value)

    @contextmanager
    def use_catchment(self, value: str):
        """Activate ``value`` as the catchment for the duration of the block, then
        restore the previously active catchment (including on exception).

        The supported replacement for the old ``config.catchment_id = value``: switches
        are scoped, so a nested or sequential run cannot leak its catchment into the
        enclosing one. Validates ``value`` eagerly (raises ``ValueError`` if unknown).
        """
        previous = self._catchment_id
        self._set_catchment(value)
        try:
            yield value
        finally:
            self._set_catchment(previous)

    @property
    def CATCHMENT(self) -> str:
        """Alias for catchment_id (for server.py compatibility)."""
        return self._catchment_id

    @property
    def CURRENCY(self) -> str:
        """ISO 4217 currency code for the active catchment.

        Single source of truth read from the catchment params module
        (``catch.<catchment_id>.CURRENCY``), so loans, valuations, PRS
        notionals, counterparties and book summaries all stamp the same
        code without hardcoding it. Falls back to ``GBP`` if a catchment
        does not define one.
        """
        try:
            return getattr(self.load_params_module(), "CURRENCY", "GBP")
        except Exception:
            return "GBP"

    # ------------------------------------------------------------------
    # Module loaders
    # ------------------------------------------------------------------

    def load_random_module(self, module_name: str):
        """
        Load a catchment-specific random module.

        Example:
            module_name = 'gauge_random' -> port.rand.<catchment_id>.gauge_random
        """
        import importlib
        try:
            return importlib.import_module(f"port.rand.{self._catchment_id}.{module_name}")
        except ModuleNotFoundError as e:
            raise ImportError(
                f"Could not load random module '{module_name}' for catchment "
                f"'{self._catchment_id}': {e}"
            )

    def load_params_module(self):
        """
        Load the catchment-specific parameters module.

        Params live in 'catch/<catchment_id>.py', imported as 'catch.<catchment_id>'.
        """
        import importlib
        try:
            return importlib.import_module(f"catch.{self._catchment_id}")
        except ModuleNotFoundError as e:
            raise ImportError(
                f"Could not load params for catchment '{self._catchment_id}': {e}"
            )

    # ------------------------------------------------------------------
    # Catchment enumeration + instance
    # ------------------------------------------------------------------

    # Module/file names under data/catch/ that are infrastructure rather
    # than real catchments — base classes, helpers, etc. Excluded from
    # ``list_catchments()`` so they can't be selected as the active
    # catchment.
    _CATCHMENT_INFRASTRUCTURE_NAMES = frozenset({'base', 'base_catchment'})

    def list_catchments(self) -> list:
        """Return sorted list of available catchment names.

        Excludes underscore-prefixed names (private modules) and the
        known infrastructure files (``base.py``, ``base_catchment.py``).
        """
        # Union both homes: a catchment vendored into the repo and one still
        # under the data root must both be selectable, or migrating one would
        # make the others vanish from the list.
        names = set()
        search = (self.catchment_search_paths()
                  if hasattr(self, 'catchment_search_paths')
                  else [self.catchments_dir])
        for directory in search:
            if not directory.exists():
                continue
            names |= {
            p.stem for p in directory.iterdir()
            if (
                (p.is_file() and p.suffix == ".py" and not p.stem.startswith('_')
                 and p.stem not in self._CATCHMENT_INFRASTRUCTURE_NAMES) or
                (p.is_dir() and not p.name.startswith('_') and not p.name.startswith('.')
                 and p.name not in self._CATCHMENT_INFRASTRUCTURE_NAMES)
            )
            }
        return sorted(names)

    def get_catchment(self) -> 'BaseCatchment':
        """
        Get the current catchment instance.

        Returns:
            BaseCatchment implementation for the current catchment_id

        Raises:
            ImportError: If catchment module cannot be loaded
        """
        if self._catchment_instance is not None:
            return self._catchment_instance

        import importlib
        try:
            module = importlib.import_module(f"catch.{self._catchment_id}")
            if hasattr(module, 'catchment'):
                self._catchment_instance = module.catchment
            else:
                raise ImportError(
                    f"Catchment module 'catch.{self._catchment_id}' "
                    f"must expose a 'catchment' attribute"
                )
            return self._catchment_instance
        except ModuleNotFoundError as e:
            raise ImportError(
                f"Could not load catchment '{self._catchment_id}': {e}"
            )
