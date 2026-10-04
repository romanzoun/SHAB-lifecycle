import importlib
import sys
from pathlib import Path

import pytest


def _reload_config():
    sys.modules.pop("shab_harvester.config", None)
    return importlib.import_module("shab_harvester.config")


@pytest.fixture
def hide_real_dotenv():
    """config.py's dotenv loader always targets the real project root, not
    cwd — reloading the module in a test would otherwise pick up whatever
    .env the developer actually has checked out locally. Hide it for the
    duration of the test."""
    real_env = Path(__file__).resolve().parent.parent / ".env"
    backup = real_env.parent / ".env.test_backup"
    moved = False
    if real_env.exists():
        real_env.rename(backup)
        moved = True
    try:
        yield
    finally:
        if moved:
            backup.rename(real_env)


def test_defaults_match_original_hardcoded_values(monkeypatch, tmp_path, hide_real_dotenv):
    for name in [
        "SHAB_SCRAPE_PAUSE_MIN", "SHAB_SCRAPE_PAUSE_MAX", "SHAB_RATE_LIMIT_BACKOFF_MIN",
        "SHAB_RATE_LIMIT_BACKOFF_MAX", "SHAB_MAX_CONSECUTIVE_RATE_LIMITS", "SHAB_MAX_QUEUE_ATTEMPTS",
        "SHAB_PAGE_TIMEOUT_MS", "SHAB_FILTERED_RESPONSE_TIMEOUT_MS", "SHAB_SCROLL_MAX_ROUNDS",
        "SHAB_SCROLL_WAIT_MS", "SHAB_SCROLL_STABLE_ROUNDS", "SHAB_TRIGGER_SCROLL_ATTEMPTS",
        "SHAB_TRIGGER_SCROLL_WAIT_MS", "SHAB_HEADLESS_DEFAULT", "SHAB_WEBUI_HOST", "SHAB_WEBUI_PORT",
        "SHAB_DB_PATH",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)  # no .env file here

    config = _reload_config()

    assert config.SCRAPE_PAUSE_MIN == 1.0
    assert config.SCRAPE_PAUSE_MAX == 3.0
    assert config.RATE_LIMIT_BACKOFF_MIN == 60.0
    assert config.RATE_LIMIT_BACKOFF_MAX == 300.0
    assert config.MAX_CONSECUTIVE_RATE_LIMITS == 2
    assert config.MAX_QUEUE_ATTEMPTS == 3
    assert config.PAGE_TIMEOUT_MS == 30000
    assert config.FILTERED_RESPONSE_TIMEOUT_MS == 20000
    assert config.SCROLL_MAX_ROUNDS == 200
    assert config.SCROLL_WAIT_MS == 800
    assert config.SCROLL_STABLE_ROUNDS == 5
    assert config.TRIGGER_SCROLL_ATTEMPTS == 10
    assert config.TRIGGER_SCROLL_WAIT_MS == 500
    assert config.HEADLESS_DEFAULT is False
    assert config.WEBUI_HOST == "127.0.0.1"
    assert config.WEBUI_PORT == 8765


def test_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("SHAB_SCRAPE_PAUSE_MIN", "0.2")
    monkeypatch.setenv("SHAB_MAX_CONSECUTIVE_RATE_LIMITS", "5")
    monkeypatch.setenv("SHAB_HEADLESS_DEFAULT", "true")
    monkeypatch.setenv("SHAB_WEBUI_PORT", "9999")

    config = _reload_config()

    assert config.SCRAPE_PAUSE_MIN == 0.2
    assert config.MAX_CONSECUTIVE_RATE_LIMITS == 5
    assert config.HEADLESS_DEFAULT is True
    assert config.WEBUI_PORT == 9999


def test_dotenv_file_is_loaded_but_real_env_var_wins(monkeypatch, tmp_path, hide_real_dotenv):
    monkeypatch.delenv("SHAB_SCRAPE_PAUSE_MIN", raising=False)
    monkeypatch.delenv("SHAB_SCRAPE_PAUSE_MAX", raising=False)
    (tmp_path / ".env").write_text("SHAB_SCRAPE_PAUSE_MIN=0.5\nSHAB_SCRAPE_PAUSE_MAX=0.9\n")
    monkeypatch.chdir(tmp_path)

    # Point config's dotenv loader at this tmp_path's .env by reloading with
    # PROJECT_ROOT patched after import; simplest is to load it directly.
    config = _reload_config()
    config._load_dotenv(tmp_path / ".env")
    assert config._env_float("SHAB_SCRAPE_PAUSE_MIN", 1.0) == 0.5

    # A real env var must still win over the .env file value.
    monkeypatch.setenv("SHAB_SCRAPE_PAUSE_MAX", "2.5")
    config2 = _reload_config()
    config2._load_dotenv(tmp_path / ".env")
    assert config2._env_float("SHAB_SCRAPE_PAUSE_MAX", 1.0) == 2.5


def test_bool_parsing_accepts_common_truthy_values():
    config = _reload_config()
    import os

    for value in ("1", "true", "True", "yes", "on"):
        os.environ["SHAB_TEST_BOOL"] = value
        assert config._env_bool("SHAB_TEST_BOOL", False) is True
    for value in ("0", "false", "no", "off", ""):
        os.environ["SHAB_TEST_BOOL"] = value
        assert config._env_bool("SHAB_TEST_BOOL", True) is False
    del os.environ["SHAB_TEST_BOOL"]
