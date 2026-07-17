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
Base loader class providing common functionality for all entity loaders.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

from database import read_json_document

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=Dict[str, Any])


class BaseLoader(ABC, Generic[T]):
    """
    Abstract base class for entity data loaders.

    Subclasses must define class attributes:
    - ENTITY_NAME: str - Name for logging
    - DEFAULT_FILENAME: str - Default data filename
    - CONTAINER_KEYS: List[str] - Possible JSON container keys

    Subclasses must implement:
    - get_entity_id(): Extract ID from an entity
    - get_entity_summary(): Create summary dict for listing
    """

    ENTITY_NAME: str = 'entity'
    DEFAULT_FILENAME: str = 'data.json'
    CONTAINER_KEYS: List[str] = []

    def __init__(self, data_dir: Path, filename: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            data_dir: Directory containing data files
            filename: Optional custom filename (defaults to DEFAULT_FILENAME)
        """
        self.data_dir = Path(data_dir)
        self.filename = filename or self.DEFAULT_FILENAME
        self._cache: Optional[List[T]] = None
        self._cache_valid = False

    def _get_file_path(self) -> Path:
        """Get the path to the data file."""
        return self.data_dir / self.filename

    @abstractmethod
    def get_entity_id(self, entity: T) -> Optional[str]:
        """Extract the unique ID from an entity."""
        pass

    @abstractmethod
    def get_entity_summary(self, entity: T) -> Dict[str, Any]:
        """Create a summary dictionary for listing."""
        pass

    def _load_json(self, filepath: Path) -> Optional[Dict]:
        """Load a JSON document via the database package (coding rule R6).

        Returns ``None`` when the file is absent; a corrupt file raises (kept for
        compatibility with the previous direct-``json.load`` behaviour)."""
        data = read_json_document(filepath.parent, filepath.name)
        if data is None:
            logger.warning(f"File not found: {filepath}")
        return data

    def _load_document(self) -> Optional[Dict]:
        """Return the raw entity document.

        The default reads the on-disk file at ``data_dir/filename``. Migrated
        subclasses override this to read the active catchment through the database
        seam instead, so the running app serves from whichever backend is bound
        (file or Postgres under ``MKM_REPO_BACKEND=pg``)."""
        return self._load_json(self._get_file_path())

    def _normalize_to_list(self, data: Any) -> List[T]:
        """Normalize various JSON structures to a list."""
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in self.CONTAINER_KEYS:
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []

    def load_all(self, force_reload: bool = False) -> List[T]:
        """Load and cache all entities (via ``_load_document`` — file or seam)."""
        if self._cache is None or not self._cache_valid or force_reload:
            data = self._load_document()
            self._cache = self._normalize_to_list(data)
            self._cache_valid = True
            logger.info(f"Loaded {len(self._cache)} {self.ENTITY_NAME}(s)")
        return self._cache or []

    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Find a specific entity by ID."""
        for entity in self.load_all():
            if self.get_entity_id(entity) == entity_id:
                return entity
        return None

    def list_all(self) -> List[Dict[str, Any]]:
        """Get summary list of all entities."""
        return [self.get_entity_summary(entity) for entity in self.load_all()]

    def count(self) -> int:
        """Get count of entities."""
        return len(self.load_all())

    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists."""
        return self.find_by_id(entity_id) is not None

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache = None
        self._cache_valid = False

    def invalidate_cache(self) -> None:
        """Invalidate the cache (alias for clear_cache)."""
        self.clear_cache()

    def get_status(self) -> Dict[str, Any]:
        """Get status information about the loader."""
        filepath = self._get_file_path()
        exists = filepath.exists()
        return {
            'entity_name': self.ENTITY_NAME,
            'path': str(filepath),
            'exists': exists,
            'size_bytes': filepath.stat().st_size if exists else 0,
            'cached': self._cache_valid,
            'cached_count': len(self._cache) if self._cache else 0
        }

    # Compatibility aliases
    def _extract_id(self, entity: T) -> Optional[str]:
        """Alias for get_entity_id (compatibility)."""
        return self.get_entity_id(entity)

    def _create_summary(self, entity: T) -> Dict[str, Any]:
        """Alias for get_entity_summary (compatibility)."""
        return self.get_entity_summary(entity)

    def _get_container_keys(self) -> List[str]:
        """Get container keys (compatibility)."""
        return self.CONTAINER_KEYS

    def get_file_status(self) -> Dict[str, Any]:
        """Alias for get_status (compatibility)."""
        return self.get_status()
