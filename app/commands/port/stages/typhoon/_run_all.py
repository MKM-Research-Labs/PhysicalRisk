# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Ordered driver for the typhoon stage."""

from ...context import StageContext
from ._run import run_typhoon


def run_all(ctx: StageContext):
    run_typhoon(ctx)
