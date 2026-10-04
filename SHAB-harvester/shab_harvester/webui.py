"""Small local dashboard over the harvester's SQLite state.

Stdlib only (http.server + sqlite3 + threading) — no JS framework, no extra
dependency. Two screens:

- Harvest  (/harvest): start any harvesting command as a background job and
  watch its log.
- Analyse  (/analyse): the raw state machine (days/publications) plus the
  aggregate layer (organizations/persons/cases) built by `analyze`.
"""
from __future__ import annotations

import html
import itertools
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import config
from . import db
from . import jobs
from .utils import now_iso

PROJECT_ROOT = db.DEFAULT_DB_PATH.parent.parent

STYLE = """
body { font-family: -apple-system, Helvetica, Arial, sans-serif; margin: 2rem; color: #1c1c1c; }
h1, h2 { margin-bottom: 0.3rem; }
table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
th, td { border-bottom: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.9rem; }
th { background: #f5f5f5; position: sticky; top: 0; }
a { color: #0b5fff; text-decoration: none; }
a:hover { text-decoration: underline; }
nav.topnav { margin-bottom: 1rem; }
nav.topnav a { margin-right: 1.2rem; font-weight: 600; }
.bar { background: #eee; border-radius: 4px; height: 10px; width: 200px; overflow: hidden; display: inline-block; vertical-align: middle; }
.bar-fill { background: #2e9e44; height: 100%; }
.status-pending { color: #888; }
.status-running { color: #c98a00; }
.status-discovered { color: #0b5fff; }
.status-completed { color: #2e9e44; }
.status-empty { color: #aaa; }
.status-failed { color: #cc3333; font-weight: 600; }
.status-scraped { color: #2e9e44; }
.status-success { color: #2e9e44; font-weight: 600; }
.pill { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 10px; font-size: 0.8rem; }
.pill-high { background: #e3f5e6; color: #1f7a32; }
.pill-low { background: #fdf0d5; color: #92660a; }
.filters a { margin-right: 0.6rem; }
.muted { color: #888; font-size: 0.85rem; }
.stats { display: flex; gap: 1.5rem; margin: 1rem 0; flex-wrap: wrap; }
.stat { background: #f5f5f5; border-radius: 6px; padding: 0.5rem 1rem; }
.stat .n { font-size: 1.3rem; font-weight: 700; display: block; }
dl.fields { display: grid; grid-template-columns: 220px 1fr; gap: 0.3rem 1rem; margin: 1rem 0; }
dl.fields dt { font-weight: 600; color: #555; }
dl.fields dd { margin: 0; word-break: break-word; }
pre.json, pre.log { background: #f5f5f5; padding: 0.8rem; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; }
iframe.raw-html { width: 100%; height: 500px; border: 1px solid #ddd; border-radius: 6px; }
form.job-form { background: #f9f9f9; border: 1px solid #eee; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
form.job-form h3 { margin: 0 0 0.6rem 0; }
form.job-form label { display: inline-block; margin-right: 1rem; font-size: 0.85rem; }
form.job-form input[type=text], form.job-form input[type=number] { padding: 0.3rem; margin-right: 0.6rem; }
form.job-form button { padding: 0.4rem 0.9rem; cursor: pointer; }
"""

NAV_LINKS = [
    ("/harvest", "Harvest"),
    ("/analyse", "Analyse"),
    ("/analyse/orgs", "Organizations"),
    ("/analyse/cases", "Cases"),
]


def _nav() -> str:
    links = "".join(f'<a href="{path}">{html.escape(label)}</a>' for path, label in NAV_LINKS)
    return f'<nav class="topnav">{links}</nav>'


def _page(title: str, body: str) -> bytes:
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{STYLE}</style></head><body>{_nav()}{body}</body></html>"""
    return html_doc.encode("utf-8")


def _progress_bar(scraped: int, total: int) -> str:
    pct = round((scraped / total) * 100) if total else 0
    return (
        f'<span class="bar"><span class="bar-fill" style="width:{pct}%"></span></span> '
        f'{scraped}/{total} ({pct}%)'
    )


def _stat(label: str, value) -> str:
    return f'<div class="stat"><span class="n">{value}</span>{html.escape(label)}</div>'


# ---------------------------------------------------------------------------
# Background job runner (Harvest screen)
# ---------------------------------------------------------------------------

class JobManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._counter = itertools.count(1)

    def start(self, command: str, params: dict, target) -> str:
        job_id = str(next(self._counter))
        job = {
            "id": job_id,
            "command": command,
            "params": params,
            "status": "running",
            "log": [],
            "started_at": now_iso(),
            "finished_at": None,
        }
        with self._lock:
            self._jobs[job_id] = job

        def log(msg: str) -> None:
            with self._lock:
                job["log"].append(str(msg))

        def run() -> None:
            try:
                target(log)
                with self._lock:
                    job["status"] = "success"
                    job["finished_at"] = now_iso()
            except Exception as exc:
                log(f"ERROR: {exc}")
                with self._lock:
                    job["status"] = "failed"
                    job["finished_at"] = now_iso()

        threading.Thread(target=run, daemon=True).start()
        return job_id

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job, log=list(job["log"])) if job else None

    def list_recent(self, limit: int = 30) -> list[dict]:
        with self._lock:
            ordered = sorted(self._jobs.values(), key=lambda j: int(j["id"]), reverse=True)
            return [dict(j, log=list(j["log"])) for j in ordered[:limit]]


JOB_MANAGER = JobManager()

JOB_COMMANDS = [
    "init-db", "export-data", "import-data", "reset-all",
    "seed-days", "discover-day", "discover-pending-days",
    "scrape-pending", "harvest-day", "harvest-range",
    "analyze", "reset-failed",
]


def _build_job_target(cmd: str, query: dict):
    def get(name: str, default: str | None = None) -> str | None:
        return query.get(name, [default])[0]

    def get_bool(name: str) -> bool:
        return get(name) is not None

    def get_int(name: str, default: int | None) -> int | None:
        value = get(name)
        return int(value) if value else default

    if cmd == "init-db":
        return lambda log: jobs.init_db(log=log)
    if cmd == "seed-days":
        return lambda log: jobs.seed_days(get("from"), get("to"), log=log)
    if cmd == "discover-day":
        return lambda log: jobs.discover_day(get("date"), get_bool("headless"), log=log)
    if cmd == "discover-pending-days":
        return lambda log: jobs.discover_pending_days(get_bool("headless"), log=log)
    if cmd == "scrape-pending":
        return lambda log: jobs.scrape_pending(get_int("limit", 100), get_bool("headless"), get_bool("force"), log=log)
    if cmd == "harvest-day":
        return lambda log: jobs.harvest_day(
            get("date"), get_int("limit", 100), get_bool("headless"), get_bool("force"), log=log
        )
    if cmd == "harvest-range":
        return lambda log: jobs.harvest_range(
            get("from"), get("to"), get_int("limit", 100), get_bool("headless"), get_bool("force"), log=log
        )
    if cmd == "reset-failed":
        return lambda log: jobs.reset_failed(log=log)
    if cmd == "analyze":
        return lambda log: jobs.analyze(get_int("limit", None), get_bool("force"), log=log)
    if cmd == "reset-all":
        confirmed = (get("confirm") or "").strip() == "RESET"
        return lambda log: jobs.reset_all(confirm=confirmed, log=log)
    if cmd == "export-data":
        return lambda log: jobs.export_data(log=log)
    if cmd == "import-data":
        zip_name = get("zip")
        confirmed = (get("confirm") or "").strip() == "IMPORT"

        def _run(log):
            if not zip_name:
                log("No export selected.")
                return
            zip_path = (jobs.EXPORT_DIR / zip_name).resolve()
            if jobs.EXPORT_DIR.resolve() not in zip_path.parents:
                log("Invalid export file.")
                return
            jobs.import_data(zip_path, confirm=confirmed, log=log)

        return _run
    return None


SEGMENTS = [
    {
        "title": "Data Segment",
        "explain": "Verwaltet die komplette Datenbasis als Einheit: Datenbank anlegen, "
                   "als ZIP sichern, aus einem ZIP wiederherstellen, oder alles löschen.",
        "after": "init-db: eine leere, aber vollständige DB mit allen Tabellen. "
                 "export: ein ZIP unter data/exports/ mit Zeitstempel im Namen (DB + raw_html + raw_xml), "
                 "das von delete/reset NICHT angefasst wird. import: DB + raw-Dateien exakt wie im gewählten ZIP "
                 "(alles Aktuelle wird vorher überschrieben). delete: alles weg, aber Schema wieder leer angelegt.",
        "forms": [
            ("init-db", "Init DB", ""),
            ("export-data", "Export (ZIP-Backup)", ""),
            ("import-data", "Import (aus ZIP-Backup)", None),  # special-cased below
            ("reset-all", "Alles löschen", '<label style="color:#cc3333">Deletes the entire DB and all '
             'raw_html/raw_xml files. Type RESET to confirm: <input type="text" name="confirm"></label>'),
        ],
    },
    {
        "title": "Discover Segment",
        "explain": "Legt fest, welche Tage überhaupt bearbeitet werden sollen (seed), und durchsucht "
                   "anschliessend SHAB für diese Tage (discover) — danach sind die gefundenen shab-ids "
                   "in der Warteschlange, aber noch ohne Inhalt.",
        "after": "seed: import_day-Zeilen (status pending) für jeden Tag im Zeitraum. "
                 "discover-day/discover-pending-days: publication_queue gefüllt mit den an diesen Tagen "
                 "gefundenen shab-ids (status pending) — bereit zum Scrapen.",
        "forms": [
            ("seed-days", "Seed days (Zeitraum festlegen)",
             '<label>Von <input type="text" name="from" placeholder="2018-09-02"></label>'
             '<label>Bis <input type="text" name="to" placeholder="2018-09-05"></label>'),
            ("discover-day", "Discover ein Tag",
             '<label>Datum <input type="text" name="date" placeholder="2018-09-03"></label>'
             '<label><input type="checkbox" name="headless" checked> headless</label>'),
            ("discover-pending-days", "Discover alle ausstehenden Tage",
             '<label><input type="checkbox" name="headless" checked> headless</label>'),
        ],
    },
    {
        "title": "Scrape Segment",
        "explain": "Lädt für jede in der Queue gefundene shab-id die Detailseite: Metadaten, UID, "
                   "XML/PDF/ZEFIX-Links, Volltext. harvest-day/harvest-range bündeln Discover+Scrape "
                   "für Tage, die noch nicht durchsucht wurden.",
        "after": "shab_publication_raw-Zeilen mit allen Detaildaten, plus gespeicherte Dateien unter "
                 "data/raw_html/YYYY/MM/ und data/raw_xml/YYYY/MM/.",
        "forms": [
            ("scrape-pending", "Scrape pending",
             '<label>Limit <input type="number" name="limit" value="100"></label>'
             '<label><input type="checkbox" name="headless" checked> headless</label>'
             '<label><input type="checkbox" name="force"> force re-download</label>'),
            ("harvest-day", "Harvest day (discover + scrape)",
             '<label>Datum <input type="text" name="date" placeholder="2018-09-03"></label>'
             '<label>Limit <input type="number" name="limit" value="100"></label>'
             '<label><input type="checkbox" name="headless" checked> headless</label>'),
            ("harvest-range", "Harvest range (discover + scrape)",
             '<label>Von <input type="text" name="from" placeholder="2018-09-02"></label>'
             '<label>Bis <input type="text" name="to" placeholder="2018-09-05"></label>'
             '<label>Limit <input type="number" name="limit" value="100"></label>'
             '<label><input type="checkbox" name="headless" checked> headless</label>'),
        ],
    },
    {
        "title": "Analyse / Maintenance Segment",
        "explain": "analyze baut aus den rohen Publikationen die Organization/Case/Person-Aggregation "
                   "(siehe Analyse-Screen). reset-failed gibt gescheiterten Tagen/Einträgen eine neue "
                   "Chance, indem ihr Status zurück auf pending gesetzt wird.",
        "after": "analyze: organizations/cases/persons-Tabellen befüllt bzw. aktualisiert. "
                 "reset-failed: vorher failed-markierte import_day/publication_queue-Zeilen sind wieder "
                 "pending und werden beim nächsten Discover/Scrape-Lauf erneut versucht.",
        "forms": [
            ("analyze", "Analyze (Aggregation aufbauen)",
             '<label>Limit <input type="number" name="limit" placeholder="(alle)"></label>'
             '<label><input type="checkbox" name="force"> force reprocess</label>'),
            ("reset-failed", "Reset failed", ""),
        ],
    },
]


def _import_data_form() -> str:
    exports = jobs.list_exports(jobs.EXPORT_DIR)
    if not exports:
        return "<p class='muted'>Noch kein Export vorhanden — erst 'Export (ZIP-Backup)' ausführen.</p>"
    options = "".join(f'<option value="{html.escape(p.name)}">{html.escape(p.name)}</option>' for p in exports)
    return (
        f'<label>ZIP <select name="zip">{options}</select></label>'
        '<label style="color:#cc3333">Überschreibt die aktuelle DB/Dateien. '
        'Type IMPORT to confirm: <input type="text" name="confirm"></label>'
    )


def render_harvest() -> bytes:
    body = ["<h1>Harvest</h1>", '<p class="muted">Start any harvesting command. Each run is a background job.</p>']

    for segment in SEGMENTS:
        body.append(f"<h2>{html.escape(segment['title'])}</h2>")
        body.append(f"<p>{html.escape(segment['explain'])}</p>")
        body.append(f"<p class='muted'><strong>Danach hast du:</strong> {html.escape(segment['after'])}</p>")
        for cmd, label, fields in segment["forms"]:
            if fields is None:  # import-data: dynamic dropdown of available exports
                fields = _import_data_form()
            body.append(
                f'<form class="job-form" method="get" action="/harvest/run">'
                f'<h3>{html.escape(label)}</h3>'
                f'<input type="hidden" name="cmd" value="{cmd}">'
                f"{fields}"
                f'<button type="submit">Run</button>'
                f"</form>"
            )

    jobs_list = JOB_MANAGER.list_recent()
    body.append("<h2>Recent jobs</h2>")
    if not jobs_list:
        body.append("<p class='muted'>No jobs started yet.</p>")
    else:
        body.append("<table><tr><th>id</th><th>command</th><th>status</th><th>started</th><th>finished</th><th></th></tr>")
        for job in jobs_list:
            body.append(
                "<tr>"
                f'<td>{job["id"]}</td>'
                f'<td>{html.escape(job["command"])}</td>'
                f'<td><span class="status-{job["status"]}">{job["status"]}</span></td>'
                f'<td class="muted">{job["started_at"]}</td>'
                f'<td class="muted">{job["finished_at"] or "-"}</td>'
                f'<td><a href="/harvest/job?id={job["id"]}">log</a></td>'
                "</tr>"
            )
        body.append("</table>")

    return _page("Harvest", "\n".join(body))


def render_job(job: dict | None, job_id: str) -> bytes:
    if not job:
        return _page("Not found", f"<h1>Unknown job</h1><p>{html.escape(job_id)}</p><p><a href='/harvest'>&larr; back</a></p>")

    refresh = '<meta http-equiv="refresh" content="2">' if job["status"] == "running" else ""
    body = [
        f"<h1>Job {job['id']}: {html.escape(job['command'])}</h1>",
        '<p><a href="/harvest">&larr; back to harvest</a></p>',
        f'<p>Status: <span class="status-{job["status"]}">{job["status"]}</span> '
        f'&middot; started {job["started_at"]} &middot; finished {job["finished_at"] or "-"}</p>',
        f"<pre class='log'>{html.escape(chr(10).join(job['log']) or '(no output yet)')}</pre>",
    ]
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8">{refresh}<title>Job {html.escape(job['id'])}</title>
<style>{STYLE}</style></head><body>{_nav()}{''.join(body)}</body></html>"""
    return html_doc.encode("utf-8")


# ---------------------------------------------------------------------------
# Analyse screen: raw state machine
# ---------------------------------------------------------------------------

def render_overview(conn) -> bytes:
    rows = db.all_import_days(conn)

    total_raw = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw")
    with_uid = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE uid IS NOT NULL")
    with_zefix = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE zefix_url IS NOT NULL")
    with_xml = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE xml_url IS NOT NULL")
    queue_failed = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status = 'failed'")
    queue_pending = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status = 'pending'")
    agg = db.aggregate_counts(conn)

    body = ["<h1>Analyse</h1>", '<p class="muted">Overview of all import_day rows.</p>']
    body.append(
        '<div class="stats">'
        + _stat("publications collected", total_raw)
        + _stat("with UID", with_uid)
        + _stat("with ZEFIX link", with_zefix)
        + _stat("with XML", with_xml)
        + _stat("queue pending", queue_pending)
        + _stat("queue failed", queue_failed)
        + "</div>"
    )
    body.append(
        '<div class="stats">'
        + _stat("organizations", agg["organizations"])
        + _stat("organizations with UID", agg["organizations_with_uid"])
        + _stat("persons", agg["persons"])
        + _stat("cases", agg["cases"])
        + _stat("cases open", agg["cases_open"])
        + _stat("analyzed publications", agg["processed_publications"])
        + "</div>"
        + '<p><a href="/analyse/orgs">browse organizations &rarr;</a> &middot; '
        '<a href="/analyse/cases">browse cases &rarr;</a></p>'
    )
    body.append("<table><tr><th>Date</th><th>Status</th><th>Result count</th>"
                "<th>Scraped progress</th><th>Failed</th><th></th></tr>")
    for row in rows:
        total = row["queue_total"] or 0
        scraped = row["queue_scraped"] or 0
        failed = row["queue_failed"] or 0
        date = row["publication_date"]
        result_count = row["result_count"] if row["result_count"] is not None else "-"
        failed_cell = f'<span class="status-failed">{failed}</span>' if failed else "0"
        body.append(
            "<tr>"
            f'<td><a href="/analyse/day?date={date}">{date}</a></td>'
            f'<td><span class="status-{row["status"]}">{row["status"]}</span></td>'
            f"<td>{result_count}</td>"
            f"<td>{_progress_bar(scraped, total)}</td>"
            f"<td>{failed_cell}</td>"
            f'<td><a href="/analyse/day?date={date}">details</a></td>'
            "</tr>"
        )
    body.append("</table>")
    return _page("Analyse", "\n".join(body))


def render_day(conn, date: str, status_filter: str | None) -> bytes:
    day = db.get_import_day(conn, date)
    if not day:
        return _page("Not found", f"<h1>No import_day for {html.escape(date)}</h1><p><a href='/analyse'>back</a></p>")

    rows = db.day_overview(conn, date, status=status_filter)

    body = [
        f'<h1>{date}</h1>',
        f'<p>import_day.status = <span class="status-{day["status"]}">{day["status"]}</span> '
        f'&middot; result_count = {day["result_count"]} &middot; discovered_count = {day["discovered_count"]} '
        f'&middot; scraped_count = {day["scraped_count"]}</p>',
        '<p><a href="/analyse">&larr; back to overview</a></p>',
        '<p class="filters">Filter: '
        f'<a href="/analyse/day?date={date}">all</a> '
        f'<a href="/analyse/day?date={date}&status=pending">pending</a> '
        f'<a href="/analyse/day?date={date}&status=running">running</a> '
        f'<a href="/analyse/day?date={date}&status=scraped">scraped</a> '
        f'<a href="/analyse/day?date={date}&status=failed">failed</a>'
        "</p>",
    ]

    body.append("<table><tr><th>publication_id</th><th>number</th><th>status</th>"
                "<th>attempts</th><th>raw</th><th>title</th><th>last_error</th></tr>")
    for row in rows:
        pub_id = row["publication_id"]
        body.append(
            "<tr>"
            f'<td><a href="/analyse/pub?id={pub_id}">{html.escape(pub_id)}</a></td>'
            f'<td>{html.escape(row["publication_number"] or "-")}</td>'
            f'<td><span class="status-{row["status"]}">{row["status"]}</span></td>'
            f'<td>{row["attempt_count"]}</td>'
            f'<td>{"yes" if row["has_raw"] else "no"}</td>'
            f'<td>{html.escape(row["title"] or "")}</td>'
            f'<td class="muted">{html.escape(row["last_error"] or "")}</td>'
            "</tr>"
        )
    body.append("</table>")
    if not rows:
        body.append("<p class='muted'>No publications match this filter.</p>")
    return _page(f"Analyse - {date}", "\n".join(body))


RAW_FIELDS = [
    ("Status", "status"),
    ("Category", "category"),
    ("Subcategory", "subcategory"),
    ("Language", "language"),
    ("Canton", "canton"),
    ("Title", "title"),
    ("Publishing entity", "company_name_raw"),
    ("UID", "uid"),
    ("Company block text", "company_block_text"),
    ("Body text", "body_text"),
    ("Journal number", "journal_number"),
    ("Journal date", "journal_date"),
    ("Previous SOGC number", "previous_sogc_number"),
    ("Previous SOGC date", "previous_sogc_date"),
    ("Previous publication number", "previous_publication_number"),
    ("Contact point", "contact_point"),
    ("Content hash", "content_hash"),
    ("Scraped at", "scraped_at"),
]

LINK_FIELDS = [
    ("Detail URL", "detail_url"),
    ("XML URL", "xml_url"),
    ("PDF URL", "pdf_url"),
    ("ZEFIX URL", "zefix_url"),
]


def render_publication(conn, publication_id: str) -> bytes:
    queue_item = db.get_queue_item(conn, publication_id)
    if not queue_item:
        return _page(
            "Not found",
            f"<h1>Unknown publication_id</h1><p>{html.escape(publication_id)}</p>"
            "<p><a href='/analyse'>&larr; back</a></p>",
        )

    raw = db.get_publication_raw(conn, publication_id)

    body = [
        f"<h1>{html.escape(publication_id)}</h1>",
        f'<p><a href="/analyse/day?date={queue_item["publication_date"]}">'
        f'&larr; back to {queue_item["publication_date"]}</a></p>',
        f'<p>Queue status: <span class="status-{queue_item["status"]}">{queue_item["status"]}</span> '
        f"&middot; attempts: {queue_item['attempt_count']} "
        f'&middot; last_error: {html.escape(queue_item["last_error"] or "-")}</p>',
    ]

    if not raw:
        body.append("<p class='muted'>Not scraped yet — no shab_publication_raw row.</p>")
        return _page(f"Analyse - {publication_id}", "\n".join(body))

    org_row = conn.execute(
        "SELECT org_key FROM organization_publications WHERE publication_id = ?", (publication_id,)
    ).fetchone()
    if org_row:
        body.append(f'<p><a href="/analyse/org?key={org_row["org_key"]}">view organization &rarr;</a></p>')

    body.append("<dl class='fields'>")
    for label, field in RAW_FIELDS:
        value = raw[field]
        if value:
            body.append(f"<dt>{html.escape(label)}</dt><dd>{html.escape(str(value))}</dd>")
    for label, field in LINK_FIELDS:
        value = raw[field]
        if value:
            body.append(
                f'<dt>{html.escape(label)}</dt><dd><a href="{html.escape(value)}" '
                f'target="_blank" rel="noopener">{html.escape(value)}</a></dd>'
            )
    body.append("</dl>")

    if raw["raw_page_html_path"]:
        body.append(
            "<h2>Stored detail page HTML</h2>"
            f'<p class="muted">{html.escape(raw["raw_page_html_path"])}</p>'
            f'<iframe class="raw-html" src="/raw/html?id={publication_id}"></iframe>'
        )
    if raw["raw_xml_path"]:
        body.append(
            "<h2>Stored XML</h2>"
            f'<p class="muted">{html.escape(raw["raw_xml_path"])} '
            f'(<a href="/raw/xml?id={publication_id}" target="_blank">open</a>)</p>'
        )

    for label, field in [
        ("raw_metadata_json", "raw_metadata_json"),
        ("raw_links_json", "raw_links_json"),
        ("raw_content_json", "raw_content_json"),
    ]:
        if raw[field]:
            body.append(f"<h2>{label}</h2><pre class='json'>{html.escape(raw[field])}</pre>")

    return _page(f"Analyse - {publication_id}", "\n".join(body))


# ---------------------------------------------------------------------------
# Analyse screen: aggregate layer (organizations / persons / cases)
# ---------------------------------------------------------------------------

def render_organizations(conn, search: str | None) -> bytes:
    rows = db.list_organizations(conn, search)
    body = ["<h1>Organizations</h1>", '<p><a href="/analyse">&larr; back to overview</a></p>']
    body.append(
        '<form method="get" action="/analyse/orgs">'
        f'<input type="text" name="search" placeholder="name or UID" value="{html.escape(search or "")}">'
        '<button type="submit">Search</button></form>'
    )
    body.append("<table><tr><th>Organization</th><th>UID</th><th>Confidence</th><th>Canton</th>"
                "<th>Publications</th><th>First seen</th><th>Last seen</th></tr>")
    for row in rows:
        pill_class = "pill-high" if row["match_confidence"] == "HIGH" else "pill-low"
        body.append(
            "<tr>"
            f'<td><a href="/analyse/org?key={row["org_key"]}">{html.escape(row["name_current"] or row["org_key"])}</a></td>'
            f'<td>{html.escape(row["uid"] or "-")}</td>'
            f'<td><span class="pill {pill_class}">{row["match_confidence"]}</span></td>'
            f'<td>{html.escape(row["canton"] or "-")}</td>'
            f'<td>{row["publication_count"]}</td>'
            f'<td class="muted">{row["first_seen_at"] or "-"}</td>'
            f'<td class="muted">{row["last_seen_at"] or "-"}</td>'
            "</tr>"
        )
    body.append("</table>")
    if not rows:
        body.append("<p class='muted'>No organizations yet — run `analyze` on the Harvest screen first.</p>")
    return _page("Organizations", "\n".join(body))


def render_organization(conn, org_key: str) -> bytes:
    org = db.get_organization(conn, org_key)
    if not org:
        return _page("Not found", f"<h1>Unknown organization</h1><p>{html.escape(org_key)}</p>"
                                   "<p><a href='/analyse/orgs'>&larr; back</a></p>")

    pill_class = "pill-high" if org["match_confidence"] == "HIGH" else "pill-low"
    body = [
        f"<h1>{html.escape(org['name_current'] or org_key)}</h1>",
        '<p><a href="/analyse/orgs">&larr; back to organizations</a></p>',
        f'<p>UID: {html.escape(org["uid"] or "-")} &middot; '
        f'confidence: <span class="pill {pill_class}">{org["match_confidence"]}</span> &middot; '
        f'canton: {html.escape(org["canton"] or "-")}'
        + (f' &middot; <a href="{html.escape(org["zefix_url"])}" target="_blank">ZEFIX</a>' if org["zefix_url"] else "")
        + "</p>",
    ]

    cases = db.organization_cases(conn, org_key)
    if cases:
        body.append("<h2>Cases / Verfahren</h2><table><tr><th>Type</th><th>Status</th><th>Office</th>"
                    "<th>Opened</th><th>Closed</th><th></th></tr>")
        for case in cases:
            body.append(
                "<tr>"
                f'<td>{html.escape(case["case_type"])}</td>'
                f'<td><span class="status-{case["status"] or "pending"}">{case["status"] or "-"}</span></td>'
                f'<td>{html.escape(case["office"] or "-")}</td>'
                f'<td>{case["opened_date"] or "-"}</td>'
                f'<td>{case["closed_date"] or "-"}</td>'
                f'<td><a href="/analyse/case?id={case["case_id"]}">details</a></td>'
                "</tr>"
            )
        body.append("</table>")

    pubs = db.organization_publication_rows(conn, org_key)
    body.append("<h2>Publications</h2><table><tr><th>Date</th><th>Event type</th><th>Confidence</th><th>Title</th></tr>")
    for pub in pubs:
        body.append(
            "<tr>"
            f'<td>{pub["publication_date"]}</td>'
            f'<td>{html.escape(pub["event_type"] or "-")}</td>'
            f'<td class="muted">{html.escape(pub["confidence"] or "-")}</td>'
            f'<td><a href="/analyse/pub?id={pub["publication_id"]}">{html.escape(pub["title"] or pub["publication_id"])}</a></td>'
            "</tr>"
        )
    body.append("</table>")

    persons = db.organization_persons(conn, org_key)
    if persons:
        body.append("<h2>Persons (extracted, best-effort)</h2><table><tr><th>Name</th><th>Place</th>"
                    "<th>Role</th><th>Signing</th><th>Action</th><th>As of</th></tr>")
        for person in persons:
            body.append(
                "<tr>"
                f'<td>{html.escape(person["full_name"] or "-")}</td>'
                f'<td>{html.escape(person["place"] or "-")}</td>'
                f'<td>{html.escape(person["role"] or "-")}</td>'
                f'<td>{html.escape(person["signing_authority"] or "-")}</td>'
                f'<td>{html.escape(person["mutation_action"] or "-")}</td>'
                f'<td class="muted">{person["valid_from_publication_date"] or "-"}</td>'
                "</tr>"
            )
        body.append("</table>")

    return _page(f"Organization - {org['name_current'] or org_key}", "\n".join(body))


def render_cases(conn) -> bytes:
    rows = db.list_cases(conn)
    body = ["<h1>Cases</h1>", '<p><a href="/analyse">&larr; back to overview</a></p>']
    body.append("<table><tr><th>Case</th><th>Type</th><th>Status</th><th>Debtor</th><th>Office</th>"
                "<th>Opened</th><th>Closed</th></tr>")
    for row in rows:
        body.append(
            "<tr>"
            f'<td><a href="/analyse/case?id={row["case_id"]}">{html.escape(row["case_id"])}</a></td>'
            f'<td>{html.escape(row["case_type"])}</td>'
            f'<td><span class="status-{row["status"] or "pending"}">{row["status"] or "-"}</span></td>'
            f'<td>{html.escape(row["debtor_name"] or "-")}</td>'
            f'<td>{html.escape(row["office"] or "-")}</td>'
            f'<td>{row["opened_date"] or "-"}</td>'
            f'<td>{row["closed_date"] or "-"}</td>'
            "</tr>"
        )
    body.append("</table>")
    if not rows:
        body.append("<p class='muted'>No cases yet — run `analyze` on the Harvest screen first.</p>")
    return _page("Cases", "\n".join(body))


def render_case(conn, case_id: str) -> bytes:
    case = db.get_case(conn, case_id)
    if not case:
        return _page("Not found", f"<h1>Unknown case</h1><p>{html.escape(case_id)}</p>"
                                   "<p><a href='/analyse/cases'>&larr; back</a></p>")

    body = [
        f"<h1>{html.escape(case_id)}</h1>",
        '<p><a href="/analyse/cases">&larr; back to cases</a></p>',
        f'<p>Type: {html.escape(case["case_type"])} &middot; status: '
        f'<span class="status-{case["status"] or "pending"}">{case["status"] or "-"}</span> &middot; '
        f'debtor: {html.escape(case["debtor_name"] or "-")} &middot; office: {html.escape(case["office"] or "-")}</p>',
        f'<p>Opened: {case["opened_date"] or "-"} &middot; Closed: {case["closed_date"] or "-"}'
        + (f' &middot; <a href="/analyse/org?key={case["org_key"]}">organization</a>' if case["org_key"] else "")
        + "</p>",
    ]

    pubs = db.case_publication_rows(conn, case_id)
    body.append("<h2>Events</h2><table><tr><th>Date</th><th>Event</th><th>Publication</th></tr>")
    for pub in pubs:
        body.append(
            "<tr>"
            f'<td>{pub["publication_date"]}</td>'
            f'<td>{html.escape(pub["case_event_type"] or "-")}</td>'
            f'<td><a href="/analyse/pub?id={pub["publication_id"]}">{html.escape(pub["title"] or pub["publication_id"])}</a></td>'
            "</tr>"
        )
    body.append("</table>")
    return _page(f"Case - {case_id}", "\n".join(body))


def _resolve_raw_file(relative_path: str) -> Path | None:
    candidate = (PROJECT_ROOT / relative_path).resolve()
    if PROJECT_ROOT.resolve() not in candidate.parents:
        return None
    return candidate if candidate.is_file() else None


def make_handler(db_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # quieter default logging
            pass

        def _redirect(self, location: str) -> None:
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            if parsed.path in ("/raw/html", "/raw/xml"):
                self._serve_raw_file(parsed.path, query)
                return

            if parsed.path == "/":
                self._redirect("/analyse")
                return

            if parsed.path == "/harvest":
                self._respond(render_harvest())
                return

            if parsed.path == "/harvest/run":
                cmd = query.get("cmd", [None])[0]
                target = _build_job_target(cmd, query) if cmd else None
                if not target:
                    self.send_response(400)
                    self.end_headers()
                    return
                job_id = JOB_MANAGER.start(cmd, query, target)
                self._redirect(f"/harvest/job?id={job_id}")
                return

            if parsed.path == "/harvest/job":
                job_id = query.get("id", [None])[0]
                self._respond(render_job(JOB_MANAGER.get(job_id) if job_id else None, job_id or ""))
                return

            conn = db.get_connection(db_path)
            try:
                if parsed.path == "/analyse":
                    body = render_overview(conn)
                elif parsed.path == "/analyse/day":
                    date = query.get("date", [None])[0]
                    status_filter = query.get("status", [None])[0]
                    if not date:
                        self.send_response(400)
                        self.end_headers()
                        return
                    body = render_day(conn, date, status_filter)
                elif parsed.path == "/analyse/pub":
                    publication_id = query.get("id", [None])[0]
                    if not publication_id:
                        self.send_response(400)
                        self.end_headers()
                        return
                    body = render_publication(conn, publication_id)
                elif parsed.path == "/analyse/orgs":
                    body = render_organizations(conn, query.get("search", [None])[0])
                elif parsed.path == "/analyse/org":
                    org_key = query.get("key", [None])[0]
                    if not org_key:
                        self.send_response(400)
                        self.end_headers()
                        return
                    body = render_organization(conn, org_key)
                elif parsed.path == "/analyse/cases":
                    body = render_cases(conn)
                elif parsed.path == "/analyse/case":
                    case_id = query.get("id", [None])[0]
                    if not case_id:
                        self.send_response(400)
                        self.end_headers()
                        return
                    body = render_case(conn, case_id)
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
            finally:
                conn.close()

            self._respond(body)

        def _respond(self, body: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _serve_raw_file(self, path: str, query: dict) -> None:
            publication_id = query.get("id", [None])[0]
            if not publication_id:
                self.send_response(400)
                self.end_headers()
                return

            conn = db.get_connection(db_path)
            try:
                raw = db.get_publication_raw(conn, publication_id)
            finally:
                conn.close()

            if not raw:
                self.send_response(404)
                self.end_headers()
                return

            relative_path = raw["raw_page_html_path"] if path == "/raw/html" else raw["raw_xml_path"]
            file_path = _resolve_raw_file(relative_path) if relative_path else None
            if not file_path:
                self.send_response(404)
                self.end_headers()
                return

            content_type = "text/html; charset=utf-8" if path == "/raw/html" else "application/xml; charset=utf-8"
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def run_server(
    host: str = config.WEBUI_HOST, port: int = config.WEBUI_PORT, db_path: Path = db.DEFAULT_DB_PATH
) -> None:
    server = HTTPServer((host, port), make_handler(db_path))
    print(f"shab_harvester dashboard running at http://{host}:{port}/  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
