"""Refresh script for ignore_manager.

Run via: python adhd_framework.py refresh --module ignore-manager
"""

from __future__ import annotations

from logger_util import Logger


def main() -> None:
    """Refresh ignore_manager — no dynamic setup required beyond config template."""
    logger = Logger(name="ignore_managerRefresh")
    logger.info("ignore_manager refresh complete (config template registered by framework)")
