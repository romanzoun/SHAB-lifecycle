"""All externally tunable runtime parameters, in one place.

Every value here can be overridden by an environment variable (see
.env.example for the full list and explanations) or by a `.env` file in the
project root. Real environment variables always win over `.env` file values.
Defaults match the project's original hardcoded values, so an unconfigured
install behaves exactly as before.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(PROJECT_ROOT / ".env")


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- Politeness: pause between detail-page scrapes (seconds) --------------
SCRAPE_PAUSE_MIN = _env_float("SHAB_SCRAPE_PAUSE_MIN", 1.0)
SCRAPE_PAUSE_MAX = _env_float("SHAB_SCRAPE_PAUSE_MAX", 3.0)

# --- Rate-limit handling ----------------------------------------------------
RATE_LIMIT_BACKOFF_MIN = _env_float("SHAB_RATE_LIMIT_BACKOFF_MIN", 60.0)
RATE_LIMIT_BACKOFF_MAX = _env_float("SHAB_RATE_LIMIT_BACKOFF_MAX", 300.0)
MAX_CONSECUTIVE_RATE_LIMITS = _env_int("SHAB_MAX_CONSECUTIVE_RATE_LIMITS", 2)

# --- Retry limit for failed publication_queue items -------------------------
MAX_QUEUE_ATTEMPTS = _env_int("SHAB_MAX_QUEUE_ATTEMPTS", 3)

# --- Playwright timeouts (milliseconds) -------------------------------------
PAGE_TIMEOUT_MS = _env_int("SHAB_PAGE_TIMEOUT_MS", 30000)
FILTERED_RESPONSE_TIMEOUT_MS = _env_int("SHAB_FILTERED_RESPONSE_TIMEOUT_MS", 20000)

# --- Infinite-scroll loading of the discovery results list ------------------
SCROLL_MAX_ROUNDS = _env_int("SHAB_SCROLL_MAX_ROUNDS", 200)
SCROLL_WAIT_MS = _env_int("SHAB_SCROLL_WAIT_MS", 800)
SCROLL_STABLE_ROUNDS = _env_int("SHAB_SCROLL_STABLE_ROUNDS", 5)

# --- Scroll nudges to provoke the date-filtered API response (discovery.py) -
TRIGGER_SCROLL_ATTEMPTS = _env_int("SHAB_TRIGGER_SCROLL_ATTEMPTS", 10)
TRIGGER_SCROLL_WAIT_MS = _env_int("SHAB_TRIGGER_SCROLL_WAIT_MS", 500)

# --- Publication search API (discovery paging) ------------------------------
# Unsorted pages repeat rows and skip others. PUBLICATION_NUMBER is stable.
DISCOVERY_PAGE_SIZE = _env_int("SHAB_DISCOVERY_PAGE_SIZE", 100)
DISCOVERY_PAGE_PAUSE_S = _env_float("SHAB_DISCOVERY_PAGE_PAUSE_S", 0.05)
DISCOVERY_PAGE_RETRIES = _env_int("SHAB_DISCOVERY_PAGE_RETRIES", 3)
DISCOVERY_HTTP_TIMEOUT_S = _env_float("SHAB_DISCOVERY_HTTP_TIMEOUT_S", 30.0)
# A filtered day is a few thousand hits. Larger totals are the unfiltered
# all-time count and must not be paged.
DISCOVERY_MAX_DAY_TOTAL = _env_int("SHAB_DISCOVERY_MAX_DAY_TOTAL", 5000)

# --- Browser / server defaults ----------------------------------------------
HEADLESS_DEFAULT = _env_bool("SHAB_HEADLESS_DEFAULT", False)
WEBUI_HOST = _env_str("SHAB_WEBUI_HOST", "127.0.0.1")
WEBUI_PORT = _env_int("SHAB_WEBUI_PORT", 8765)

# --- Paths -------------------------------------------------------------------
DB_PATH = Path(_env_str("SHAB_DB_PATH", str(PROJECT_ROOT / "data" / "shab_harvester.sqlite")))
