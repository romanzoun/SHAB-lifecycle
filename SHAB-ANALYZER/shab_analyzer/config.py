from __future__ import annotations

import os
from pathlib import Path

# Bump when person/XML rules change so the walker re-queues PARTIAL/ERROR.
PARSER_VERSION = 310

# After HR leftover is empty, unlock one non-HR family at a time (sub_rubric prefix).
# KK/SB sit next to the company timeline; then volume-heavy families; remainder last.
DEFERRED_RUBRIC_ORDER = (
    "KK",
    "SB",
    "LS",
    "AW",
    "BH",
    "EK",
    "AB",
    "NA",
    "SR",
    "ES",
    "FM",
    "UP",
    "UV",
    "BB",
    "AZ",
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ANALYZER_DB = Path(
    os.environ.get("SHAB_ANALYZER_DB", str(PACKAGE_ROOT / "data" / "shab_analyzer.sqlite"))
)
DEFAULT_WAREHOUSE_DB = Path(
    os.environ.get("SHAB_WAREHOUSE_DB", str(PACKAGE_ROOT / "data" / "shab_warehouse.sqlite"))
)
# Server layout: structured volume; harvester raw stays on the other disk.
DEFAULT_STRUCTURED_DIR = Path(os.environ.get("SHAB_STRUCTURED_DIR", "/opt/shab-structured"))
HARVESTER_DB = Path(
    os.environ.get("SHAB_HARVESTER_DB", "/opt/shab-raw/shab_harvester.sqlite")
)
HARVESTER_XML_ROOT = Path(os.environ.get("SHAB_HARVESTER_XML", "/opt/shab-raw/raw_xml"))
