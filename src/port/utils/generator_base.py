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
