"""Shared initialisation logic for property-level generators."""

import logging
from pathlib import Path
from typing import Optional, Union

from config import config


class GeneratorInitMixin:
    """Mixin providing common __init__ and log() for property generators.

    Subclasses must call ``_init_generator(output_dir, mode, verbose)`` in
    their own ``__init__`` to set ``self.output_dir``, ``self.mode``,
    ``self.verbose`` and configure logging.
    """

    def _init_generator(
        self,
        output_dir: Optional[Union[str, Path]],
        mode: str,
        verbose: bool,
    ):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.verbose = verbose
        if not verbose:
            logging.getLogger(self.__class__.__module__).setLevel(logging.WARNING)

    def log(self, message: str):
        logging.getLogger(self.__class__.__module__).info(message)
