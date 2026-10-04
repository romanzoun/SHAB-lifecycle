from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config
from . import store
from . import warehouse
from .parse import parse_publication_xml


def cmd_parse(args: argparse.Namespace) -> None:
    result = parse_publication_xml(Path(args.xml), publication_id=args.id)
    print(json.dumps(
        {
            "publication_id": result.publication_id,
            "status": result.status,
            "event_types": [e.event_type for e in result.events],
            "events": [
                {
                    "event_type": e.event_type,
                    "org_uid": e.org_uid,
                    "person_key": e.person_key,
                    "plz": e.plz,
                    "canton": e.canton,
                    "role": e.role,
                    "signing": e.signing,
                    "payload": e.payload,
                    "rule_id": e.rule_id,
                    "published_at": e.published_at,
                }
                for e in result.events
            ],
        },
        ensure_ascii=False,
        indent=2,
    ))
    if args.write:
        conn = store.connect(Path(args.db))
        store.replace_parse(conn, result)
        conn.close()


def cmd_parse_dir(args: argparse.Namespace) -> None:
    conn = store.connect(Path(args.db))
    from .walk import run_walk

    result = run_walk(
        conn,
        Path(args.dir),
        once=True,
        lock_path=Path(args.db).with_suffix(".walk.lock"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    conn.close()


def cmd_walk(args: argparse.Namespace) -> None:
    from .walk import run_walk

    conn = store.connect(Path(args.db))
    result = run_walk(
        conn,
        Path(args.xml_root),
        once=args.once,
        batch_size=args.batch,
        limit=args.limit,
        poll_seconds=args.poll,
        lock_path=Path(args.lock),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    conn.close()


def cmd_status(args: argparse.Namespace) -> None:
    from .walk import coverage

    conn = store.connect(Path(args.db))
    print(json.dumps(coverage(conn), ensure_ascii=False, indent=2))
    conn.close()


def cmd_gaps(args: argparse.Namespace) -> None:
    from .walk import gap_samples

    conn = store.connect(Path(args.db))
    print(json.dumps(gap_samples(conn, limit=args.limit), ensure_ascii=False, indent=2))
    conn.close()


def cmd_warehouse_load(args: argparse.Namespace) -> None:
    aconn = store.connect(Path(args.analyzer_db))
    wconn = warehouse.connect(Path(args.warehouse_db))
    n = warehouse.replay_from_analyzer(aconn, wconn)
    print(f"fact_event_rows={n}")
    aconn.close()
    wconn.close()


def cmd_lens(args: argparse.Namespace) -> None:
    conn = warehouse.connect(Path(args.warehouse_db))
    if args.mode == "pulse":
        data = warehouse.lens_pulse(conn, args.dimension, args.key)
    else:
        data = warehouse.lens_timeline(conn, args.dimension, args.key)
    extra = {}
    if args.dimension == "person":
        extra["related_org_events"] = warehouse.related_org_events(conn, args.key)
    if args.dimension == "plz":
        extra["people"] = warehouse.plz_people(conn, args.key)
    conn.close()
    print(json.dumps({"series": data, **extra}, ensure_ascii=False, indent=2))


def cmd_serve(args: argparse.Namespace) -> None:
    from .api import app, set_warehouse_path
    import uvicorn

    set_warehouse_path(Path(args.warehouse_db))
    uvicorn.run(app, host=args.host, port=args.port)


def main() -> None:
    parser = argparse.ArgumentParser(prog="shab-parser")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="Parse one HR XML file")
    p.add_argument("xml")
    p.add_argument("--id", default=None)
    p.add_argument("--write", action="store_true")
    p.add_argument("--db", default=str(config.DEFAULT_ANALYZER_DB))
    p.set_defaults(func=cmd_parse)

    p = sub.add_parser("parse-dir", help="Parse every XML under a directory into the analyzer DB (resumable)")
    p.add_argument("dir")
    p.add_argument("--db", default=str(config.DEFAULT_ANALYZER_DB))
    p.set_defaults(func=cmd_parse_dir)

    p = sub.add_parser("walk", help="State-machine walk over harvest XML; resumes after crash")
    p.add_argument("--xml-root", default=str(config.HARVESTER_XML_ROOT))
    p.add_argument("--db", default=str(config.DEFAULT_ANALYZER_DB))
    p.add_argument("--lock", default="/var/lock/shab-analyzer-walk.lock")
    p.add_argument("--batch", type=int, default=200)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--poll", type=int, default=300, help="Seconds to wait when complete before rediscovering")
    p.add_argument("--once", action="store_true", help="Exit when the current pending set is empty")
    p.set_defaults(func=cmd_walk)

    p = sub.add_parser("status", help="Walk state machine coverage")
    p.add_argument("--db", default=str(config.DEFAULT_ANALYZER_DB))
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("gaps", help="Cluster leftover PARTIAL/ERROR texts")
    p.add_argument("--db", default=str(config.DEFAULT_ANALYZER_DB))
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_gaps)

    p = sub.add_parser("warehouse-load", help="Replay analyzer events into fact_event")
    p.add_argument("--analyzer-db", default=str(config.DEFAULT_ANALYZER_DB))
    p.add_argument("--warehouse-db", default=str(config.DEFAULT_WAREHOUSE_DB))
    p.set_defaults(func=cmd_warehouse_load)

    p = sub.add_parser("lens", help="Query a dashboard lens")
    p.add_argument("dimension", choices=["person", "plz", "canton", "org", "event_type"])
    p.add_argument("key")
    p.add_argument("--mode", default="timeline", choices=["timeline", "pulse"])
    p.add_argument("--warehouse-db", default=str(config.DEFAULT_WAREHOUSE_DB))
    p.set_defaults(func=cmd_lens)

    p = sub.add_parser("serve", help="HTTP API for lenses")
    p.add_argument("--warehouse-db", default=str(config.DEFAULT_WAREHOUSE_DB))
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8770)
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
