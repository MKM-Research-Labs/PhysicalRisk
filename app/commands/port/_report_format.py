# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see auth.py for full license text)

"""Tiny formatting helpers shared between summary.py and summary_sections.py."""

W = 72  # report width


def heading(title: str) -> None:
    print(f'\n  {title}')
    print(f'  {"-" * (W - 4)}')


def row(label: str, value: str, indent: int = 4) -> None:
    print(f'{" " * indent}{label:<32s} {value}')
