# Copyright (c) 2026 MinchinWeb
"""Invoke tasks; run with ``uv run invoke --list``."""

from __future__ import annotations

from minchin.tasks import (  # noqa: F401
    check,
    format_code,
    lint,
    test,
    update,
    upgrade,
)
