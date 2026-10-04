import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "rule_watch",
    Path(__file__).resolve().parents[1] / "scripts" / "rule_watch.py",
)
rule_watch = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(rule_watch)


def test_codex_usage_limit_retries_without_flag():
    key = "157:20298"
    state = {"failed_key": key}
    assert rule_watch.should_skip_failed(state, key, retry=False) is False


def test_pytest_failure_blocks_until_retry():
    key = "157:20298"
    state = {"failed_key": key, "failed_kind": "code"}
    assert rule_watch.should_skip_failed(state, key, retry=False) is True
    assert rule_watch.should_skip_failed(state, key, retry=True) is False
