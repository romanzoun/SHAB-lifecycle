from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from . import db
from . import jobs
from . import webui


def cmd_init_db(args: argparse.Namespace) -> None:
    jobs.init_db()


def cmd_seed_days(args: argparse.Namespace) -> None:
    jobs.seed_days(args.from_date, args.to_date)


def cmd_discover_day(args: argparse.Namespace) -> None:
    jobs.discover_day(args.date, args.headless)


def cmd_discover_pending_days(args: argparse.Namespace) -> None:
    jobs.discover_pending_days(args.headless)


def cmd_scrape_pending(args: argparse.Namespace) -> None:
    jobs.scrape_pending(args.limit, args.headless, args.force)


def cmd_harvest_day(args: argparse.Namespace) -> None:
    jobs.harvest_day(args.date, args.limit, args.headless, args.force)


def cmd_harvest_range(args: argparse.Namespace) -> None:
    jobs.harvest_range(args.from_date, args.to_date, args.limit, args.headless, args.force)


def cmd_reset_failed(args: argparse.Namespace) -> None:
    jobs.reset_failed()


def cmd_archive_non_public(args: argparse.Namespace) -> None:
    jobs.archive_non_public()


def cmd_reset_all(args: argparse.Namespace) -> None:
    if not args.yes:
        print(
            "This deletes the entire database and all downloaded raw_html/raw_xml files.\n"
            "Re-run with --yes to confirm."
        )
        return
    jobs.reset_all(confirm=True)


def cmd_analyze(args: argparse.Namespace) -> None:
    jobs.analyze(args.limit, args.force)


def cmd_export_data(args: argparse.Namespace) -> None:
    jobs.export_data()


def cmd_import_data(args: argparse.Namespace) -> None:
    if not args.yes:
        print(
            "This deletes whatever is currently in the database/raw files and replaces it "
            f"with the contents of {args.zip}.\nRe-run with --yes to confirm."
        )
        return
    jobs.import_data(Path(args.zip), confirm=True)


def cmd_status(args: argparse.Namespace) -> None:
    with db.connect() as conn:
        repaired = db.repair_queue_status(conn)
        if repaired:
            print(f"Repaired {repaired} queue item(s) whose raw row already existed.")

        print("import_day by status:")
        for status, count in db.counts_by_status(conn, "import_day").items():
            print(f"  {status}: {count}")

        print("publication_queue by status:")
        for status, count in db.counts_by_status(conn, "publication_queue").items():
            print(f"  {status}: {count}")

        total_raw = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw")
        with_uid = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE uid IS NOT NULL")
        with_zefix = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE zefix_url IS NOT NULL")
        with_xml = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE xml_url IS NOT NULL")
        failed_count = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status = 'failed'")
        non_public_q = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status = 'non_public'")
        try:
            non_public_raw = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_non_public")
        except Exception:
            non_public_raw = 0

        print(f"shab_publication_raw total: {total_raw}")
        print(f"  with uid: {with_uid}")
        print(f"  with zefix_url: {with_zefix}")
        print(f"  with xml_url: {with_xml}")
        print(f"failed queue items: {failed_count}")
        print(f"non_public queue items: {non_public_q}")
        print(f"shab_publication_non_public: {non_public_raw}")

        agg = db.aggregate_counts(conn)
        print(f"organizations: {agg['organizations']} (with uid: {agg['organizations_with_uid']})")
        print(f"persons: {agg['persons']}")
        print(f"cases: {agg['cases']} (open: {agg['cases_open']})")
        print(f"analyzed publications: {agg['processed_publications']}")

        failed_items = db.failed_queue_items(conn, limit=20)
        if failed_items:
            print("First 20 failed items:")
            for row in failed_items:
                print(
                    f"  {row['publication_id']} ({row['publication_date']}) "
                    f"attempts={row['attempt_count']} error={row['last_error']}"
                )


STATUS_MARK = {
    "scraped": "[x]",
    "running": "[~]",
    "failed": "[!]",
    "non_public": "[np]",
    "pending": "[ ]",
}



def cmd_day_overview(args: argparse.Namespace) -> None:
    with db.connect() as conn:
        day = db.get_import_day(conn, args.date)
        if not day:
            print(f"No import_day found for {args.date}.")
            return

        rows = db.day_overview(conn, args.date, status=args.status)
        print(f"Day {args.date}: import_day.status={day['status']} result_count={day['result_count']}")
        if not rows:
            print("  (no publications match the filter)")
            return

        for row in rows:
            mark = STATUS_MARK.get(row["status"], "[?]")
            raw_flag = "raw" if row["has_raw"] else "no-raw"
            line = (
                f"  {mark} {row['publication_id']} {row['publication_number'] or '-'} "
                f"status={row['status']} attempts={row['attempt_count']} {raw_flag}"
            )
            if row["title"]:
                line += f" - {row['title']}"
            if row["last_error"]:
                line += f" | last_error={row['last_error']}"
            print(line)

        total = len(rows)
        done = sum(1 for row in rows if row["status"] == "scraped")
        print(f"  {done}/{total} scraped")


def cmd_webui(args: argparse.Namespace) -> None:
    webui.run_server(host=args.host, port=args.port)


def cmd_verify_day(args: argparse.Namespace) -> None:
    with db.connect() as conn:
        day = db.get_import_day(conn, args.date)
        if not day:
            print(f"No import_day found for {args.date}.")
            return
        queue_count = db.scalar(
            conn, "SELECT COUNT(*) FROM publication_queue WHERE publication_date = ?", (args.date,)
        )
        scraped_count = db.scalar(
            conn,
            "SELECT COUNT(*) FROM publication_queue WHERE publication_date = ? AND status = 'scraped'",
            (args.date,),
        )
        raw_count = db.scalar(
            conn, "SELECT COUNT(*) FROM shab_publication_raw WHERE publication_date = ?", (args.date,)
        )

        print(f"Verify {args.date}:")
        print(f"  result_count: {day['result_count']}")
        print(f"  discovered_count: {day['discovered_count']}")
        print(f"  publication_queue rows: {queue_count}")
        print(f"  scraped queue rows: {scraped_count}")
        print(f"  shab_publication_raw rows: {raw_count}")

        if day["result_count"] is not None and day["result_count"] != queue_count:
            print(f"  WARNING: result_count ({day['result_count']}) != queue count ({queue_count})")
        if scraped_count != raw_count:
            print(f"  WARNING: scraped_count ({scraped_count}) != raw count ({raw_count})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shab_harvester")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("init-db")
    p.set_defaults(func=cmd_init_db)

    p = subparsers.add_parser("seed-days")
    p.add_argument("--from", dest="from_date", required=True)
    p.add_argument("--to", dest="to_date", required=True)
    p.set_defaults(func=cmd_seed_days)

    p = subparsers.add_parser("discover-day")
    p.add_argument("--date", required=True)
    p.add_argument("--headless", action=argparse.BooleanOptionalAction, default=config.HEADLESS_DEFAULT)
    p.set_defaults(func=cmd_discover_day)

    p = subparsers.add_parser("discover-pending-days")
    p.add_argument("--headless", action=argparse.BooleanOptionalAction, default=config.HEADLESS_DEFAULT)
    p.set_defaults(func=cmd_discover_pending_days)

    p = subparsers.add_parser("scrape-pending")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--headless", action=argparse.BooleanOptionalAction, default=config.HEADLESS_DEFAULT)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scrape_pending)

    p = subparsers.add_parser("harvest-day")
    p.add_argument("--date", required=True)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--headless", action=argparse.BooleanOptionalAction, default=config.HEADLESS_DEFAULT)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_harvest_day)

    p = subparsers.add_parser("harvest-range")
    p.add_argument("--from", dest="from_date", required=True)
    p.add_argument("--to", dest="to_date", required=True)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--headless", action=argparse.BooleanOptionalAction, default=config.HEADLESS_DEFAULT)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_harvest_range)

    p = subparsers.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = subparsers.add_parser("reset-failed")
    p.set_defaults(func=cmd_reset_failed)

    p = subparsers.add_parser(
        "archive-non-public",
        help="Archive exhausted failed queue items as non_public (list metadata only).",
    )
    p.set_defaults(func=cmd_archive_non_public)

    p = subparsers.add_parser("reset-all", help="Delete the entire DB and all raw_html/raw_xml files, then re-init.")
    p.add_argument("--yes", action="store_true", help="Required to actually perform the reset.")
    p.set_defaults(func=cmd_reset_all)

    p = subparsers.add_parser("verify-day")
    p.add_argument("--date", required=True)
    p.set_defaults(func=cmd_verify_day)

    p = subparsers.add_parser("day-overview")
    p.add_argument("--date", required=True)
    p.add_argument("--status", choices=["pending", "running", "scraped", "failed"], default=None)
    p.set_defaults(func=cmd_day_overview)

    p = subparsers.add_parser("analyze")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_analyze)

    p = subparsers.add_parser("export-data", help="Zip the DB + raw_html/raw_xml into data/exports/<timestamp>.zip")
    p.set_defaults(func=cmd_export_data)

    p = subparsers.add_parser("import-data", help="Restore the DB + raw_html/raw_xml from an export zip (wipes current data first).")
    p.add_argument("--zip", required=True, help="Path to a shab_export_*.zip created by export-data")
    p.add_argument("--yes", action="store_true", help="Required to actually perform the import.")
    p.set_defaults(func=cmd_import_data)

    p = subparsers.add_parser("webui")
    p.add_argument("--host", default=config.WEBUI_HOST)
    p.add_argument("--port", type=int, default=config.WEBUI_PORT)
    p.set_defaults(func=cmd_webui)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
