"""Structured logging setup, applied once at app startup.

Replaces the scattered `print()` calls that used to be the only signal for
scraper/LLM/description-fetch failures — those are invisible in production
(no timestamps, no log levels, easy to lose in stdout). `get_logger(name)`
gives every module a logger namespaced under `app.*`, so `logging.getLogger`
filtering/config (e.g. quieting `app.services.description`) works normally.
"""

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root `app` logger with a single stream handler.

    Input: level (int): minimum level to emit, default INFO.

    Calls: `logging.getLogger()`, `logging.StreamHandler()`.
    Called by: `app.main` at import time (module-level, so it runs once
        whether under uvicorn or pytest).

    Logic: guards on `logger.handlers` so re-importing this module (e.g.
        pytest re-importing `app.main` per test session) never attaches a
        second handler and duplicates every log line.
    """
    logger = logging.getLogger("app")
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced under `app.*` for the given module.

    Input: name (str): typically `__name__` of the calling module.
    Output: logging.Logger.
    Calls: `logging.getLogger()`.
    Called by: any `app.*` module that used to call `print()`.
    """
    return logging.getLogger(f"app.{name}")
