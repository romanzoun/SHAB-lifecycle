#!/usr/bin/env python3
"""Watchdog: poll the Hetzner walk, then run Codex or Claude CLI for the next parser.

Start:

  python3 scripts/rule_watch.py
  python3 scripts/rule_watch.py --engine claude
  bash scripts/start-rule-watch.sh --engine claude
  python3 scripts/rule_watch.py --engine cloud --cloud-env ENV_ID

`--engine local` = `codex exec`. `--engine claude` = `claude -p`.
Usage-Limit/Capacity: Pause, dann erneut, kein --retry.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ANALYZER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANALYZER_ROOT))
from shab_analyzer.config import DEFERRED_RUBRIC_ORDER  # noqa: E402
STATE_PATH = ANALYZER_ROOT / "data" / "rule_watch_state.json"
SAMPLE_DIR = ANALYZER_ROOT / "data" / "rule_watch_samples"
SSH_KEY = Path(os.environ.get("SHAB_SSH_KEY", Path.home() / ".ssh/hetzner_prod"))
SERVER = os.environ.get("SHAB_SERVER", "root@46.225.119.148")
REMOTE_DB = "/mnt/HC_Volume_106976683/analyzer/shab_analyzer.sqlite"
REMOTE_XML = "/opt/shab-raw/raw_xml"
DEFAULT_INTERVAL = 120
IDLE_LOG_EVERY = 900
CODEX_RETRY_SEC = 900
_last_idle_log = 0.0
SAMPLE_LIMIT = 12000
SAMPLE_FILES = 16


class CodexUnavailable(RuntimeError):
    """codex exec / cloud is at capacity or usage limit — retry next tick."""

_REMOTE_STATUS = r"""
import sqlite3
conn = sqlite3.connect("file:%s?mode=ro", uri=True, timeout=8)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM walk_job WHERE id=1").fetchone()
print("JOB", row["state"], row["parser_version"], row["heartbeat_at"] or "")
keys = row.keys()
print("UNLOCKED", row["unlocked_rubrics"] if "unlocked_rubrics" in keys and row["unlocked_rubrics"] else "HR")
for st in ("pending", "ok", "partial", "deferred", "error"):
    n = conn.execute("SELECT COUNT(*) FROM walk_item WHERE status=?", (st,)).fetchone()[0]
    print("COUNT", st, n)
""" % REMOTE_DB

_REMOTE_DEFERRED_FAMS = r"""
import sqlite3
conn = sqlite3.connect("file:%s?mode=ro", uri=True, timeout=60)
print("FAMS")
q = (
    "SELECT substr(pr.sub_rubric, 1, 2) fam, COUNT(*) n "
    "FROM walk_item wi "
    "JOIN parse_run pr ON pr.publication_id = wi.publication_id "
    "WHERE wi.status = 'deferred' "
    "GROUP BY 1"
)
for fam, n in conn.execute(q):
    print(fam, n)
""" % REMOTE_DB

_REMOTE_CLUSTERS = r"""
import collections, json, sqlite3
conn = sqlite3.connect("file:%s?mode=ro", uri=True, timeout=30)
conn.row_factory = sqlite3.Row
rows = conn.execute('''
  SELECT pr.language, pr.leftover_text, pr.publication_id, pr.source_relpath
  FROM walk_item wi
  JOIN parse_run pr ON pr.publication_id = wi.publication_id
  WHERE wi.status = ?
  LIMIT %d
''', ('partial',)).fetchall()
clusters = collections.Counter()
examples = {}
for r in rows:
    left = " ".join((r["leftover_text"] or "").split())
    key = (r["language"] or "?", left[:140])
    clusters[key] += 1
    if key not in examples:
        examples[key] = (r["publication_id"], r["source_relpath"], left[:400])
picked = []
for key, n in clusters.most_common(30):
    lang, prefix = key
    pid, rel, full = examples[key]
    picked.append({"n": n, "lang": lang, "pid": pid, "rel": rel, "leftover": full})
open("/tmp/shab-watch-clusters.json", "w").write(json.dumps(picked, ensure_ascii=False, indent=2))
rels = [p["rel"] for p in picked if p.get("rel")][:%d]
print(json.dumps({"sample_rows": len(rows), "clusters": len(picked), "rels": rels}))
""" % (REMOTE_DB, SAMPLE_LIMIT, SAMPLE_FILES)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _later(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"[{_now()}] {msg}", flush=True)


def _log_idle(msg: str) -> None:
    global _last_idle_log
    now = time.monotonic()
    if _last_idle_log and now - _last_idle_log < IDLE_LOG_EVERY:
        return
    _last_idle_log = now
    _log(msg)


def _ssh(remote_cmd: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "ssh",
            "-i",
            str(SSH_KEY),
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ServerAliveInterval=15",
            SERVER,
            remote_cmd,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _ssh_python(script: str, timeout: int = 90) -> str:
    proc = subprocess.run(
        [
            "ssh",
            "-i",
            str(SSH_KEY),
            "-o",
            "ConnectTimeout=10",
            SERVER,
            "python3",
            "-",
        ],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"ssh python exit {proc.returncode}")
    return proc.stdout


def require_codex_login(*, context: str) -> str:
    proc = subprocess.run(
        ["codex", "login", "status"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    text = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        raise SystemExit(
            f"Codex ist nicht eingeloggt ({context}).\n"
            f"{text}\n"
            "Lokal:  codex login\n"
            "Danach dieses Skript im Terminal neu starten."
        )
    if not text:
        text = "Logged in"
    return text


def require_claude_login(*, context: str) -> str:
    proc = subprocess.run(
        ["claude", "auth", "status"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    text = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        raise SystemExit(
            f"Claude CLI ist nicht eingeloggt ({context}).\n"
            f"{text}\n"
            "Lokal:  claude auth login\n"
            "Danach dieses Skript im Terminal neu starten."
        )
    if not text:
        text = "Logged in"
    return text


def require_engine_login(engine: str, *, context: str) -> str:
    if engine == "claude":
        return require_claude_login(context=context)
    return require_codex_login(context=context)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def local_parser_version() -> int:
    text = (ANALYZER_ROOT / "shab_analyzer" / "config.py").read_text()
    match = re.search(r"^PARSER_VERSION\s*=\s*(\d+)", text, re.M)
    if not match:
        raise RuntimeError("PARSER_VERSION nicht in config.py gefunden")
    return int(match.group(1))


def fetch_coverage() -> dict:
    out = _ssh_python(_REMOTE_STATUS, timeout=90)
    coverage = {"counts": {}, "unlocked": "HR"}
    for line in out.splitlines():
        parts = line.split()
        if parts[:1] == ["JOB"] and len(parts) >= 4:
            coverage["state"] = parts[1]
            coverage["parser_version"] = int(parts[2])
            coverage["heartbeat_at"] = parts[3]
        elif parts[:1] == ["UNLOCKED"] and len(parts) >= 2:
            coverage["unlocked"] = parts[1]
        elif parts[:1] == ["COUNT"] and len(parts) >= 3:
            coverage["counts"][parts[1]] = int(parts[2])
    if "state" not in coverage:
        raise RuntimeError(f"unerwarteter Status:\n{out}")
    return coverage


def fetch_deferred_families() -> dict[str, int]:
    out = _ssh_python(_REMOTE_DEFERRED_FAMS, timeout=180)
    fams: dict[str, int] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] != "FAMS":
            fams[parts[0]] = int(parts[1])
    return fams


def remote_unlock_family(family: str) -> int:
    script = f"""
import sqlite3
from datetime import datetime, timezone
family = {family!r}
db = {REMOTE_DB!r}
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
conn = sqlite3.connect(db, timeout=120)
cols = {{row[1] for row in conn.execute("PRAGMA table_info(walk_job)")}}
if "unlocked_rubrics" not in cols:
    conn.execute("ALTER TABLE walk_job ADD COLUMN unlocked_rubrics text")
    conn.execute("UPDATE walk_job SET unlocked_rubrics = 'HR' WHERE id = 1")
raw = conn.execute("SELECT unlocked_rubrics FROM walk_job WHERE id=1").fetchone()[0] or "HR"
prefixes = [p.strip() for p in raw.split(",") if p.strip()]
if family not in prefixes:
    prefixes.append(family)
    conn.execute("UPDATE walk_job SET unlocked_rubrics = ? WHERE id=1", (",".join(prefixes),))
sql = (
    "UPDATE walk_item SET status = 'pending', error_text = NULL, updated_at = ? "
    "WHERE status = 'deferred' AND publication_id IN ("
    "SELECT publication_id FROM parse_run WHERE sub_rubric LIKE ?)"
)
cur = conn.execute(sql, (now, family + "%"))
conn.commit()
print(cur.rowcount)
"""
    out = _ssh_python(script, timeout=180)
    return int(out.strip().splitlines()[-1])


def export_samples() -> dict:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.loads(_ssh_python(_REMOTE_CLUSTERS, timeout=120))
    rels = [r for r in payload.get("rels") or [] if r.endswith(".xml")]
    if not rels:
        raise RuntimeError("keine Sample-XML-Pfade in den Clustern")
    quoted = " ".join(f"'{REMOTE_XML}/{rel}'" for rel in rels)
    prep = _ssh(
        f"mkdir -p /tmp/shab-watch && rm -f /tmp/shab-watch/*.xml && cp {quoted} /tmp/shab-watch/",
        timeout=60,
    )
    if prep.returncode != 0:
        raise RuntimeError(prep.stderr or prep.stdout or "scp-prep failed")
    dest = SAMPLE_DIR / "xml"
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.xml"):
        old.unlink()
    scp = subprocess.run(
        [
            "scp",
            "-i",
            str(SSH_KEY),
            "-o",
            "ConnectTimeout=10",
            f"{SERVER}:/tmp/shab-watch/*.xml",
            str(dest),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if scp.returncode != 0:
        raise RuntimeError(scp.stderr or scp.stdout or "scp failed")
    clusters_text = _ssh("cat /tmp/shab-watch-clusters.json", timeout=30).stdout
    clusters_path = SAMPLE_DIR / "clusters.json"
    clusters_path.write_text(clusters_text)
    fixtures = ANALYZER_ROOT / "tests" / "fixtures"
    copied = []
    for xml in sorted(dest.glob("*.xml")):
        target = fixtures / xml.name
        target.write_bytes(xml.read_bytes())
        copied.append(xml.stem)
    payload["copied"] = copied
    payload["clusters_path"] = str(clusters_path)
    return payload


def build_prompt(coverage: dict, samples: dict, next_version: int) -> str:
    clusters = (SAMPLE_DIR / "clusters.json").read_text()[:8000]
    copied = ", ".join(samples.get("copied") or [])
    return f"""Du arbeitest lokal im Repo SHAB-ANALYZER (cwd ist dieses Paket).

Aufgabe: Parser {next_version} bauen, weil der Server-Walk complete ist und noch PARTIAL offen sind.

Freigeschaltete Rubriken: {coverage.get('unlocked') or 'HR'}
(Nicht-HR erst nach HR-PARTIAL=0, eine Familie nach der anderen.)

Server jetzt:
- state={coverage['state']}
- parser_version={coverage['parser_version']}
- pending={coverage['counts'].get('pending')}
- ok={coverage['counts'].get('ok')}
- partial={coverage['counts'].get('partial')}
- deferred={coverage['counts'].get('deferred')}
- error={coverage['counts'].get('error')}

Leftover-Cluster (Stichprobe, oft 2018-lastig wegen Index-Reihenfolge) stehen in:
  data/rule_watch_samples/clusters.json

Die Sample-XMLs sind nach tests/fixtures/ kopiert: {copied}

Regeln:
1. PARSER_VERSION in shab_analyzer/config.py auf {next_version} setzen.
2. Nur SHAB-ANALYZER anfassen. Harvester analysis.py nicht. Kein Postgres. Nicht committen. Nicht pushen.
3. Runtime bleibt deterministisch (Regex/XML). Kein LLM im Parser.
4. Für die kopierten Fixtures tests in tests/test_parse_fixtures.py ergänzen; pytest muss grün sein.
5. Leftover leer ohne Events ist PARTIAL — ein Event emitten oder den Resttext wirklich parsen, nicht FULLY erzwingen.
6. Bestehende Tests nicht kaputt machen.

Cluster-Kopf:
{clusters}
"""


def run_codex_local(prompt: str, timeout: int) -> None:
    prompt_path = SAMPLE_DIR / "prompt.md"
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt)
    _log("starte Codex lokal (codex exec)")
    proc = subprocess.run(
        [
            "codex",
            "exec",
            "-C",
            str(ANALYZER_ROOT),
            "--approve-for-me",
            "-o",
            str(SAMPLE_DIR / "codex_last_message.txt"),
            prompt,
        ],
        cwd=str(ANALYZER_ROOT),
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise CodexUnavailable(f"codex exec exit {proc.returncode}")


def run_claude_local(prompt: str, timeout: int) -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    (SAMPLE_DIR / "prompt.md").write_text(prompt)
    _log("starte Claude CLI (claude -p --permission-mode bypassPermissions)")
    proc = subprocess.run(
        [
            "claude",
            "-p",
            "--permission-mode",
            "bypassPermissions",
            "--output-format",
            "text",
            prompt,
        ],
        cwd=str(ANALYZER_ROOT),
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise CodexUnavailable(f"claude -p exit {proc.returncode}")


def _parse_task_id(text: str) -> str | None:
    match = re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", text, re.I)
    return match.group(0) if match else None


def run_codex_cloud(prompt: str, env_id: str, timeout: int) -> None:
    repo = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(ANALYZER_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if repo.returncode != 0 or repo.stdout.strip() != "true":
        raise RuntimeError(
            "Cloud-Modus braucht ein lokales Git-Repository für codex cloud apply. "
            "Kein Cloud-Auftrag gestartet; lokalen Engine-Modus verwenden."
        )
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    _log(f"starte Codex Cloud (codex cloud exec --env {env_id})")
    proc = subprocess.run(
        ["codex", "cloud", "exec", "--env", env_id, prompt],
        cwd=str(ANALYZER_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
    (SAMPLE_DIR / "cloud_exec.txt").write_text(blob)
    if proc.returncode != 0:
        raise CodexUnavailable(f"codex cloud exec exit {proc.returncode}: {blob[-2000:]}")
    task_id = _parse_task_id(blob)
    if not task_id:
        raise RuntimeError("keine Cloud-Task-ID in exec Output — kein fremder Auftrag wird übernommen")
    _log(f"Cloud-Task {task_id}, warte auf complete")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        st = subprocess.run(
            ["codex", "cloud", "status", task_id],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        text = (st.stdout or "") + "\n" + (st.stderr or "")
        low = text.lower()
        if any(word in low for word in ("fail", "error", "cancelled", "canceled")):
            raise RuntimeError(f"Cloud-Task fehlgeschlagen:\n{text[-2000:]}")
        if any(word in low for word in ("complete", "completed", "succeeded", "success")):
            apply = subprocess.run(
                ["codex", "cloud", "apply", task_id],
                cwd=str(ANALYZER_ROOT),
                timeout=120,
                check=False,
            )
            if apply.returncode != 0:
                raise RuntimeError(f"codex cloud apply exit {apply.returncode}")
            return
        time.sleep(20)
    raise RuntimeError(f"Cloud-Task {task_id} Timeout")


def run_pytest() -> None:
    venv_py = Path("/tmp/shab-analyzer-venv/bin/pytest")
    local_py = ANALYZER_ROOT / ".venv" / "bin" / "pytest"
    if venv_py.exists():
        cmd = [str(venv_py), str(ANALYZER_ROOT / "tests"), "-q"]
    elif local_py.exists():
        cmd = [str(local_py), str(ANALYZER_ROOT / "tests"), "-q"]
    else:
        cmd = [sys.executable, "-m", "pytest", str(ANALYZER_ROOT / "tests"), "-q"]
    _log("pytest " + " ".join(cmd[1:]))
    proc = subprocess.run(cmd, cwd=str(ANALYZER_ROOT), check=False)
    if proc.returncode != 0:
        raise RuntimeError("pytest nicht grün — kein Deploy")


def deploy() -> None:
    script = ANALYZER_ROOT / "scripts" / "remote" / "install-walk.sh"
    _log("deploy install-walk.sh")
    proc = subprocess.run(["bash", str(script)], cwd=str(ANALYZER_ROOT), check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"install-walk.sh exit {proc.returncode}")


def cycle_key(coverage: dict) -> str:
    return f"{coverage['parser_version']}:{coverage['counts'].get('partial', 0)}"


def should_skip_failed(state: dict, key: str, retry: bool) -> bool:
    """Block only pytest/deploy failures. Codex usage/capacity must retry without --retry."""
    if retry:
        return False
    return state.get("failed_key") == key and state.get("failed_kind") == "code"


def maybe_unlock_deferred(args: argparse.Namespace, coverage: dict, state: dict) -> dict:
    deferred = coverage["counts"].get("deferred", 0)
    unlocked = [p.strip() for p in str(coverage.get("unlocked") or "HR").split(",") if p.strip()]
    if deferred == 0:
        _log_idle("alles fertig (kein pending/partial/deferred). Warte auf neue XML.")
        return state
    _log(f"HR-PARTIAL leer. deferred={deferred} unlocked={','.join(unlocked)} — prüfe nächste Familie")
    fams = fetch_deferred_families()
    nxt = None
    for family in DEFERRED_RUBRIC_ORDER:
        if fams.get(family, 0) > 0:
            nxt = family
            break
    if nxt is None:
        leftover = ", ".join(f"{k}:{v}" for k, v in sorted(fams.items(), key=lambda kv: -kv[1]))
        _log_idle(f"keine nächste Familie, Rest {leftover or 'leer'} — warte")
        return state
    if args.dry_run:
        _log(f"dry-run: würde {nxt} freischalten ({fams.get(nxt)} deferred)")
        return state
    n = remote_unlock_family(nxt)
    _log(f"{nxt} freigeschaltet, {n} Items requeued. Walk übernimmt beim nächsten Tick.")
    return state


def maybe_run_parser(args: argparse.Namespace, coverage: dict, state: dict) -> dict:
    counts = coverage["counts"]
    pending = counts.get("pending", 0)
    partial = counts.get("partial", 0)
    if pending != 0:
        _log(
            f"warten: state={coverage['state']} parser={coverage['parser_version']} "
            f"pending={pending} ok={counts.get('ok')} partial={partial} "
            f"deferred={counts.get('deferred')} hb={coverage.get('heartbeat_at')}"
        )
        return state
    if partial == 0:
        return maybe_unlock_deferred(args, coverage, state)

    key = cycle_key(coverage)
    if state.get("handled_key") == key and not args.retry:
        _log(f"dieser complete-Stand wurde schon behandelt ({key}). --retry zum nochmal.")
        return state
    if should_skip_failed(state, key, args.retry):
        _log(f"letzter Code-Fehler für {key} (pytest/deploy). --retry zum nochmal.")
        return state
    nxt = state.get("codex_next_try") or ""
    if nxt and nxt > _now() and not args.retry:
        _log_idle(f"Codex-Pause bis {nxt} ({key})")
        return state

    local_ver = local_parser_version()
    server_ver = coverage["parser_version"]
    next_version = local_ver if local_ver > server_ver else server_ver + 1
    try:
        if local_ver > server_ver:
            _log(f"lokal schon PARSER_VERSION={local_ver}, Server {server_ver} — pytest + deploy, kein Codex")
            if args.dry_run:
                _log("dry-run: kein pytest/deploy")
                return state
            run_pytest()
            deploy()
        else:
            _log(f"complete + PARTIAL={partial} → Parser {next_version} ({args.engine})")
            require_engine_login(args.engine, context="vor Parser-Lauf")
            samples = export_samples()
            _log(f"Samples: {len(samples.get('copied') or [])} XML, {samples.get('clusters')} Cluster")
            prompt = build_prompt(coverage, samples, next_version)
            SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
            (SAMPLE_DIR / "prompt.md").write_text(prompt)
            if args.dry_run:
                _log(f"dry-run: Prompt nach {SAMPLE_DIR / 'prompt.md'}, kein Agent")
                return state
            if args.engine == "cloud":
                run_codex_cloud(prompt, args.cloud_env, args.codex_timeout)
            elif args.engine == "claude":
                run_claude_local(prompt, args.codex_timeout)
            else:
                run_codex_local(prompt, args.codex_timeout)
            after = local_parser_version()
            run_pytest()
            if after <= server_ver:
                raise RuntimeError(
                    f"PARSER_VERSION nicht erhöht (lokal {after}, Server {server_ver}) — kein Deploy"
                )
            deploy()
        state["handled_key"] = key
        state.pop("failed_key", None)
        state.pop("failed_kind", None)
        state.pop("codex_next_try", None)
        state["last_deployed"] = local_parser_version()
        state["last_ok_at"] = _now()
        save_state(state)
        _log(f"Parser {local_parser_version()} deployed. Nächster Tick wartet auf Walk complete.")
    except CodexUnavailable as exc:
        state.pop("failed_key", None)
        state.pop("failed_kind", None)
        state["codex_next_try"] = _later(CODEX_RETRY_SEC)
        save_state(state)
        _log(f"Codex CLI nicht bereit ({exc}). Nächster Versuch {state['codex_next_try']}.")
        return state
    except Exception:
        state["failed_key"] = key
        state["failed_kind"] = "code"
        save_state(state)
        raise
    return state


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lokaler Rule-Watchdog mit Codex CLI")
    p.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Sekunden zwischen Checks (default 120)")
    p.add_argument("--once", action="store_true", help="ein Check, dann Ende")
    p.add_argument("--dry-run", action="store_true", help="Samples+Prompt, kein Codex/Deploy")
    p.add_argument("--retry", action="store_true", help="denselben complete-Stand nochmal an Codex geben")
    p.add_argument("--engine", choices=("local", "cloud", "claude"), default="local")
    p.add_argument("--cloud-env", default=os.environ.get("CODEX_CLOUD_ENV"), help="für --engine cloud")
    p.add_argument("--codex-timeout", type=int, default=3600, help="Sekunden für Codex-Lauf")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.engine == "cloud" and not args.cloud_env:
        print("--engine cloud braucht --cloud-env ENV_ID (siehe: codex cloud)", file=sys.stderr)
        return 2
    if not SSH_KEY.exists():
        print(f"SSH-Key fehlt: {SSH_KEY}", file=sys.stderr)
        return 2

    login = require_engine_login(args.engine, context="Start")
    _log(f"login ok ({args.engine}): {login}")
    _log(
        f"Watchdog aktiv. Ctrl+C zum Stoppen. engine={args.engine} interval={args.interval}s "
        f"cwd={ANALYZER_ROOT}"
    )
    while True:
        state = load_state()
        try:
            coverage = fetch_coverage()
            state = maybe_run_parser(args, coverage, state)
        except KeyboardInterrupt:
            _log("gestoppt")
            return 130
        except Exception as exc:
            _log(f"Fehler: {exc}")
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(max(15, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
