import importlib.util
from pathlib import Path
from subprocess import CompletedProcess

import pytest

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


@pytest.mark.parametrize("returncode,output", [(128, ""), (0, "false\n")])
def test_cloud_without_worktree_stops_before_agent(monkeypatch, tmp_path, returncode, output):
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        return CompletedProcess(cmd, returncode, stdout=output, stderr="")

    monkeypatch.setattr(rule_watch.subprocess, "run", run)
    monkeypatch.setattr(rule_watch, "SAMPLE_DIR", tmp_path / "samples")
    with pytest.raises(RuntimeError, match="Git-Repository"):
        rule_watch.run_codex_cloud("fixture prompt", "fixture-env", 1)
    assert calls == [["git", "rev-parse", "--is-inside-work-tree"]]
    assert not (tmp_path / "samples").exists()


def test_cloud_missing_task_id_never_selects_latest_task(monkeypatch, tmp_path):
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        output = "true\n" if cmd[0] == "git" else "Task submitted without ID"
        return CompletedProcess(cmd, 0, stdout=output, stderr="")

    monkeypatch.setattr(rule_watch.subprocess, "run", run)
    monkeypatch.setattr(rule_watch, "SAMPLE_DIR", tmp_path / "samples")
    with pytest.raises(RuntimeError, match="kein fremder Auftrag"):
        rule_watch.run_codex_cloud("fixture prompt", "fixture-env", 1)
    assert calls == [
        ["git", "rev-parse", "--is-inside-work-tree"],
        ["codex", "cloud", "exec", "--env", "fixture-env", "fixture prompt"],
    ]


def test_cloud_applies_only_submitted_task(monkeypatch, tmp_path):
    task_id = "12345678-1234-1234-1234-123456789abc"
    calls = []

    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0] == "git":
            output = "true\n"
        elif cmd[2] == "exec":
            output = task_id
        elif cmd[2] == "status":
            output = "completed"
        else:
            output = ""
        return CompletedProcess(cmd, 0, stdout=output, stderr="")

    monkeypatch.setattr(rule_watch.subprocess, "run", run)
    monkeypatch.setattr(rule_watch, "SAMPLE_DIR", tmp_path / "samples")
    rule_watch.run_codex_cloud("fixture prompt", "fixture-env", 10)
    assert calls[-2:] == [
        ["codex", "cloud", "status", task_id],
        ["codex", "cloud", "apply", task_id],
    ]
